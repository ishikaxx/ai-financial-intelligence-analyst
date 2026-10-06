"""Deterministic response rendering for structured analytics."""

from typing import Dict, List, Sequence

from .config import TOPIC_PREFIX_REPLACEMENTS


METRIC_LABELS = {
    "complaints": "total complaints",
    "narratives": "complaint narratives",
    "negative_sentiment": "negative narrative sentiment",
    "untimely_response": "untimely response rate",
    "attention_score": "attention score",
    "rank": "overall attention rank",
}

METRIC_COLUMNS = {
    "complaints": "total_complaints",
    "narratives": "narrative_complaints",
    "negative_sentiment": "negative_sentiment_percentage",
    "untimely_response": "untimely_response_percentage",
    "attention_score": "weighted_company_attention_score",
    "rank": "overall_company_rank",
}


def display_company(company: object) -> str:
    name = str(company)
    replacements = {
        "BANK OF AMERICA, NATIONAL ASSOCIATION": "Bank of America",
        "NAVY FEDERAL CREDIT UNION": "Navy Federal Credit Union",
        "CAPITAL ONE FINANCIAL CORPORATION": "Capital One",
    }
    return replacements.get(name, name)


def neutralize_topic_label(label: object) -> str:
    result = str(label)
    for prefix, replacement in TOPIC_PREFIX_REPLACEMENTS:
        if result.startswith(prefix):
            result = replacement + result[len(prefix):]
            break
    return result.strip() or str(label)


def _number(value: object, decimals: int = 2) -> str:
    if value is None:
        return "not available"
    return f"{float(value):,.{decimals}f}"


def format_metric(metric_key: str, value: object) -> str:
    if value is None:
        return "not available"
    if metric_key in {"complaints", "narratives", "rank"}:
        return f"{int(value):,}"
    if metric_key in {"negative_sentiment", "untimely_response"}:
        return f"{float(value):.2f}%"
    if metric_key == "attention_score":
        return f"{float(value):.2f}/100"
    return str(value)


def render_single_metric(row: Dict[str, object], metric_key: str) -> str:
    company = display_company(row["company"])
    column = METRIC_COLUMNS[metric_key]
    value = format_metric(metric_key, row.get(column))
    label = METRIC_LABELS[metric_key]

    if metric_key == "untimely_response":
        count = int(row.get("untimely_complaints") or 0)
        return (
            f"### {company}: Untimely Responses\n\n"
            f"**{value}** of recorded complaints received an untimely response "
            f"(**{count:,} complaints**).\n\n"
            "This measures the formal CFPB response-timeliness field, not customer satisfaction."
        )
    if metric_key == "attention_score":
        tier = row.get("overall_attention_tier") or "not available"
        return (
            f"### {company}: Attention Score\n\n"
            f"**{value} — {tier}**\n\n"
            "A higher attention score indicates greater analytical priority; "
            "it is not a positive performance rating."
        )
    return f"### {company}\n\nIts {label} value is **{value}**."


def render_comparison(rows: Sequence[Dict[str, object]], metric_key: str) -> str:
    if len(rows) < 2:
        return "I need two recognized companies to make this comparison."
    column = METRIC_COLUMNS[metric_key]
    available = [row for row in rows if row.get(column) is not None]
    if len(available) < 2:
        return "The requested metric is not available for both companies."

    reverse = metric_key != "rank"
    ordered = sorted(available, key=lambda row: float(row[column]), reverse=reverse)
    leader = ordered[0]
    runner_up = ordered[1]
    leader_name = display_company(leader["company"])
    runner_name = display_company(runner_up["company"])

    if float(leader[column]) == float(runner_up[column]):
        direct = (
            f"**{leader_name} and {runner_name} are tied at "
            f"{format_metric(metric_key, leader[column])}.**"
        )
    else:
        direct = (
            f"**{leader_name} has the higher {METRIC_LABELS[metric_key]}: "
            f"{format_metric(metric_key, leader[column])}, compared with "
            f"{format_metric(metric_key, runner_up[column])} for {runner_name}.**"
        )
        if metric_key in {"complaints", "narratives"}:
            difference = int(leader[column]) - int(runner_up[column])
            direct += f" The difference is **{difference:,}**."
        elif metric_key in {"negative_sentiment", "untimely_response"}:
            difference = float(leader[column]) - float(runner_up[column])
            direct += f" The difference is **{difference:.2f} percentage points**."

    table = [
        "| Company | Value |",
        "|---|---:|",
    ]
    for row in rows:
        table.append(
            f"| {display_company(row['company'])} | {format_metric(metric_key, row[column])} |"
        )
    return f"### Company Comparison\n\n{direct}\n\n" + "\n".join(table)


