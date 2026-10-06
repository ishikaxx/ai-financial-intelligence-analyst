"""Metadata-filtered semantic retrieval over the existing RAG index."""

import json
from functools import lru_cache
from typing import Optional, Sequence

import numpy as np
import pandas as pd

from .config import (
    DEFAULT_EMBEDDING_MODEL,
    EMBEDDINGS_PATH,
    MANIFEST_PATH,
    METADATA_PATH,
    TOP_K,
)


def _require_files() -> None:
    missing = [
        str(path)
        for path in (EMBEDDINGS_PATH, METADATA_PATH)
        if not path.exists()
    ]
    if missing:
        raise FileNotFoundError("Missing RAG index files:\n" + "\n".join(missing))


@lru_cache(maxsize=1)
def load_index():
    _require_files()
    embeddings = np.load(EMBEDDINGS_PATH).astype(np.float32)
    metadata = pd.read_csv(METADATA_PATH)
    if len(embeddings) != len(metadata):
        raise ValueError("Embedding and metadata row counts do not match.")

    # Normalize defensively because the current manifest does not record this.
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    embeddings = embeddings / norms
    return embeddings, metadata


@lru_cache(maxsize=1)
def load_embedding_model():
    import torch
    from sentence_transformers import SentenceTransformer

    model_name = DEFAULT_EMBEDDING_MODEL
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH, "r", encoding="utf-8") as handle:
            manifest = json.load(handle)
        model_name = manifest.get("embedding_model", model_name)

    if torch.backends.mps.is_available():
        device = "mps"
    elif torch.cuda.is_available():
        device = "cuda"
    else:
        device = "cpu"
    return SentenceTransformer(model_name, device=device)


def _combined_text(metadata: pd.DataFrame, requested_columns) -> pd.Series:
    columns = [column for column in requested_columns if column in metadata.columns]
    if not columns:
        return pd.Series("", index=metadata.index, dtype="object")
    searchable = metadata[columns[0]].fillna("").astype(str)
    for column in columns[1:]:
        searchable = searchable + " " + metadata[column].fillna("").astype(str)
    return searchable.str.lower()


def issue_candidate_mask(
    metadata: pd.DataFrame, issue_terms: Sequence[str]
) -> np.ndarray:
    """Require issue evidence in metadata and in the actual narrative."""

    if not issue_terms:
        return np.ones(len(metadata), dtype=bool)

    structural_text = _combined_text(
        metadata, ("issue", "sub_issue", "topic_label")
    )
    narrative_text = _combined_text(
        metadata, ("narrative_text", "retrieval_text")
    )

    structural_mask = np.zeros(len(metadata), dtype=bool)
    narrative_mask = np.zeros(len(metadata), dtype=bool)
    for term in issue_terms:
        structural_mask |= structural_text.str.contains(
            term, case=False, regex=False
        ).to_numpy()
        narrative_mask |= narrative_text.str.contains(
            term, case=False, regex=False
        ).to_numpy()

    # If the index has no narrative/retrieval column, retain the structural
    # requirement rather than silently switching to unfiltered retrieval.
    has_narrative_text = any(
        column in metadata.columns for column in ("narrative_text", "retrieval_text")
    )
    return structural_mask & narrative_mask if has_narrative_text else structural_mask


def filtered_search(
    question: str,
    companies: Sequence[str] = (),
    product: Optional[str] = None,
    issue_terms: Sequence[str] = (),
    top_k: int = TOP_K,
) -> pd.DataFrame:
    embeddings, metadata = load_index()
    mask = np.ones(len(metadata), dtype=bool)

    if companies:
        if "company" not in metadata.columns:
            raise ValueError("RAG metadata has no company column.")
        mask &= metadata["company"].fillna("").astype(str).isin(companies).to_numpy()

    if product:
        if "product" not in metadata.columns:
            raise ValueError("RAG metadata has no product column.")
        mask &= metadata["product"].fillna("").astype(str).eq(product).to_numpy()

    if issue_terms:
        mask &= issue_candidate_mask(metadata, issue_terms)

    candidate_indices = np.flatnonzero(mask)
    if candidate_indices.size == 0:
        return metadata.iloc[[]].copy()

    query_vector = load_embedding_model().encode(
        [question], normalize_embeddings=True, convert_to_numpy=True
    )[0].astype(np.float32)
    scores = embeddings[candidate_indices] @ query_vector
    result_count = min(int(top_k), candidate_indices.size)
    order = np.argsort(-scores)[:result_count]
    selected_indices = candidate_indices[order]

    results = metadata.iloc[selected_indices].copy()
    results["retrieval_score"] = scores[order]
    return results.reset_index(drop=True)


def source_view(rows: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "complaint_id", "company", "product", "issue", "topic_label",
        "retrieval_score",
    ]
    available = [column for column in columns if column in rows.columns]
    result = rows[available].copy()
    if "retrieval_score" in result.columns:
        result["retrieval_score"] = result["retrieval_score"].round(3)
    return result
