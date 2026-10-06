-- AI Financial Intelligence Analyst
-- SQLite schema, indexes and analytical views

CREATE TABLE "company_kpis" (
"company" TEXT,
  "total_complaints" INTEGER,
  "narrative_complaints" INTEGER,
  "non_template_narratives" INTEGER,
  "negative_narrative_complaints" REAL,
  "negative_non_template_complaints" REAL,
  "mean_negative_probability" REAL,
  "untimely_complaints" INTEGER,
  "monetary_relief_complaints" INTEGER,
  "any_relief_complaints" INTEGER,
  "template_heavy_complaints" REAL,
  "products_represented" INTEGER,
  "issues_represented" INTEGER,
  "complaint_volume_percentage" REAL,
  "narrative_coverage_percentage" REAL,
  "negative_sentiment_percentage" REAL,
  "non_template_negative_percentage" REAL,
  "untimely_response_percentage" REAL,
  "monetary_relief_percentage" REAL,
  "any_relief_percentage" REAL,
  "template_heavy_percentage" REAL,
  "eligible_for_comparison" INTEGER
);

CREATE TABLE "company_product_attention" (
"company" TEXT,
  "product" TEXT,
  "total_complaints" INTEGER,
  "narrative_complaints" INTEGER,
  "non_template_narratives" INTEGER,
  "negative_narrative_complaints" REAL,
  "negative_non_template_complaints" REAL,
  "mean_negative_probability" REAL,
  "untimely_complaints" INTEGER,
  "monetary_relief_complaints" INTEGER,
  "any_relief_complaints" INTEGER,
  "template_heavy_complaints" REAL,
  "issues_represented" INTEGER,
  "narrative_coverage_percentage" REAL,
  "negative_sentiment_percentage" REAL,
  "non_template_negative_percentage" REAL,
  "untimely_response_percentage" REAL,
  "monetary_relief_percentage" REAL,
  "any_relief_percentage" REAL,
  "template_heavy_percentage" REAL,
  "eligible_for_comparison" INTEGER,
  "severity_scored_complaints" INTEGER,
  "mean_issue_severity_score" REAL,
  "severity_coverage_percentage" REAL,
  "volume_percentile" REAL,
  "negative_sentiment_percentile" REAL,
  "issue_severity_percentile" REAL,
  "untimely_response_percentile" REAL,
  "monetary_relief_percentile" REAL,
  "complaint_attention_score" REAL,
  "attention_tier" TEXT,
  "product_rank" INTEGER
);

CREATE TABLE "company_product_kpis" (
"company" TEXT,
  "product" TEXT,
  "total_complaints" INTEGER,
  "narrative_complaints" INTEGER,
  "non_template_narratives" INTEGER,
  "negative_narrative_complaints" REAL,
  "negative_non_template_complaints" REAL,
  "mean_negative_probability" REAL,
  "untimely_complaints" INTEGER,
  "monetary_relief_complaints" INTEGER,
  "any_relief_complaints" INTEGER,
  "template_heavy_complaints" REAL,
  "issues_represented" INTEGER,
  "narrative_coverage_percentage" REAL,
  "negative_sentiment_percentage" REAL,
  "non_template_negative_percentage" REAL,
  "untimely_response_percentage" REAL,
  "monetary_relief_percentage" REAL,
  "any_relief_percentage" REAL,
  "template_heavy_percentage" REAL,
  "eligible_for_comparison" INTEGER,
  "severity_scored_complaints" INTEGER,
  "mean_issue_severity_score" REAL,
  "severity_coverage_percentage" REAL
);

