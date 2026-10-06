"""Constrained local-LLM summarisation for retrieved narratives."""

from typing import Sequence

import ollama
import pandas as pd

from .config import OLLAMA_MODEL


def _format_evidence(rows: pd.DataFrame) -> str:
    documents = []
    for _, row in rows.iterrows():
        narrative = str(row.get("narrative_text", ""))
        if len(narrative) > 1200:
            narrative = narrative[:1200] + "..."
        documents.append(
            f"COMPLAINT ID: {row.get('complaint_id', 'Unknown')}\n"
            f"COMPANY: {row.get('company', 'Unknown')}\n"
            f"PRODUCT: {row.get('product', 'Unknown')}\n"
            f"ISSUE: {row.get('issue', 'Unknown')}\n"
            f"TOPIC: {row.get('topic_label', 'Unknown')}\n"
            f"NARRATIVE: {narrative}"
        )
    return "\n\n---\n\n".join(documents)


def summarize_narratives(question: str, rows: pd.DataFrame) -> str:
    evidence = _format_evidence(rows)
    system_prompt = """
You summarize retrieved CFPB consumer complaint narratives.

Strict rules:
1. Use only the supplied narratives.
2. Discuss only the exact issue requested in the question. Ignore unrelated
   issues mentioned in the same narratives, even if they concern fees or the
   same account.
3. Support every observation with its complaint ID. Use phrasing such as
   "Complaint 12345678 alleges..." or "Complaints 12345678 and 87654321 report...".
4. Call something a recurring pattern only when at least two retrieved
   narratives explicitly support it. Otherwise describe it as one example.
5. State that the examples are illustrative, not population-level evidence.
6. Do not introduce counts, percentages, rankings or attention scores.
7. Do not recommend that a company change a policy.
8. Do not claim fraud, misconduct, illegality or statistical significance.
9. Treat every narrative as an unverified consumer allegation.
10. Cite only complaint IDs that appear in the supplied evidence.
11. If the examples do not directly answer the exact issue, say so plainly.
12. Be concise: a direct answer, up to three evidence bullets, then one limitation.
"""
    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"QUESTION:\n{question}\n\nRETRIEVED EVIDENCE:\n{evidence}",
            },
        ],
        options={"temperature": 0.0},
    )
    if hasattr(response, "message"):
        return response.message.content
    return response["message"]["content"]
