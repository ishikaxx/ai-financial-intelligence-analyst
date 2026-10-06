from pathlib import Path
import json

import numpy as np
import pandas as pd
import torch
from sentence_transformers import SentenceTransformer


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_PATH = (
    PROJECT_ROOT
    / "outputs"
    / "notebook7_analysis"
    / "full_narratives_with_topics_and_sentiment.csv.gz"
)

INDEX_DIRECTORY = PROJECT_ROOT / "rag" / "rag_index"

EMBEDDINGS_PATH = INDEX_DIRECTORY / "embeddings.npy"
METADATA_PATH = INDEX_DIRECTORY / "metadata.csv.gz"
MANIFEST_PATH = INDEX_DIRECTORY / "manifest.json"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
MAX_DOCUMENTS = 50_000
RANDOM_STATE = 42


def load_retrieval_corpus():
    required_columns = [
        "complaint_id",
        "product",
        "company",
        "issue",
        "sub_issue",
        "narrative_text",
        "topic_key",
        "topic_label",
        "sentiment_label",
        "negative_probability",
        "topic_assignment_strength",
    ]

    print("Loading narrative dataset...")

    data = pd.read_csv(
        DATA_PATH,
        usecols=required_columns,
        low_memory=False,
    )

    print(f"Original narrative records: {len(data):,}")

    data = data.dropna(
        subset=["narrative_text"]
    ).copy()

    data["narrative_text"] = (
        data["narrative_text"]
        .astype(str)
        .str.strip()
    )

    data = data[
        data["narrative_text"].str.len() >= 40
    ].copy()

    data = data.drop_duplicates(
        subset=["narrative_text"]
    ).copy()

    text_columns = [
        "product",
        "company",
        "issue",
        "sub_issue",
        "topic_key",
        "topic_label",
        "sentiment_label",
    ]

    for column in text_columns:
        data[column] = data[column].fillna(
            "Not available"
        )

    # Randomise before taking representative examples.
    data = data.sample(
        frac=1,
        random_state=RANDOM_STATE,
    )

    # Keep several examples for each company-topic combination.
    corpus = (
        data.groupby(
            [
                "product",
                "company",
                "topic_key",
            ],
            group_keys=False,
            dropna=False,
        )
        .head(3)
        .copy()
    )

    if len(corpus) > MAX_DOCUMENTS:
        corpus = corpus.sample(
            n=MAX_DOCUMENTS,
            random_state=RANDOM_STATE,
        ).copy()

    corpus = corpus.reset_index(drop=True)

    corpus["retrieval_text"] = (
        "Product: "
        + corpus["product"].astype(str)
        + "\nCompany: "
        + corpus["company"].astype(str)
        + "\nIssue: "
        + corpus["issue"].astype(str)
        + "\nSub-issue: "
        + corpus["sub_issue"].astype(str)
        + "\nTopic: "
        + corpus["topic_label"].astype(str)
        + "\nSentiment: "
        + corpus["sentiment_label"].astype(str)
        + "\nComplaint narrative: "
        + corpus["narrative_text"]
        .astype(str)
        .str.slice(0, 1_500)
    )

    print(
        f"Representative RAG documents: "
        f"{len(corpus):,}"
    )

    return corpus


def create_embeddings(corpus):
    device = (
        "mps"
        if torch.backends.mps.is_available()
        else "cpu"
    )

    print(f"Embedding device: {device}")
    print(f"Embedding model: {MODEL_NAME}")

    model = SentenceTransformer(
        MODEL_NAME,
        device=device,
    )

    embeddings = model.encode(
        corpus["retrieval_text"].tolist(),
        batch_size=128,
        show_progress_bar=True,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )

    return embeddings.astype("float32")


def save_index(corpus, embeddings):
    INDEX_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    np.save(
        EMBEDDINGS_PATH,
        embeddings,
    )

    corpus.to_csv(
        METADATA_PATH,
        index=False,
        compression="gzip",
    )

    manifest = {
        "embedding_model": MODEL_NAME,
        "document_count": int(len(corpus)),
        "embedding_dimensions": int(
            embeddings.shape[1]
        ),
        "source_file": str(
            DATA_PATH.relative_to(PROJECT_ROOT)
        ),
        "maximum_documents": MAX_DOCUMENTS,
        "sampling_strategy": (
            "Up to 3 unique narratives per "
            "product-company-topic group, "
            "capped at 50,000 documents."
        ),
    }

    with open(
        MANIFEST_PATH,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            manifest,
            file,
            indent=2,
        )

    print("\nRAG index created successfully.")
    print(f"Embeddings: {EMBEDDINGS_PATH}")
    print(f"Metadata: {METADATA_PATH}")
    print(f"Manifest: {MANIFEST_PATH}")
    print(f"Embedding shape: {embeddings.shape}")


def main():
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_PATH}"
        )

    corpus = load_retrieval_corpus()
    embeddings = create_embeddings(corpus)
    save_index(corpus, embeddings)


if __name__ == "__main__":
    main()