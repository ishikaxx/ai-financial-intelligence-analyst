"""Lightweight safeguards for generated narrative summaries."""

import re
from typing import Iterable, Tuple


UNSUPPORTED_PATTERNS = (
    r"\bshould (?:change|review|revise|stop|improve)\b",
    r"\bproves? (?:fraud|misconduct|wrongdoing|illegality)\b",
    r"\bthe company (?:committed|engaged in)\b",
    r"\bstatistically significant\b",
)


def validate_narrative_answer(
    answer: str,
    allowed_complaint_ids: Iterable[object],
) -> Tuple[bool, str]:
    allowed = {str(value) for value in allowed_complaint_ids}
    cited_ids = set(re.findall(r"\b\d{7,10}\b", answer))
    if allowed and not cited_ids:
        return False, "The generated answer did not cite its retrieved complaint evidence."
    unknown = cited_ids - allowed
    if unknown:
        return False, "The generated answer cited complaint IDs outside the retrieved evidence."

    for pattern in UNSUPPORTED_PATTERNS:
        if re.search(pattern, answer, flags=re.IGNORECASE):
            return False, "The generated answer added an unsupported conclusion."

    # Narrative generation is not allowed to invent population percentages.
    if re.search(r"\b\d+(?:\.\d+)?%", answer):
        return False, "The generated narrative introduced an unvalidated percentage."
    return True, ""
