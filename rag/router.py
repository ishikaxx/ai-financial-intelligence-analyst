"""Reliable question router for the Streamlit AI analyst."""

from functools import lru_cache
import re
from typing import Dict, Optional

import pandas as pd

from .entities import detect_issue_terms, detect_product, normalize_text, resolve_companies
from .sql_queries import (
    get_company_metrics,
    get_company_names,
    get_company_products,
    get_company_themes,
    rank_companies,
)
from .templates import (
    render_comparison,
    render_full_comparison,
    render_products,
    render_ranking,
    render_ranking_explanation,
    render_single_metric,
    render_themes,
)
from .validator import validate_narrative_answer


@lru_cache(maxsize=1)
def _company_names():
    return tuple(get_company_names())


def detect_metric(question: str) -> str:
    text = normalize_text(question)
    if "negative" in text or "sentiment" in text:
        return "negative_sentiment"
    if "untimely" in text or "late response" in text or "responds late" in text:
        return "untimely_response"
    if "attention" in text or "risk score" in text:
        return "attention_score"
    if "narrative" in text:
        return "narratives"
    if "rank" in text and "complaint" not in text:
        return "rank"
    return "complaints"


def _direction(question: str) -> str:
    text = normalize_text(question)
    lowest_words = ("lowest", "least", "fewest", "minimum", "lower")
    return "ASC" if any(word in text for word in lowest_words) else "DESC"


def _is_comparison(question: str, company_count: int) -> bool:
    if company_count < 2:
        return False
    text = normalize_text(question)
    words = ("compare", "versus", " vs ", "which", "more", "higher", "lower", "between")
    return any(word.strip() in text if word != " vs " else word in f" {text} " for word in words)


def _is_global_ranking(question: str, company_count: int) -> bool:
    if company_count:
        return False
    text = normalize_text(question)
    ranking_phrases = (
        "which company", "what company", "who has", "who responds",
        "top company", "top companies", "most complaints", "fewest complaints",
        "highest", "lowest", "rank companies",
    )
    return any(phrase in text for phrase in ranking_phrases)


def _is_product_question(question: str) -> bool:
    text = normalize_text(question)
    return (
        "which product" in text
        or "what product" in text
        or "products drive" in text
        or "product creates" in text
        or "product has the most" in text
    )


def _is_theme_question(question: str) -> bool:
    text = normalize_text(question)
    return "theme" in text or "topic" in text


def _is_ranking_explanation(question: str) -> bool:
    text = normalize_text(question)
    return "why" in text and ("rank" in text or "attention" in text)


def _is_direct_metric_question(question: str) -> bool:
    text = normalize_text(question)
    phrases = (
        "what percentage", "how many", "how frequently", "what is",
        "what s", "attention score", "untimely", "negative sentiment",
        "total complaints",
    )
    return any(phrase in text for phrase in phrases)


def _is_narrative_question(question: str) -> bool:
    text = normalize_text(question)
    phrases = (
        "what are consumers saying", "what do consumers say", "show examples",
        "summarize", "summarise", "what problems", "report about",
        "complaints about", "examples of",
    )
    return any(phrase in text for phrase in phrases)


def _result(answer: str, companies, sources: Optional[pd.DataFrame] = None) -> Dict[str, object]:
    return {
        "answer": answer,
        "sources": sources if sources is not None else pd.DataFrame(),
        "detected_companies": list(companies),
    }


def answer_question(question: str) -> Dict[str, object]:
    question = str(question).strip()
    if not question:
        return _result("Please enter a question about the complaint data.", [])

    companies = resolve_companies(question, _company_names())
    metric = detect_metric(question)

    if _is_comparison(question, len(companies)):
        rows = get_company_metrics(companies)
        if len(rows) != len(companies):
            return _result("Metrics were not available for every requested company.", companies)
        text = normalize_text(question)
        explicit_metric = any(
            phrase in text
            for phrase in ("complaint", "negative", "sentiment", "untimely", "late", "attention", "rank")
        )
        answer = render_comparison(rows, metric) if explicit_metric else render_full_comparison(rows)
        return _result(answer, companies)

    if _is_global_ranking(question, len(companies)):
        direction = _direction(question)
        eligible_only = metric != "complaints" or direction == "ASC" or "eligible" in normalize_text(question)
        rows = rank_companies(metric, direction, eligible_only=eligible_only)
        return _result(render_ranking(rows, metric, direction, eligible_only), companies)

    if len(companies) > 1:
        return _result(
            "I detected multiple companies. Please say which metric you want to compare, "
            "such as complaints, negative sentiment, untimely responses or attention score.",
            companies,
        )

    if len(companies) == 1:
        company = companies[0]
        metrics = get_company_metrics([company])
        if not metrics:
            return _result("No company metrics were available.", companies)

        if _is_ranking_explanation(question):
            return _result(render_ranking_explanation(metrics[0]), companies)

        if _is_product_question(question):
            return _result(render_products(company, get_company_products(company)), companies)

        if _is_theme_question(question):
            product = detect_product(question)
            themes = get_company_themes(company, product=product)
            return _result(render_themes(company, themes), companies)

        if _is_direct_metric_question(question):
            return _result(render_single_metric(metrics[0], metric), companies)

    if _is_narrative_question(question):
        # Heavy NLP dependencies are loaded only for narrative questions.
        # SQL-only questions remain available even when Ollama is not running.
        from .generation import summarize_narratives
        from .retrieval import filtered_search, source_view

        product = detect_product(question)
        issue_terms = detect_issue_terms(question)
        rows = filtered_search(
            question,
            companies=companies,
            product=product,
            issue_terms=issue_terms,
        )
        if rows.empty:
            filters = []
            if companies:
                filters.append("the requested company")
            if product:
                filters.append("product")
            if issue_terms:
                filters.append("issue")
            detail = ", ".join(filters) or "question"
            return _result(
                f"No representative narratives matched the requested {detail}. "
                "I will not substitute unrelated complaints.",
                companies,
            )

        answer = summarize_narratives(question, rows)
        allowed_ids = rows["complaint_id"] if "complaint_id" in rows.columns else []
        valid, reason = validate_narrative_answer(answer, allowed_ids)
        if not valid:
            answer = (
                "Relevant complaint examples were retrieved, but the generated summary failed "
                f"the factual validation check: {reason} Please review the sources below."
            )
        return _result(answer, companies, source_view(rows))

    return _result(
        "I can reliably answer company metrics, rankings, comparisons, product drivers, "
        "main themes and filtered narrative questions. Please make the company and metric "
        "or issue explicit.",
        companies,
    )


# Backward-compatible name for terminal scripts and simple imports.
ask_analyst = answer_question
