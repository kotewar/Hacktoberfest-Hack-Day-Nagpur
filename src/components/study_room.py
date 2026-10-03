import streamlit as st
from pathlib import Path
from typing import Dict, Any

from config import BOOKS_DIR
from src.rag_engine import rag_engine, extract_text_from_pdf
from src.llm_client import (
    ask_socratic_tutor,
    ask_socratic_tutor_with_thinking,
    explain_simply_analogy,
    summarize_key_formulas
)
from src.database import log_study_activity

def render_study_room(user: Dict[str, Any]):
    """Renders the split-screen Study Room tab."""
    st.markdown("## 📖 Interactive Study Room & Socratic Co-Pilot")
    st.caption("Read chapters offline, ask Socratic questions, or get instant analogies.")

    # Initialize session state for Study Room chat and quick actions
    if "study_messages" not in st.session_state:
        st.session_state.study_messages = [
            {"role": "assistant", "content": "Namaste! I am your offline Gemma study companion. Ask me anything about your chapter or paste a difficult paragraph, and I'll help you understand it step-by-step!"}
        ]
    if "active_passage" not in st.session_state:
        st.session_state.active_passage = ""

    # Split layout: Left column = Textbook Reader; Right column = AI Co-Pilot
    col_left, col_right = st.columns([1.1, 1.0], gap="large")

    # ================= LEFT COLUMN: TEXTBOOK READER =================
    with col_left:
        st.subheader("📚 Offline Textbook Reader")

        # Discover all available books/chapters
        available_files = list(BOOKS_DIR.glob("*"))
        valid_files = [f for f in available_files if f.suffix.lower() in [".pdf", ".txt", ".md"]]

        selected_text = ""
        chapter_title = ""
        subject_name = ""

        if valid_files:
            file_options = {f.name: f for f in valid_files}
            selected_filename = st.selectbox(
                "Select Textbook / Chapter:",
                options=list(file_options.keys()),
                key="study_book_selector"
            )
            target_path = file_options[selected_filename]

            # Determine subject and chapter
            parts = target_path.stem.replace("_", " ").split(" - ")
            subject_name = parts[0].strip() if len(parts) > 1 else "General"
            chapter_title = parts[1].strip() if len(parts) > 1 else target_path.stem.replace("_", " ")

            # Read file content
            if target_path.suffix.lower() == ".pdf":
                raw_content = extract_text_from_pdf(target_path)
            else:
                try:
                    raw_content = target_path.read_text(encoding="utf-8")
                except Exception:
                    raw_content = target_path.read_text(encoding="latin-1", errors="ignore")

            st.session_state.active_chapter = chapter_title
            st.session_state.active_subject = subject_name
            st.session_state.active_chapter_text = raw_content

            # Display textbook in scrollable container
            with st.container(height=380):
                st.markdown(f"### {chapter_title} (`{subject_name}`)")
                st.markdown(raw_content)

        else:
            st.info("No textbooks found in `data/books/`. Upload a PDF or TXT below to start studying offline.")

        # Upload new textbook feature
        with st.expander("➕ Upload New Textbook (PDF / TXT)"):
            uploaded = st.file_uploader("Upload syllabus file:", type=["pdf", "txt", "md"], key="file_upload_input")
            if uploaded is not None:
                save_dest = BOOKS_DIR / uploaded.name
                with open(save_dest, "wb") as f:
                    f.write(uploaded.getbuffer())
                st.success(f"Saved `{uploaded.name}`. Indexing into vector store...")
                rag_engine.index_books(BOOKS_DIR)
                st.success("Indexing complete! Refreshing...")
                st.rerun()

        st.divider()

        # Text selection / excerpt tool
        st.markdown("#### ✂️ Focus Passage & Quick AI Shortcuts")
        passage_input = st.text_area(
            "Paste or type an excerpt from above to analyze:",
            value=st.session_state.active_passage,
            height=110,
            placeholder="e.g. Paste a law, formula, or difficult biological definition here...",
            key="custom_passage_box"
        )

        btn_c1, btn_c2, btn_c3 = st.columns(3)
        
        with btn_c1:
            if st.button("💡 Explain Simply", use_container_width=True):
                target = passage_input.strip() or st.session_state.get("active_chapter_text", "")[:600]
                if target:
                    with st.spinner("Gemma is simplifying with analogies..."):
                        response = explain_simply_analogy(target)
                        st.session_state.study_messages.append({"role": "user", "content": f"Explain simply:\n> {target[:150]}..."})
                        st.session_state.study_messages.append({"role": "assistant", "content": response})
                        log_study_activity(user["id"], minutes_spent=2, questions_answered=0)
                        st.rerun()

        with btn_c2:
            if st.button("🇮🇳 Hindi / Village Analogy", use_container_width=True):
                target = passage_input.strip() or st.session_state.get("active_chapter_text", "")[:600]
                if target:
                    with st.spinner("Crafting a real-world village/home analogy..."):
                        prompt_mod = (
                            "Explain the following concept using simple conversational language and a real-world "
                            "village, farm, or kitchen analogy that an Indian student can easily visualize:\n"
                            f"{target}"
                        )
                        from src.llm_client import query_ollama
                        response = query_ollama(prompt_mod)
                        st.session_state.study_messages.append({"role": "user", "content": f"Local village analogy for:\n> {target[:150]}..."})
                        st.session_state.study_messages.append({"role": "assistant", "content": response})
                        log_study_activity(user["id"], minutes_spent=2, questions_answered=0)
                        st.rerun()

        with btn_c3:
            if st.button("📐 Key Formulas & Laws", use_container_width=True):
                target = passage_input.strip() or st.session_state.get("active_chapter_text", "")[:1200]
                if target:
                    with st.spinner("Extracting formulas and definitions..."):
                        response = summarize_key_formulas(target)
                        st.session_state.study_messages.append({"role": "user", "content": f"Formulas & Key Laws for {st.session_state.get('active_chapter', 'Passage')}"})
                        st.session_state.study_messages.append({"role": "assistant", "content": response})
                        log_study_activity(user["id"], minutes_spent=2, questions_answered=0)
                        st.rerun()

    # ================= RIGHT COLUMN: SOCRATIC CHAT CO-PILOT =================
    with col_right:
        st.subheader("🤖 Socratic Study Co-Pilot")
        
        c_top1, c_top2 = st.columns([1.2, 0.8])
        with c_top1:
            socratic_mode = st.toggle("Socratic Guide Mode", value=True, help="When ON, Gemma asks probing questions to lead you to the answer instead of spoon-feeding.")
            show_thoughts = st.checkbox("🧠 Show Gemma's Inner Thought Process", value=True, help="Reveals Gemma's internal Chain-of-Thought reasoning steps.")
        with c_top2:
            if st.button("🧹 Clear Chat", use_container_width=True):
                st.session_state.study_messages = [
                    {"role": "assistant", "content": "Chat cleared. What topic are we exploring today?"}
                ]
                st.rerun()

        # Chat history container
        chat_box = st.container(height=480)
        with chat_box:
            for msg in st.session_state.study_messages:
                with st.chat_message(msg["role"]):
                    if msg.get("thought"):
                        with st.expander("🧠 Gemma's Internal Thinking & Pedagogical Plan", expanded=False):
                            st.markdown(msg["thought"])
                    st.markdown(msg["content"])
                    if msg.get("telemetry"):
                        t = msg["telemetry"]
                        st.caption(f"⚡ Inferred locally in {t.get('elapsed_sec', 0)}s on CPU (`{t.get('model', 'gemma')}`)")

        # Chat Input
        user_query = st.chat_input("Ask a question about this chapter (e.g. Why is respiration exothermic?)...")
        if user_query:
            # Display user message
            st.session_state.study_messages.append({"role": "user", "content": user_query})
            
            # Retrieve relevant context from RAG engine
            active_subj = st.session_state.get("active_subject", "")
            context = rag_engine.retrieve_context(user_query, subject=active_subj, top_k=2)
            
            # If no context found from vector store, provide active chapter snippet
            if not context and st.session_state.get("active_chapter_text"):
                context = st.session_state.active_chapter_text[:800]

            with st.spinner("Gemma is thinking and planning its explanation..."):
                if show_thoughts:
                    thought, reply, telemetry = ask_socratic_tutor_with_thinking(
                        query=user_query,
                        context=context,
                        socratic_mode=socratic_mode
                    )
                    st.session_state.study_messages.append({
                        "role": "assistant",
                        "content": reply,
                        "thought": thought,
                        "telemetry": telemetry
                    })
                else:
                    reply = ask_socratic_tutor(
                        query=user_query,
                        context=context,
                        socratic_mode=socratic_mode
                    )
                    st.session_state.study_messages.append({"role": "assistant", "content": reply})
            
            log_study_activity(user["id"], minutes_spent=3, questions_answered=0)
            st.rerun()
