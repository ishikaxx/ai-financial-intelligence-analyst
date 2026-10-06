"""Shared configuration for the financial-intelligence analyst."""

from pathlib import Path
import os


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "outputs" / "sql_analytics" / "financial_intelligence.db"
INDEX_DIR = PROJECT_ROOT / "rag" / "rag_index"
EMBEDDINGS_PATH = INDEX_DIR / "embeddings.npy"
METADATA_PATH = INDEX_DIR / "metadata.csv.gz"
MANIFEST_PATH = INDEX_DIR / "manifest.json"

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
TOP_K = 6

# A descriptive portfolio label present in the CFPB data, not a conventional
# company identity. Excluding it prevents a misleading "top company" result.
EXCLUDED_COMPARISON_COMPANIES = {
    "Servicer under contract with Federal Student Aid",
}

# These aliases are resolved to an official name loaded from company_rankings.
# Keep aliases specific: generic words such as "bank" or "financial" are unsafe.
COMPANY_ALIASES = {
    "bank of america": "BANK OF AMERICA, NATIONAL ASSOCIATION",
    "bofa": "BANK OF AMERICA, NATIONAL ASSOCIATION",
    "navy federal": "NAVY FEDERAL CREDIT UNION",
    "navy federal credit union": "NAVY FEDERAL CREDIT UNION",
    "block": "Block, Inc.",
    "block inc": "Block, Inc.",
    "cash app": "Block, Inc.",
    "capital one": "CAPITAL ONE FINANCIAL CORPORATION",
    "chime": "Chime Financial Inc",
    "chime financial": "Chime Financial Inc",
    "equifax": "EQUIFAX, INC.",
}

COMPANY_STOPWORDS = {
    "the", "of", "and", "inc", "incorporated", "llc", "ltd", "limited",
    "corp", "corporation", "company", "companies", "co", "holdings",
    "holding", "group", "national", "association", "na", "plc",
}

GENERIC_COMPANY_WORDS = {
    "bank", "financial", "finance", "credit", "union", "services",
    "service", "federal", "capital", "lending", "mortgage",
}

# Query phrases used only to restrict narrative candidates. If a requested
# issue has no matching indexed narratives, retrieval returns no examples.
ISSUE_TERM_GROUPS = {
    "overdraft": ("overdraft", "negative balance", "funds being low"),
    "unauthorized": ("unauthorized", "not authorized", "account takeover"),
    "account_management": ("managing an account", "account management"),
    "account_access": ("account access", "locked account", "frozen account"),
    "account_closure": ("account closure", "closed account", "account closed"),
    "fees": ("fee", "fees", "charged"),
    "deposit": ("deposit", "cash deposit", "direct deposit"),
    "fraud": ("fraud", "scam", "identity theft"),
    "transfer": ("transfer", "wire", "zelle", "payment transfer"),
    "billing": ("billing", "bill", "statement"),
    "credit_reporting": ("credit report", "credit reporting", "credit bureau"),
    "mortgage": ("mortgage", "escrow", "foreclosure", "servicing"),
    "debt_collection": ("debt collection", "collector", "collection debt"),
}

PRODUCT_PHRASES = {
    "checking or savings": "Checking or savings account",
    "checking account": "Checking or savings account",
    "savings account": "Checking or savings account",
    "credit card": "Credit card",
    "debt collection": "Debt collection",
    "mortgage": "Mortgage",
    "money transfer": "Money transfer, virtual currency, or money service",
    "virtual currency": "Money transfer, virtual currency, or money service",
    "cash app": "Money transfer, virtual currency, or money service",
}

# Display-only cleanup for topic labels created from company-heavy clusters.
# The database is not modified.
TOPIC_PREFIX_REPLACEMENTS = (
    ("Bank of America ", ""),
    ("Navy Federal ", ""),
    ("Capital One ", ""),
    ("Chime ", ""),
    ("Chase ", ""),
    ("Apple Card ", "Card "),
    ("Cash App ", "Digital-Wallet "),
)
