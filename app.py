"""
BVRIT RAG-Powered College FAQ Chatbot with Automated Evaluation
================================================================
Streamlit application providing:
1. Interactive chat interface with RAG-powered responses
2. Source citations for every answer
3. Image display from PDF documents
4. Graceful refusal for out-of-knowledge-base queries
5. Automated evaluation dashboard using RAGAS metrics
6. LLM-as-a-Judge evaluation across 8 dimensions
"""

import streamlit as st
import os
import json
import time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv

from chatbot import generate_response, retrieve_relevant_chunks
from evaluation import (
    TEST_QUESTIONS,
    evaluate_with_ragas,
    evaluate_llm_as_judge,
    JUDGE_PROMPTS,
)

# Page configuration
st.set_page_config(
    page_title="BVRIT RAG Chatbot",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Load environment variables
load_dotenv()

# Check API key
API_KEY = os.getenv("OPENROUTER_API_KEY", "")
if not API_KEY or API_KEY == "your-openrouter-api-key-here":
    st.warning(
        "⚠️ **OpenRouter API Key not configured.**\n\n"
        "Please set your `OPENROUTER_API_KEY` in the `.env` file before running the chatbot.\n\n"
        "You can get a free API key from [OpenRouter](https://openrouter.ai/keys)."
    )

# ============================================================
# Sidebar Navigation
# ============================================================
st.sidebar.title("🎓 BVRIT Chatbot")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    ["💬 Chat Interface", "📊 Evaluation Dashboard"],
    index=0,
)

st.sidebar.markdown("---")
st.sidebar.markdown("### About")
st.sidebar.info(
    "This chatbot uses **Retrieval-Augmented Generation (RAG)** "
    "to answer questions about BVRIT HYDERABAD College of Engineering for Women. "
    "Responses are grounded in official college documents, include source citations, "
    "and display relevant campus images from the PDF."
)

# ============================================================
# Helper: Display images in a grid
# ============================================================
def display_images_grid(image_paths, cols=2):
    """Display images in a responsive grid layout."""
    if not image_paths:
        return

    # Create rows of images
    for i in range(0, len(image_paths), cols):
        row_images = image_paths[i:i + cols]
        cols_in_row = st.columns(len(row_images))
        for col_idx, img_path in enumerate(row_images):
            if os.path.exists(img_path):
                with cols_in_row[col_idx]:
                    # Extract page number from filename for caption
                    img_name = os.path.basename(img_path)
                    parts = img_name.replace(".png", "").split("_")
                    page_info = parts[0].replace("page", "Page ") if len(parts) > 0 else ""
                    st.image(img_path, use_container_width=True, caption=img_name)


# ============================================================
# Page 1: Chat Interface
# ============================================================
if page == "💬 Chat Interface":
    st.title("💬 BVRIT HYDERABAD FAQ Chatbot")
    st.markdown(
        "Ask any question about BVRIT HYDERABAD College of Engineering for Women — "
        "admissions, placements, fees, departments, facilities, and more. "
        "Relevant campus images will be displayed when available."
    )

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "citations" not in st.session_state:
        st.session_state.citations = {}

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

            # Show images if available (for assistant messages)
            if msg["role"] == "assistant" and msg.get("images"):
                with st.expander("🖼️ View Campus Images", expanded=True):
                    display_images_grid(msg["images"])

            # Show citations if available
            if msg["role"] == "assistant" and msg.get("citations"):
                with st.expander("📚 View Source Citations", expanded=False):
                    for cit in msg["citations"]:
                        st.markdown(
                            f"**Source {cit['number']}** (Page {cit.get('page', 'N/A')})"
                        )
                        preview = cit["preview"]
                        st.text(preview[:200] + "..." if len(preview) > 200 else preview)
                        # Show per-source images if different from the main image set
                        source_images = cit.get("images", [])
                        if source_images and len(source_images) > 0:
                            for img in source_images:
                                if os.path.exists(img):
                                    st.image(img, width=200, caption=os.path.basename(img))
                        st.markdown("---")

    # Chat input
    if prompt := st.chat_input("Ask a question about BVRIT HYDERABAD..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("🔍 Retrieving information..."):
                try:
                    response = generate_response(prompt)
                    # Use .get() for ALL fields to handle cached old module versions
                    answer = response.get("answer", "I'm sorry, I couldn't generate a response.")
                    citations = response.get("citations", [])
                    images = response.get("images", [])
                    has_answer = response.get("has_answer", False)

                    # Display answer
                    if has_answer and answer:
                        st.markdown(answer)

                        # Display images prominently if available
                        if images:
                            with st.expander("🖼️ Campus Images", expanded=True):
                                display_images_grid(images)

                        # Display citations
                        if citations:
                            with st.expander("📚 View Source Citations", expanded=True):
                                for cit in citations:
                                    st.markdown(
                                        f"**Source {cit['number']}** (Page {cit.get('page', 'N/A')})"
                                    )
                                    preview = cit["preview"]
                                    st.text(preview[:200] + "..." if len(preview) > 200 else preview)
                                    st.markdown("---")
                    else:
                        st.info(answer)

                    # Save to session
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "citations": citations or [],
                        "images": images or [],
                    })

                except Exception as e:
                    import traceback
                    error_details = traceback.format_exc()
                    print(f"[ERROR] {error_details}")
                    error_msg = f"❌ **Error generating response:** {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg,
                        "citations": [],
                        "images": [],
                    })

    # Clear chat button
    if st.session_state.messages:
        if st.button("🗑️ Clear Chat History"):
            st.session_state.messages = []
            st.session_state.citations = {}
            st.rerun()

