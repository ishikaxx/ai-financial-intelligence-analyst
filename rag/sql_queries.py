"""Deterministic SQL access for analyst metrics."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from .config import DB_PATH, EXCLUDED_COMPARISON_COMPANIES


ALLOWED_METRICS = {
    "complaints": "total_complaints",
    "narratives": "narrative_complaints",
    "negative_sentiment": "negative_sentiment_percentage",
    "untimely_response": "untimely_response_percentage",
    "attention_score": "weighted_company_attention_score",
    "rank": "overall_company_rank",
}


@contextmanager
def connect(db_path: Path = DB_PATH):
    if not Path(db_path).exists():
        raise FileNotFoundError(f"Financial-intelligence database not found: {db_path}")
    connection = sqlite3.connect(str(db_path))
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.close()


def _rows(cursor: sqlite3.Cursor) -> List[Dict[str, object]]:
    return [dict(row) for row in cursor.fetchall()]


def get_company_names(db_path: Path = DB_PATH) -> List[str]:
    with connect(db_path) as connection:
        cursor = connection.execute(
            """
            SELECT DISTINCT company
            FROM company_rankings
            WHERE company IS NOT NULL
            ORDER BY company
            """
        )
        return [str(row[0]) for row in cursor.fetchall()]


def get_company_metrics(
    companies: Sequence[str], db_path: Path = DB_PATH
) -> List[Dict[str, object]]:
    if not companies:
        return []
    placeholders = ",".join("?" for _ in companies)
    query = f"""
        SELECT
            company,
            total_complaints,
            narrative_complaints,
            negative_sentiment_percentage,
            untimely_complaints,
            untimely_response_percentage,
            weighted_company_attention_score,
            overall_attention_tier,
            overall_company_rank,
            highest_attention_product,
            highest_product_score,
            eligible_for_comparison
        FROM company_rankings
        WHERE company IN ({placeholders})
    """
    with connect(db_path) as connection:
        result = _rows(connection.execute(query, list(companies)))
    order = {company: position for position, company in enumerate(companies)}
    result.sort(key=lambda row: order.get(str(row["company"]), len(order)))
    return result


def get_company_products(
    company: str, db_path: Path = DB_PATH
) -> List[Dict[str, object]]:
    query = """
        SELECT
            company,
            product,
            total_complaints,
            narrative_complaints,
            negative_sentiment_percentage,
            untimely_response_percentage,
            complaint_attention_score,
            attention_tier,
            product_rank
        FROM company_product_attention
        WHERE company = ?
        ORDER BY total_complaints DESC, product ASC
    """
    with connect(db_path) as connection:
        return _rows(connection.execute(query, [company]))


def get_company_themes(
    company: str,
    product: Optional[str] = None,
    search_terms: Sequence[str] = (),
    limit: int = 8,
    db_path: Path = DB_PATH,
) -> List[Dict[str, object]]:
    conditions = [
        "company = ?",
        "topic_label IS NOT NULL",
        "topic_type = 'Discovered theme'",
    ]
    params: List[object] = [company]

    if product:
        conditions.append("product = ?")
        params.append(product)

    if search_terms:
        searchable_clauses = []
        for term in search_terms:
            searchable_clauses.append(
                "(LOWER(topic_label) LIKE ? OR LOWER(issue) LIKE ? OR LOWER(sub_issue) LIKE ?)"
            )
            like_value = f"%{term.lower()}%"
            params.extend([like_value, like_value, like_value])
        conditions.append("(" + " OR ".join(searchable_clauses) + ")")

    params.append(int(limit))
    query = f"""
        SELECT
            product,
            topic_label,
            COUNT(*) AS complaint_count,
            ROUND(100.0 * AVG(is_negative_sentiment), 2)
                AS negative_sentiment_percentage
        FROM complaints
        WHERE {' AND '.join(conditions)}
        GROUP BY product, topic_label
        ORDER BY complaint_count DESC, topic_label ASC
        LIMIT ?
    """
    with connect(db_path) as connection:
        return _rows(connection.execute(query, params))


def rank_companies(
    metric_key: str,
    direction: str = "DESC",
    eligible_only: bool = True,
    limit: int = 10,
    db_path: Path = DB_PATH,
) -> List[Dict[str, object]]:
    if metric_key not in ALLOWED_METRICS:
        raise ValueError(f"Unsupported ranking metric: {metric_key}")
    direction = direction.upper()
    if direction not in {"ASC", "DESC"}:
        raise ValueError("Ranking direction must be ASC or DESC")

    metric = ALLOWED_METRICS[metric_key]
    conditions = []
    params: List[object] = []
    if eligible_only:
        conditions.append("eligible_for_comparison = 1")
    if EXCLUDED_COMPARISON_COMPANIES:
        placeholders = ",".join("?" for _ in EXCLUDED_COMPARISON_COMPANIES)
        conditions.append(f"company NOT IN ({placeholders})")
        params.extend(sorted(EXCLUDED_COMPARISON_COMPANIES))
    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    query = f"""
        SELECT
            company,
            total_complaints,
            narrative_complaints,
            negative_sentiment_percentage,
            untimely_complaints,
            untimely_response_percentage,
            weighted_company_attention_score,
            overall_attention_tier,
            overall_company_rank,
            highest_attention_product,
            eligible_for_comparison
        FROM company_rankings
        {where}
        ORDER BY {metric} {direction}, company ASC
        LIMIT ?
    """
    params.append(int(limit))
    with connect(db_path) as connection:
        return _rows(connection.execute(query, params))
