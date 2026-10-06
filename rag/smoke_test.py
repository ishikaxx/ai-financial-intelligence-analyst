"""Run deterministic analyst checks against the real project database."""

from rag.router import answer_question


QUESTIONS = [
    "Which company has the most complaints?",
    "Which eligible company has the fewest complaints?",
    "What percentage of Bank of America's narratives are negative?",
    "What is Bank of America's attention score?",
    "Which product creates the most complaints for Block?",
    "Which has more complaints: Block or Chime Financial Inc?",
    "Compare Bank of America and Capital One.",
    "Compare the negative sentiment of Bank of America and Navy Federal.",
    "What are Navy Federal's main complaint themes?",
]


def main():
    for question in QUESTIONS:
        print("\n" + "=" * 80)
        print(question)
        result = answer_question(question)
        print(result["answer"])


if __name__ == "__main__":
    main()
