-- AI Financial Intelligence Analyst
-- Portfolio SQL analytical queries

-- Query 1: Top three companies within each product
WITH product_rankings AS (
    SELECT
        company,
        product,
        total_complaints,
        non_template_negative_percentage,
        mean_issue_severity_score,
        untimely_response_percentage,
        monetary_relief_percentage,
        complaint_attention_score,
        ROW_NUMBER() OVER (
            PARTITION BY product
            ORDER BY
                complaint_attention_score DESC,
                total_complaints DESC
        ) AS peer_rank
    FROM company_product_attention
)
SELECT
    product,
    peer_rank,
    company,
    total_complaints,
    non_template_negative_percentage,
    mean_issue_severity_score,
    untimely_response_percentage,
    monetary_relief_percentage,
    complaint_attention_score
FROM product_rankings
WHERE peer_rank <= 3
ORDER BY
    product,
    peer_rank;

-- Query 2: Monthly product growth using LAG
WITH monthly_metrics AS (
    SELECT
        complaint_month,
        product,
        total_complaints,
        negative_sentiment_percentage,
        untimely_response_percentage,
        relief_complaints
    FROM vw_monthly_product_trends
),
growth_calculation AS (
    SELECT
        complaint_month,
        product,
        total_complaints,
        LAG(total_complaints) OVER (
            PARTITION BY product
            ORDER BY complaint_month
        ) AS previous_month_complaints,
        negative_sentiment_percentage,
        untimely_response_percentage,
        relief_complaints
    FROM monthly_metrics
),
recent_months AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY product
            ORDER BY complaint_month DESC
        ) AS recent_month_rank
    FROM growth_calculation
)
SELECT
    product,
    complaint_month,
    total_complaints,
    previous_month_complaints,
    ROUND(
        100.0
        * (
            total_complaints
            - previous_month_complaints
        )
        / NULLIF(
            previous_month_complaints,
            0
        ),
        2
    ) AS month_over_month_growth_percentage,
    negative_sentiment_percentage,
    untimely_response_percentage,
    relief_complaints
FROM recent_months
WHERE recent_month_rank <= 4
ORDER BY
    product,
    complaint_month;

-- Query 3: High-attention companies joined to
-- sufficiently large discovered topic hotspots
WITH high_attention AS (
    SELECT
        company,
        product,
        complaint_attention_score,
        attention_tier,
        total_complaints,
        non_template_negative_percentage
    FROM company_product_attention
    WHERE attention_tier IN (
        'High attention',
        'Very high attention'
    )
),
ranked_topics AS (
    SELECT
        company,
        product,
        topic_label,
        complaint_count,
        negative_complaints,
        negative_percentage,
        mean_negative_probability,
        ROW_NUMBER() OVER (
            PARTITION BY company, product
            ORDER BY
                complaint_count DESC,
                negative_complaints DESC
        ) AS topic_rank
    FROM vw_company_topic_hotspots
    WHERE topic_type = 'Discovered theme'
  AND complaint_count >= 100
)
SELECT
    h.company,
    h.product,
    h.total_complaints,
    h.complaint_attention_score,
    h.attention_tier,
    h.non_template_negative_percentage,
    t.topic_label AS largest_discovered_topic,
    t.complaint_count AS topic_complaints,
    t.negative_complaints AS topic_negative_complaints,
    t.negative_percentage AS topic_negative_percentage
FROM high_attention AS h
LEFT JOIN ranked_topics AS t
    ON h.company = t.company
   AND h.product = t.product
   AND t.topic_rank = 1
ORDER BY
    h.complaint_attention_score DESC
LIMIT 20;