CREATE TABLE "company_rankings" (
"company" TEXT,
  "total_complaints" INTEGER,
  "narrative_complaints" INTEGER,
  "non_template_narratives" INTEGER,
  "negative_narrative_complaints" REAL,
  "negative_non_template_complaints" REAL,
  "mean_negative_probability" REAL,
  "untimely_complaints" INTEGER,
  "monetary_relief_complaints" INTEGER,
  "any_relief_complaints" INTEGER,
  "template_heavy_complaints" REAL,
  "products_represented" INTEGER,
  "issues_represented" INTEGER,
  "complaint_volume_percentage" REAL,
  "narrative_coverage_percentage" REAL,
  "negative_sentiment_percentage" REAL,
  "non_template_negative_percentage" REAL,
  "untimely_response_percentage" REAL,
  "monetary_relief_percentage" REAL,
  "any_relief_percentage" REAL,
  "template_heavy_percentage" REAL,
  "eligible_for_comparison" INTEGER,
  "scored_complaints" REAL,
  "weighted_score_sum" REAL,
  "scored_products" REAL,
  "highest_product_score" REAL,
  "weighted_company_attention_score" REAL,
  "highest_attention_product" TEXT,
  "scoring_coverage_percentage" REAL,
  "overall_attention_tier" TEXT,
  "overall_company_rank" INTEGER
);

CREATE TABLE "complaints" (
"date_received" TEXT,
  "product" TEXT,
  "issue" TEXT,
  "sub_issue" TEXT,
  "company" TEXT,
  "state" TEXT,
  "company_response_to_consumer" TEXT,
  "timely_response" TEXT,
  "complaint_id" TEXT,
  "has_narrative" INTEGER,
  "topic_text_id" REAL,
  "topic_assignment_corrected" INTEGER,
  "topic_id" REAL,
  "topic_key" TEXT,
  "topic_assignment_strength" REAL,
  "topic_label" TEXT,
  "topic_type" TEXT,
  "sentiment_label" TEXT,
  "negative_probability" REAL,
  "neutral_probability" REAL,
  "positive_probability" REAL,
  "sentiment_confidence" REAL,
  "complaint_month" TEXT,
  "has_narrative_intelligence" INTEGER,
  "is_untimely" INTEGER,
  "has_monetary_relief" INTEGER,
  "has_non_monetary_relief" INTEGER,
  "has_any_relief" INTEGER,
  "is_negative_sentiment" REAL,
  "is_template_heavy_topic" REAL,
  "is_topic_outlier" REAL,
  "is_topic_eligible" REAL,
  "has_non_template_narrative" INTEGER,
  "is_negative_non_template" REAL,
  "issue_severity_score" REAL,
  "has_issue_severity_score" INTEGER
);

CREATE TABLE "issue_severity_kpis" (
"product" TEXT,
  "issue" TEXT,
  "total_complaints" INTEGER,
  "narrative_complaints" INTEGER,
  "negative_narrative_complaints" REAL,
  "mean_negative_probability" REAL,
  "untimely_complaints" INTEGER,
  "monetary_relief_complaints" INTEGER,
  "negative_sentiment_percentage" REAL,
  "untimely_response_percentage" REAL,
  "monetary_relief_percentage" REAL,
  "eligible_for_severity_scoring" INTEGER,
  "issue_severity_score" REAL
);

CREATE TABLE "product_kpis" (
"product" TEXT,
  "total_complaints" INTEGER,
  "narrative_complaints" INTEGER,
  "negative_narrative_complaints" REAL,
  "mean_negative_probability" REAL,
  "untimely_complaints" INTEGER,
  "monetary_relief_complaints" INTEGER,
  "non_monetary_relief_complaints" INTEGER,
  "any_relief_complaints" INTEGER,
  "template_heavy_complaints" REAL,
  "topic_outlier_complaints" REAL,
  "unique_companies" INTEGER,
  "unique_issues" INTEGER,
  "narrative_coverage_percentage" REAL,
  "negative_sentiment_percentage" REAL,
  "untimely_response_percentage" REAL,
  "monetary_relief_percentage" REAL,
  "any_relief_percentage" REAL,
  "template_heavy_percentage" REAL,
  "topic_outlier_percentage" REAL
);

CREATE INDEX idx_company_product_attention_product_score
    ON company_product_attention
    (product, complaint_attention_score DESC);

CREATE INDEX idx_company_rankings_rank
    ON company_rankings (overall_company_rank);

CREATE INDEX idx_complaints_company
    ON complaints (company);

CREATE INDEX idx_complaints_company_month
    ON complaints (company, complaint_month);

CREATE INDEX idx_complaints_company_product
    ON complaints (company, product);