# ============================================================
# Page 2: Evaluation Dashboard
# ============================================================
elif page == "📊 Evaluation Dashboard":
    st.title("📊 Automated Evaluation Dashboard")
    st.markdown(
        "Evaluate the chatbot's performance using **RAGAS metrics** and "
        "**LLM-as-a-Judge** framework across 8 dimensions."
    )

    # Check if API key is set
    if not API_KEY or API_KEY == "your-openrouter-api-key-here":
        st.error(
            "⚠️ **API Key Required**\n\n"
            "Please set your `OPENROUTER_API_KEY` in the `.env` file to run evaluations."
        )
        st.stop()

    # Run evaluation button
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"**Test Suite:** {len(TEST_QUESTIONS)} predefined questions covering all knowledge base categories")
    with col2:
        run_eval = st.button("🚀 Run Full Evaluation", type="primary")

    if run_eval:
        progress_bar = st.progress(0, text="Starting evaluation...")
        status_text = st.empty()

        # Run RAGAS evaluation
        status_text.text("📊 Running RAGAS metrics evaluation...")
        progress_bar.progress(20, text="Evaluating Faithfulness, Relevancy, Precision, Recall...")

        try:
            ragas_results, _ = evaluate_with_ragas()
            progress_bar.progress(50, text="RAGAS evaluation complete. Running LLM-as-a-Judge...")
        except Exception as e:
            st.error(f"❌ RAGAS evaluation failed: {str(e)}")
            ragas_results = {"faithfulness": 0, "answer_relevancy": 0, "context_precision": 0, "context_recall": 0}

        # Run LLM-as-a-Judge
        status_text.text("🤖 Running LLM-as-a-Judge evaluation across 8 dimensions...")
        try:
            judge_results = evaluate_llm_as_judge()
            progress_bar.progress(90, text="Evaluation complete. Generating dashboard...")
        except Exception as e:
            st.error(f"❌ LLM-as-a-Judge evaluation failed: {str(e)}")
            judge_results = {
                "dimension_scores": {dim: 0 for dim in JUDGE_PROMPTS.keys()},
                "overall": 0,
                "detailed_results": [],
                "raw_dimension_scores": {},
            }

        # Store results in session state
        st.session_state["ragas_results"] = ragas_results
        st.session_state["judge_results"] = judge_results
        progress_bar.progress(100, text="✅ Evaluation complete!")
        status_text.text("")
        time.sleep(0.5)
        progress_bar.empty()

    # Display results if available
    if "ragas_results" in st.session_state and "judge_results" in st.session_state:
        ragas_results = st.session_state["ragas_results"]
        judge_results = st.session_state["judge_results"]

        # Overall Score Cards
        st.markdown("## 📈 Performance Overview")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            overall = judge_results.get("overall", 0)
            st.metric(
                "Overall LLM-as-a-Judge",
                f"{overall:.1f}/10",
                delta=None,
                delta_color="normal",
            )
        with col2:
            faith = ragas_results.get("faithfulness", 0)
            st.metric("Faithfulness", f"{faith:.2%}", delta=None)
        with col3:
            relevancy = ragas_results.get("answer_relevancy", 0)
            st.metric("Answer Relevancy", f"{relevancy:.2%}", delta=None)
        with col4:
            recall = ragas_results.get("context_recall", 0)
            st.metric("Context Recall", f"{recall:.2%}", delta=None)

        # RAGAS Metrics Section
        st.markdown("---")
        st.markdown("## 📊 RAGAS Metrics")

        # Bar chart for RAGAS metrics
        ragas_metrics = list(ragas_results.keys())
        ragas_scores = [ragas_results[m] for m in ragas_metrics]

        fig_ragas = px.bar(
            x=ragas_metrics,
            y=ragas_scores,
            labels={"x": "RAGAS Metric", "y": "Score (0-1)"},
            title="RAGAS Performance Metrics",
            color=ragas_scores,
            color_continuous_scale="Viridis",
            range_color=[0, 1],
            text=[f"{s:.2%}" for s in ragas_scores],
        )
        fig_ragas.update_traces(textposition="outside")
        fig_ragas.update_layout(
            xaxis_tickangle=0,
            height=400,
            yaxis_range=[0, 1.1],
        )
        st.plotly_chart(fig_ragas, use_container_width=True)

        # LLM-as-a-Judge Section
        st.markdown("---")
        st.markdown("## 🤖 LLM-as-a-Judge Evaluation")

        dim_scores = judge_results.get("dimension_scores", {})
        dim_names = list(dim_scores.keys())
        dim_values = [dim_scores[d] for d in dim_names]

        # Radar chart
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=dim_values + [dim_values[0]],  # close the loop
            theta=dim_names + [dim_names[0]],
            fill="toself",
            name="Chatbot Performance",
            line_color="blue",
        ))
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 10],
                ),
            ),
            title="LLM-as-a-Judge: 8-Dimension Performance",
            height=500,
        )
        st.plotly_chart(fig_radar, use_container_width=True)

        # Bar chart for dimensions
        fig_dim = px.bar(
            x=dim_names,
            y=dim_values,
            labels={"x": "Evaluation Dimension", "y": "Score (1-10)"},
            title="LLM-as-a-Judge Dimension Scores",
            color=dim_values,
            color_continuous_scale="Blues",
            range_color=[0, 10],
            text=[f"{s:.1f}/10" for s in dim_values],
        )
        fig_dim.update_traces(textposition="outside")
        fig_dim.update_layout(
            xaxis_tickangle=45,
            height=400,
            yaxis_range=[0, 11],
        )
        st.plotly_chart(fig_dim, use_container_width=True)

        # Detailed Results Table
        st.markdown("---")
        st.markdown("## 📋 Per-Question Breakdown")

        detailed = judge_results.get("detailed_results", [])
        if detailed:
            table_data = []
            for item in detailed:
                row = {
                    "Question": item["question"][:50] + "..." if len(item["question"]) > 50 else item["question"],
                }
                for dim, score_data in item["dimensions"].items():
                    row[dim] = score_data["score"]
                table_data.append(row)

            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True, height=400)

            # Download results as JSON
            results_json = json.dumps(
                {
                    "ragas_metrics": ragas_results,
                    "llm_as_judge": {
                        "dimension_scores": dim_scores,
                        "overall": overall,
                        "detailed_results": detailed,
                    },
                },
                indent=2,
            )
            st.download_button(
                label="📥 Download Evaluation Results (JSON)",
                data=results_json,
                file_name="bvrith_chatbot_evaluation_results.json",
                mime="application/json",
            )

    else:
        st.info(
            "👈 Click **'Run Full Evaluation'** to start the automated evaluation.\n\n"
            "This will run 10 test questions through the chatbot and evaluate the responses "
            "using RAGAS metrics and LLM-as-a-Judge across 8 dimensions."
        )

# ============================================================
# Footer
# ============================================================
st.sidebar.markdown("---")
st.sidebar.markdown(
    "Built with ❤️ using **LangChain**, **ChromaDB**, **OpenRouter**, **PyMuPDF**, and **Streamlit**"
)