def render_full_comparison(rows: Sequence[Dict[str, object]]) -> str:
    if len(rows) < 2:
        return "I need two recognized companies to make this comparison."
    lines = [
        "### Company Comparison",
        "",
        "| Company | Complaints | Negative sentiment | Untimely responses | Attention score | Tier |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {display_company(row['company'])} | "
            f"{format_metric('complaints', row.get('total_complaints'))} | "
            f"{format_metric('negative_sentiment', row.get('negative_sentiment_percentage'))} | "
            f"{format_metric('untimely_response', row.get('untimely_response_percentage'))} | "
            f"{format_metric('attention_score', row.get('weighted_company_attention_score'))} | "
            f"{row.get('overall_attention_tier', 'not available')} |"
        )
    lines.extend([
        "",
        "Complaint volume and attention scores indicate analytical priority, not company quality or proven misconduct.",
    ])
    return "\n".join(lines)


def render_ranking(
    rows: Sequence[Dict[str, object]],
    metric_key: str,
    direction: str,
    eligible_only: bool,
) -> str:
    if not rows:
        return "No companies matched the ranking criteria."
    column = METRIC_COLUMNS[metric_key]
    top_value = rows[0].get(column)
    winners = [row for row in rows if row.get(column) == top_value]
    position = "lowest" if direction.upper() == "ASC" else "highest"
    scope = " among comparison-eligible companies" if eligible_only else ""
    names = ", ".join(display_company(row["company"]) for row in winners)
    if len(winners) > 1:
        statement = (
            f"{names} are tied for the {position} {METRIC_LABELS[metric_key]}{scope}"
        )
    else:
        statement = (
            f"{names} has the {position} {METRIC_LABELS[metric_key]}{scope}"
        )
    answer = (
        f"### {position.title()} {METRIC_LABELS[metric_key].title()}\n\n"
        f"**{statement}: {format_metric(metric_key, top_value)}.**"
    )
    if eligible_only:
        answer += "\n\nComparison eligibility is taken directly from the project database."
    return answer


def render_products(company: str, rows: Sequence[Dict[str, object]]) -> str:
    if not rows:
        return f"No product metrics were available for {display_company(company)}."
    top = max(rows, key=lambda row: int(row.get("total_complaints") or 0))
    lines = [
        f"### Main Complaint Product for {display_company(company)}",
        "",
        f"**{top['product']}** has the most complaints: "
        f"**{int(top['total_complaints']):,}**.",
        "",
        "| Product | Complaints | Negative sentiment | Attention score |",
        "|---|---:|---:|---:|",
    ]
    for row in sorted(rows, key=lambda item: int(item.get("total_complaints") or 0), reverse=True):
        lines.append(
            f"| {row['product']} | {int(row['total_complaints']):,} | "
            f"{_number(row.get('negative_sentiment_percentage'))}% | "
            f"{_number(row.get('complaint_attention_score'))}/100 |"
        )
    return "\n".join(lines)


def render_themes(company: str, rows: Sequence[Dict[str, object]]) -> str:
    if not rows:
        return f"No matching discovered themes were available for {display_company(company)}."
    lines = [f"### Main Complaint Themes for {display_company(company)}", ""]
    for position, row in enumerate(rows, start=1):
        label = neutralize_topic_label(row["topic_label"])
        lines.append(
            f"{position}. **{label}** ({row['product']}): "
            f"{int(row['complaint_count']):,} complaints; "
            f"{_number(row.get('negative_sentiment_percentage'))}% negative sentiment"
        )
    lines.extend([
        "",
        "Topic names are displayed in company-neutral form because clusters may contain complaints from multiple companies.",
    ])
    return "\n".join(lines)


def render_ranking_explanation(row: Dict[str, object]) -> str:
    company = display_company(row["company"])
    return (
        f"### Why {company} Receives High Analytical Attention\n\n"
        f"{company} has **{int(row['total_complaints']):,} complaints**, "
        f"**{format_metric('negative_sentiment', row.get('negative_sentiment_percentage'))}** "
        f"negative narrative sentiment and an attention score of "
        f"**{format_metric('attention_score', row.get('weighted_company_attention_score'))}**. "
        f"Its highest-attention product is **{row.get('highest_attention_product', 'not available')}**.\n\n"
        "The score identifies analytical priority based on the project’s stored metrics. "
        "It does not indicate strong performance or prove misconduct."
    )
