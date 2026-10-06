from pathlib import Path
import sys

import pandas as pd
import streamlit as st


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AI Financial Analyst",
    page_icon="🤖",
    layout="wide",
)


# ============================================================
# CONNECT THIS PAGE TO THE MAIN PROJECT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# LOAD AND CACHE THE RAG ANALYST
# ============================================================

@st.cache_resource(show_spinner=False)
def load_analyst():
    from rag.router import answer_question

    return answer_question


# ============================================================
# PAGE HEADER
# ============================================================

st.title("🤖 AI Financial Intelligence Analyst")

st.write(
    """
    Ask questions about consumer complaints, company rankings,
    complaint themes, sentiment, response performance and
    attention scores.
    """
)

st.info(
    """
    This assistant combines structured SQL analytics with retrieved
    CFPB complaint narratives. Generated responses are analytical
    summaries, not legal or financial conclusions.
    """
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("Example Questions")

    st.markdown(
        """
        - Which company has the most complaints?
        - Compare Block and Chime by complaint volume.
        - Why does Block receive high analytical attention?
        - What are Bank of America's main complaint themes?
        - What are Navy Federal's main complaint themes?
        - Which product creates the most complaints for Block?
        - What are consumers saying about Bank of America overdraft fees?
        """
    )

    st.divider()

    if st.button(
        "Clear conversation",
        width="stretch",
    ):
        st.session_state.analyst_messages = []
        st.rerun()


# ============================================================
# CHAT HISTORY
# ============================================================

if "analyst_messages" not in st.session_state:
    st.session_state.analyst_messages = []


for message in st.session_state.analyst_messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])

        sources = message.get("sources")

        if isinstance(sources, pd.DataFrame) and not sources.empty:

            with st.expander("View retrieved complaint sources"):

                st.dataframe(
                    sources,
                    width="stretch",
                    hide_index=True,
                )


# ============================================================
# USER QUESTION
# ============================================================

question = st.chat_input(
    "Ask a question about companies, complaints or trends..."
)


if question:

    # Save the user's message
    st.session_state.analyst_messages.append(
        {
            "role": "user",
            "content": question,
        }
    )

    # Display the user's message
    with st.chat_message("user"):
        st.markdown(question)

    # Generate the assistant response
    with st.chat_message("assistant"):

        try:

            with st.spinner(
                "Searching complaint data and generating analysis..."
            ):

                analyst = load_analyst()
                result = analyst(question)

            answer = result["answer"]
            sources = result["sources"]
            detected_companies = result["detected_companies"]

            st.markdown(answer)

            if detected_companies:
                st.caption(
                    "Detected company or companies: "
                    + ", ".join(detected_companies)
                )

            if isinstance(sources, pd.DataFrame) and not sources.empty:

                with st.expander(
                    "View retrieved complaint sources"
                ):

                    st.dataframe(
                        sources,
                        width="stretch",
                        hide_index=True,
                        column_config={
                            "complaint_id": (
                                st.column_config.NumberColumn(
                                    "Complaint ID",
                                    format="%d",
                                )
                            ),
                            "company": "Company",
                            "product": "Product",
                            "topic_label": "Topic",
                            "retrieval_score": (
                                st.column_config.NumberColumn(
                                    "Retrieval Score",
                                    format="%.3f",
                                )
                            ),
                        },
                    )

            # Save the assistant response
            st.session_state.analyst_messages.append(
                {
                    "role": "assistant",
                    "content": answer,
                    "sources": sources,
                }
            )

        except Exception as error:

            error_message = str(error)

            st.error(
                "The AI analyst could not generate an answer."
            )

            if (
                "ollama" in error_message.lower()
                or "connection" in error_message.lower()
            ):
                st.warning(
                    """
                    Make sure Ollama is running. Open the Ollama
                    application or run `ollama serve` in another
                    terminal.
                    """
                )

            with st.expander("Technical error details"):
                st.code(error_message)
