from pathlib import Path
import sqlite3

import pandas as pd
import plotly.express as px
import streamlit as st


# ---------------------------------------------------------
# Page configuration
# ---------------------------------------------------------

st.set_page_config(
    page_title="AI Financial Intelligence Analyst",
    page_icon="📊",
    layout="wide",
)


# ---------------------------------------------------------
# File paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DB_PATH = (
    PROJECT_ROOT
    / "outputs"
    / "sql_analytics"
    / "financial_intelligence.db"
)


# ---------------------------------------------------------
# Data loading
# ---------------------------------------------------------

@st.cache_data
def load_dashboard_data():
    with sqlite3.connect(DB_PATH) as connection:
        product_data = pd.read_sql_query(
            "SELECT * FROM product_kpis;",
            connection,
        )

        company_data = pd.read_sql_query(
            "SELECT * FROM company_rankings;",
            connection,
        )

        company_product_data = pd.read_sql_query(
            "SELECT * FROM company_product_attention;",
            connection,
        )

    return product_data, company_data, company_product_data


@st.cache_data
def load_topic_data():
    with sqlite3.connect(DB_PATH) as connection:
        topic_data = pd.read_sql_query(
            """
            SELECT
                product,
                topic_label,
                COUNT(*) AS complaint_count,
                SUM(
                    COALESCE(is_negative_sentiment, 0)
                ) AS negative_complaints
            FROM complaints
            WHERE topic_label IS NOT NULL
              AND is_topic_eligible = 1
              AND is_topic_outlier = 0
            GROUP BY product, topic_label;
            """,
            connection,
        )

        sentiment_data = pd.read_sql_query(
            """
            SELECT
                product,
                sentiment_label,
                COUNT(*) AS complaint_count
            FROM complaints
            WHERE sentiment_label IS NOT NULL
              AND has_narrative_intelligence = 1
            GROUP BY product, sentiment_label;
            """,
            connection,
        )

    return topic_data, sentiment_data


# ---------------------------------------------------------
# Dashboard heading
# ---------------------------------------------------------

st.title("AI Financial Intelligence Analyst")
st.caption("CFPB complaint intelligence dashboard")


if not DB_PATH.exists():
    st.error(f"Database not found: {DB_PATH}")
    st.stop()


product_kpis, company_rankings, company_product_attention = (
    load_dashboard_data()
)

topic_data, sentiment_data = load_topic_data()


# ---------------------------------------------------------
# Sidebar
# ---------------------------------------------------------

st.sidebar.header("Dashboard Filters")

selected_product = st.sidebar.selectbox(
    "Product",
    ["All products"]
    + sorted(product_kpis["product"].tolist()),
)


# ---------------------------------------------------------
# KPI calculations
# ---------------------------------------------------------

if selected_product == "All products":
    total_complaints = product_kpis[
        "total_complaints"
    ].sum()

    narrative_complaints = product_kpis[
        "narrative_complaints"
    ].sum()

    negative_complaints = product_kpis[
        "negative_narrative_complaints"
    ].sum()

    untimely_complaints = product_kpis[
        "untimely_complaints"
    ].sum()

    relief_complaints = product_kpis[
        "any_relief_complaints"
    ].sum()

else:
    selected_row = product_kpis[
        product_kpis["product"] == selected_product
    ].iloc[0]

    total_complaints = selected_row[
        "total_complaints"
    ]

    narrative_complaints = selected_row[
        "narrative_complaints"
    ]

    negative_complaints = selected_row[
        "negative_narrative_complaints"
    ]

    untimely_complaints = selected_row[
        "untimely_complaints"
    ]

    relief_complaints = selected_row[
        "any_relief_complaints"
    ]


negative_rate = (
    negative_complaints
    / narrative_complaints
    * 100
    if narrative_complaints
    else 0
)

untimely_rate = (
    untimely_complaints
    / total_complaints
    * 100
    if total_complaints
    else 0
)


# ---------------------------------------------------------
# KPI cards
# ---------------------------------------------------------

st.subheader("Complaint Overview")

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric(
    "Total Complaints",
    f"{total_complaints:,.0f}",
)

col2.metric(
    "Narratives",
    f"{narrative_complaints:,.0f}",
)

col3.metric(
    "Negative Narratives",
    f"{negative_rate:.1f}%",
)

col4.metric(
    "Untimely Responses",
    f"{untimely_rate:.2f}%",
)

col5.metric(
    "Complaints With Relief",
    f"{relief_complaints:,.0f}",
)


# ---------------------------------------------------------
# Product comparison
# ---------------------------------------------------------

st.subheader("Product Comparison")

chart_data = product_kpis.copy()

chart_data["negative_rate"] = (
    chart_data["negative_narrative_complaints"]
    / chart_data["narrative_complaints"]
    * 100
)

chart1, chart2 = st.columns(2)


with chart1:
    complaint_chart = px.bar(
        chart_data.sort_values(
            "total_complaints"
        ),
        x="total_complaints",
        y="product",
        orientation="h",
        title="Total Complaints by Product",
        labels={
            "total_complaints": "Complaints",
            "product": "",
        },
    )

    complaint_chart.update_yaxes(
        automargin=True
    )

    st.plotly_chart(
        complaint_chart,
        use_container_width=True,
    )