CREATE UNIQUE INDEX idx_complaints_complaint_id
    ON complaints (complaint_id);

CREATE INDEX idx_complaints_date_received
    ON complaints (date_received);

CREATE INDEX idx_complaints_issue
    ON complaints (issue);

CREATE INDEX idx_complaints_month
    ON complaints (complaint_month);

CREATE INDEX idx_complaints_product
    ON complaints (product);

CREATE INDEX idx_complaints_sentiment
    ON complaints (sentiment_label);

CREATE INDEX idx_complaints_topic
    ON complaints (topic_label);

CREATE VIEW vw_company_attention_ranking AS
    SELECT
        overall_company_rank,
        company,
        total_complaints,
        narrative_complaints,
        non_template_negative_percentage,
        untimely_response_percentage,
        monetary_relief_percentage,
        scoring_coverage_percentage,
        weighted_company_attention_score,
        highest_attention_product,
        highest_product_score,
        overall_attention_tier
    FROM company_rankings;

CREATE VIEW vw_company_topic_hotspots AS
    SELECT
        company,
        product,
        topic_label,
        topic_type,
        COUNT(*) AS complaint_count,
        SUM(
            CASE
                WHEN sentiment_label = 'negative'
                THEN 1
                ELSE 0
            END
        ) AS negative_complaints,
        ROUND(
            100.0 * SUM(
                CASE
                    WHEN sentiment_label = 'negative'
                    THEN 1
                    ELSE 0
                END
            ) / COUNT(*),
            2
        ) AS negative_percentage,
        ROUND(
            AVG(negative_probability),
            4
        ) AS mean_negative_probability
    FROM complaints
    WHERE topic_label IS NOT NULL
      AND topic_type != 'Not eligible'
    GROUP BY
        company,
        product,
        topic_label,
        topic_type;

CREATE VIEW vw_high_attention_company_products AS
    SELECT
        company,
        product,
        product_rank,
        total_complaints,
        narrative_complaints,
        non_template_negative_percentage,
        mean_issue_severity_score,
        untimely_response_percentage,
        monetary_relief_percentage,
        complaint_attention_score,
        attention_tier
    FROM company_product_attention
    WHERE attention_tier IN (
        'High attention',
        'Very high attention'
    );

CREATE VIEW vw_monthly_product_trends AS
    SELECT
        complaint_month,
        product,
        COUNT(*) AS total_complaints,
        SUM(
            CASE
                WHEN has_narrative_intelligence = 1
                THEN 1
                ELSE 0
            END
        ) AS narrative_complaints,
        SUM(
            CASE
                WHEN sentiment_label = 'negative'
                THEN 1
                ELSE 0
            END
        ) AS negative_narrative_complaints,
        ROUND(
            100.0 * SUM(
                CASE
                    WHEN sentiment_label = 'negative'
                    THEN 1
                    ELSE 0
                END
            )
            / NULLIF(
                SUM(
                    CASE
                        WHEN sentiment_label IS NOT NULL
                        THEN 1
                        ELSE 0
                    END
                ),
                0
            ),
            2
        ) AS negative_sentiment_percentage,
        SUM(
            CASE
                WHEN is_untimely = 1
                THEN 1
                ELSE 0
            END
        ) AS untimely_complaints,
        ROUND(
            100.0 * SUM(
                CASE
                    WHEN is_untimely = 1
                    THEN 1
                    ELSE 0
                END
            ) / COUNT(*),
            2
        ) AS untimely_response_percentage,
        SUM(
            CASE
                WHEN has_any_relief = 1
                THEN 1
                ELSE 0
            END
        ) AS relief_complaints
    FROM complaints
    GROUP BY
        complaint_month,
        product;

CREATE VIEW vw_product_overview AS
    SELECT
        product,
        total_complaints,
        narrative_complaints,
        narrative_coverage_percentage,
        negative_sentiment_percentage,
        mean_negative_probability,
        untimely_response_percentage,
        monetary_relief_percentage,
        any_relief_percentage,
        template_heavy_percentage,
        topic_outlier_percentage
    FROM product_kpis;