"""Company, product and issue detection."""

import re
from typing import Iterable, List, Optional, Sequence, Tuple

from .config import (
    COMPANY_ALIASES,
    COMPANY_STOPWORDS,
    GENERIC_COMPANY_WORDS,
    ISSUE_TERM_GROUPS,
    PRODUCT_PHRASES,
)


def normalize_text(value: object) -> str:
    text = str(value).lower().replace("&", " and ")
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def tokenize(value: object) -> List[str]:
    return re.findall(r"[a-z0-9]+", normalize_text(value))


def _contains_phrase(text: str, phrase: str) -> bool:
    return bool(re.search(r"(?<![a-z0-9])" + re.escape(phrase) + r"(?![a-z0-9])", text))


def _official_name(target: str, company_names: Sequence[str]) -> Optional[str]:
    target_normalized = normalize_text(target)
    for company in company_names:
        if normalize_text(company) == target_normalized:
            return company
    return None


def resolve_companies(question: str, company_names: Sequence[str]) -> List[str]:
    """Resolve every explicitly mentioned company, preserving mention order."""

    question_normalized = normalize_text(question)
    matches = []

    for alias, target in COMPANY_ALIASES.items():
        alias_normalized = normalize_text(alias)
        if _contains_phrase(question_normalized, alias_normalized):
            official = _official_name(target, company_names)
            if official:
                position = question_normalized.find(alias_normalized)
                matches.append((position, -len(alias_normalized), official))

    # Dynamic matching lets the router support companies not present in the
    # hand-written alias list, while rejecting generic one-word matches.
    question_tokens = set(tokenize(question))
    for company in company_names:
        core_tokens = [
            token for token in tokenize(company)
            if token not in COMPANY_STOPWORDS
        ]
        if not core_tokens:
            continue

        core_phrase = " ".join(core_tokens)
        position = question_normalized.find(core_phrase)
        if position >= 0:
            matches.append((position, -len(core_phrase), company))
            continue

        distinctive = [
            token for token in core_tokens
            if token not in GENERIC_COMPANY_WORDS and len(token) >= 4
        ]
        overlap = set(distinctive).intersection(question_tokens)
        if len(core_tokens) == 1 and overlap:
            token = next(iter(overlap))
            matches.append((question_normalized.find(token), -len(token), company))
        elif len(overlap) >= 2 and set(core_tokens).issubset(question_tokens):
            first = min(question_normalized.find(token) for token in overlap)
            matches.append((first, -sum(len(token) for token in overlap), company))

    matches.sort()
    resolved = []
    for _, _, company in matches:
        if company not in resolved:
            resolved.append(company)
    return resolved


def detect_product(question: str) -> Optional[str]:
    normalized = normalize_text(question)
    candidates = []
    for phrase, product in PRODUCT_PHRASES.items():
        phrase_normalized = normalize_text(phrase)
        if _contains_phrase(normalized, phrase_normalized):
            candidates.append((len(phrase_normalized), product))
    if not candidates:
        return None
    return max(candidates)[1]


def detect_issue_terms(question: str) -> Tuple[str, ...]:
    normalized = normalize_text(question)
    matched_groups = []
    for trigger, group_terms in ISSUE_TERM_GROUPS.items():
        trigger_phrase = trigger.replace("_", " ")
        if trigger_phrase in normalized or any(term in normalized for term in group_terms):
            matched_groups.append((trigger, group_terms))

    # "Fees" is too broad when a more specific request such as overdraft fees
    # was also detected. Prefer the specific issue group in that case.
    if len(matched_groups) > 1:
        matched_groups = [item for item in matched_groups if item[0] != "fees"]

    terms = []
    for _, group_terms in matched_groups:
        terms.extend(group_terms)
    return tuple(dict.fromkeys(terms))


def strip_company_tokens(question: str, companies: Iterable[str]) -> str:
    normalized = normalize_text(question)
    for company in companies:
        for token in tokenize(company):
            if token not in COMPANY_STOPWORDS:
                normalized = re.sub(r"\b" + re.escape(token) + r"\b", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()