with chart2:
    product_sentiment_chart = px.bar(
        chart_data.sort_values(
            "negative_rate"
        ),
        x="negative_rate",
        y="product",
        orientation="h",
        title="Negative Narrative Rate by Product",
        labels={
            "negative_rate":
                "Negative narratives (%)",
            "product": "",
        },
    )

    product_sentiment_chart.update_yaxes(
        automargin=True
    )

    st.plotly_chart(
        product_sentiment_chart,
        use_container_width=True,
    )


# ---------------------------------------------------------
# Company rankings
# ---------------------------------------------------------

st.subheader("Company Attention Rankings")


if selected_product == "All products":
    ranking_data = (
        company_rankings[
            company_rankings[
                "eligible_for_comparison"
            ] == 1
        ]
        .sort_values(
            "overall_company_rank"
        )
        .head(15)
        .copy()
    )

    rank_column = "overall_company_rank"

    score_column = (
        "weighted_company_attention_score"
    )

    ranking_data["attention_tier"] = (
        ranking_data[
            "overall_attention_tier"
        ]
    )

else:
    ranking_data = (
        company_product_attention[
            (
                company_product_attention[
                    "product"
                ] == selected_product
            )
            & (
                company_product_attention[
                    "eligible_for_comparison"
                ] == 1
            )
        ]
        .sort_values("product_rank")
        .head(15)
        .copy()
    )

    rank_column = "product_rank"
    score_column = "complaint_attention_score"


if ranking_data.empty:
    st.warning(
        "No eligible company rankings are available "
        "for this selection."
    )

else:
    ranking_chart = px.bar(
        ranking_data.sort_values(
            score_column
        ),
        x=score_column,
        y="company",
        orientation="h",
        color="attention_tier",
        title=(
            "Top Companies Requiring "
            f"Analytical Attention — {selected_product}"
        ),
        labels={
            score_column: "Attention score",
            "company": "",
            "attention_tier": "Attention tier",
        },
        hover_data={
            "total_complaints": ":,",
            "negative_sentiment_percentage":
                ":.1f",
            "untimely_response_percentage":
                ":.2f",
            "any_relief_percentage":
                ":.1f",
        },
    )

    ranking_chart.update_layout(
        height=650
    )

    ranking_chart.update_yaxes(
        automargin=True
    )

    st.plotly_chart(
        ranking_chart,
        use_container_width=True,
    )


    ranking_table = ranking_data[
        [
            rank_column,
            "company",
            "total_complaints",
            "negative_sentiment_percentage",
            "untimely_response_percentage",
            "any_relief_percentage",
            score_column,
            "attention_tier",
        ]
    ].copy()


    ranking_table.columns = [
        "Rank",
        "Company",
        "Complaints",
        "Negative sentiment (%)",
        "Untimely response (%)",
        "Relief provided (%)",
        "Attention score",
        "Attention tier",
    ]


    ranking_table[
        "Attention score"
    ] = ranking_table[
        "Attention score"
    ].round(2)


    st.dataframe(
        ranking_table,
        width="stretch",
        hide_index=True,
    )


st.info(
    "Attention scores are exploratory prioritisation "
    "indicators. They do not establish company misconduct, "
    "regulatory violations or complaint incidence rates."
)


# ---------------------------------------------------------
# Topic and sentiment intelligence
# ---------------------------------------------------------

st.subheader(
    "Topic and Sentiment Intelligence"
)


if selected_product == "All products":
    topic_view = topic_data.copy()

    sentiment_view = (
        sentiment_data.groupby(
            "sentiment_label",
            as_index=False,
        )["complaint_count"].sum()
    )

    topic_view["display_topic"] = (
        topic_view["product"]
        + " — "
        + topic_view["topic_label"]
    )

else:
    topic_view = topic_data[
        topic_data["product"]
        == selected_product
    ].copy()

    sentiment_view = sentiment_data[
        sentiment_data["product"]
        == selected_product
    ].copy()

    topic_view["display_topic"] = (
        topic_view["topic_label"]
    )


topic_view["negative_rate"] = (
    topic_view["negative_complaints"]
    / topic_view["complaint_count"]
    * 100
)


top_topics = (
    topic_view
    .sort_values(
        "complaint_count",
        ascending=False,
    )
    .head(12)
    .sort_values("complaint_count")
)


# Full-width topic chart
topic_chart = px.bar(
    top_topics,
    x="complaint_count",
    y="display_topic",
    orientation="h",
    color="negative_rate",
    color_continuous_scale="Reds",
    title="Most Frequent Complaint Topics",
    labels={
        "complaint_count":
            "Narrative complaints",
        "display_topic": "",
        "negative_rate": "Negative %",
    },
)


topic_chart.update_layout(
    height=650,
    margin=dict(
        l=460,
        r=40,
        t=70,
        b=60,
    ),
)


topic_chart.update_yaxes(
    automargin=True
)


st.plotly_chart(
    topic_chart,
    use_container_width=True,
)


# Sentiment chart
sentiment_chart = px.pie(
    sentiment_view,
    names="sentiment_label",
    values="complaint_count",
    hole=0.5,
    title="Narrative Sentiment Distribution",
)


sentiment_chart.update_layout(
    height=500
)


st.plotly_chart(
    sentiment_chart,
    use_container_width=True,
)


# ---------------------------------------------------------
# Methodology disclaimer
# ---------------------------------------------------------

st.caption(
    "Sentiment indicators are model-generated analytical "
    "signals and should not be interpreted as proof of "
    "company misconduct."
)