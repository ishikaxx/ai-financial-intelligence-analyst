import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from rag.entities import resolve_companies
from rag.sql_queries import get_company_metrics, rank_companies
from rag.templates import neutralize_topic_label, render_comparison
from rag.validator import validate_narrative_answer
from rag.router import answer_question
from rag.retrieval import issue_candidate_mask
import pandas as pd


COMPANIES = [
    "BANK OF AMERICA, NATIONAL ASSOCIATION",
    "NAVY FEDERAL CREDIT UNION",
    "Block, Inc.",
    "Chime Financial Inc",
    "CAPITAL ONE FINANCIAL CORPORATION",
]


class EntityTests(unittest.TestCase):
    def test_resolves_two_companies(self):
        result = resolve_companies(
            "Which has more complaints: Block or Chime Financial Inc?",
            COMPANIES,
        )
        self.assertEqual(result, ["Block, Inc.", "Chime Financial Inc"])

    def test_common_aliases(self):
        result = resolve_companies(
            "Compare Bank of America and Capital One.", COMPANIES
        )
        self.assertEqual(
            result,
            [
                "BANK OF AMERICA, NATIONAL ASSOCIATION",
                "CAPITAL ONE FINANCIAL CORPORATION",
            ],
        )


class TemplateTests(unittest.TestCase):
    def test_block_chime_comparison_keeps_values_attached(self):
        rows = [
            {"company": "Block, Inc.", "total_complaints": 46720},
            {"company": "Chime Financial Inc", "total_complaints": 7793},
        ]
        answer = render_comparison(rows, "complaints")
        self.assertIn("46,720", answer)
        self.assertIn("7,793", answer)
        self.assertIn("38,927", answer)

    def test_neutral_topic_label(self):
        self.assertEqual(
            neutralize_topic_label("Bank of America Account and Withheld-Funds Problems"),
            "Account and Withheld-Funds Problems",
        )


class ValidatorTests(unittest.TestCase):
    def test_rejects_unknown_complaint_id(self):
        valid, _ = validate_narrative_answer(
            "Complaint 99999999 concerns an account.", [11380430]
        )
        self.assertFalse(valid)

    def test_rejects_uncited_narrative_summary(self):
        valid, _ = validate_narrative_answer(
            "Consumers reported problems with overdraft fees.", [11930711]
        )
        self.assertFalse(valid)


class RetrievalFilterTests(unittest.TestCase):
    def test_issue_filter_rejects_semantically_related_but_wrong_topic(self):
        metadata = pd.DataFrame(
            [
                {
                    "issue": "Problem caused by your funds being low",
                    "sub_issue": "Overdraft fee",
                    "topic_label": "Overdraft Fees and Negative Balances",
                    "narrative_text": "I was charged an overdraft fee.",
                },
                {
                    "issue": "Managing an account",
                    "sub_issue": "Cash deposit",
                    "topic_label": "ATM Cash-Deposit Errors",
                    "narrative_text": "The missing deposit later caused an overdraft.",
                },
                {
                    "issue": "Closing an account",
                    "sub_issue": "Account closure",
                    "topic_label": "Account Closures",
                    "narrative_text": "My account had a negative balance.",
                },
            ]
        )
        mask = issue_candidate_mask(
            metadata, ("overdraft", "negative balance", "funds being low")
        )
        self.assertEqual(mask.tolist(), [True, False, False])


class RouterTests(unittest.TestCase):
    def setUp(self):
        from rag import router
        router._company_names.cache_clear()

    @patch("rag.router.get_company_names", return_value=COMPANIES)
    @patch("rag.router.get_company_metrics")
    def test_block_chime_question_is_deterministic_comparison(
        self, metrics_mock, _names_mock
    ):
        metrics_mock.return_value = [
            {"company": "Block, Inc.", "total_complaints": 46720},
            {"company": "Chime Financial Inc", "total_complaints": 7793},
        ]
        result = answer_question(
            "Which has more complaints: Block or Chime Financial Inc?"
        )
        self.assertIn("46,720", result["answer"])
        self.assertIn("7,793", result["answer"])
        self.assertEqual(
            result["detected_companies"], ["Block, Inc.", "Chime Financial Inc"]
        )

    @patch("rag.router.get_company_names", return_value=COMPANIES)
    @patch("rag.router.get_company_metrics")
    def test_full_comparison_does_not_call_llm(self, metrics_mock, _names_mock):
        metrics_mock.return_value = [
            {
                "company": "BANK OF AMERICA, NATIONAL ASSOCIATION",
                "total_complaints": 14291,
                "negative_sentiment_percentage": 50.03,
                "untimely_response_percentage": 0.4,
                "weighted_company_attention_score": 66.99,
                "overall_attention_tier": "High attention",
            },
            {
                "company": "CAPITAL ONE FINANCIAL CORPORATION",
                "total_complaints": 10000,
                "negative_sentiment_percentage": 53.97,
                "untimely_response_percentage": 0.2,
                "weighted_company_attention_score": 69.70,
                "overall_attention_tier": "High attention",
            },
        ]
        result = answer_question("Compare Bank of America and Capital One.")
        self.assertIn("Company Comparison", result["answer"])
        self.assertIn("14,291", result["answer"])
        self.assertIn("10,000", result["answer"])

    def test_rejects_generated_percentage(self):
        valid, _ = validate_narrative_answer(
            "About 75% mentioned fees.", [11380430]
        )
        self.assertFalse(valid)


class SqlTests(unittest.TestCase):
    def setUp(self):
        handle = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        handle.close()
        self.db_path = Path(handle.name)
        connection = sqlite3.connect(str(self.db_path))
        connection.execute(
            """
            CREATE TABLE company_rankings (
                company TEXT,
                total_complaints INTEGER,
                narrative_complaints INTEGER,
                negative_sentiment_percentage REAL,
                untimely_complaints INTEGER,
                untimely_response_percentage REAL,
                weighted_company_attention_score REAL,
                overall_attention_tier TEXT,
                overall_company_rank INTEGER,
                highest_attention_product TEXT,
                highest_product_score REAL,
                eligible_for_comparison INTEGER
            )
            """
        )
        rows = [
            ("Block, Inc.", 46720, 30000, 50.0, 100, 0.2, 80.0, "Very high attention", 1, "Money transfer", 88.0, 1),
            ("Chime Financial Inc", 7793, 6000, 55.0, 50, 0.6, 70.0, "High attention", 2, "Checking", 75.0, 1),
        ]
        connection.executemany(
            "INSERT INTO company_rankings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            rows,
        )
        connection.commit()
        connection.close()

    def tearDown(self):
        self.db_path.unlink(missing_ok=True)

    def test_company_metrics_preserve_requested_order(self):
        rows = get_company_metrics(
            ["Chime Financial Inc", "Block, Inc."], self.db_path
        )
        self.assertEqual(rows[0]["company"], "Chime Financial Inc")
        self.assertEqual(rows[1]["company"], "Block, Inc.")

    def test_ranking_is_sql_ordered(self):
        rows = rank_companies(
            "complaints", "DESC", eligible_only=False, db_path=self.db_path
        )
        self.assertEqual(rows[0]["company"], "Block, Inc.")


if __name__ == "__main__":
    unittest.main()
