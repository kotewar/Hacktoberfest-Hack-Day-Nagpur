import streamlit as st
from typing import Dict, Any, List

from config import BOOKS_DIR
from src.rag_engine import rag_engine, extract_text_from_pdf
from src.llm_client import generate_quiz_json, evaluate_subjective_answer
from src.database import save_quiz_result
from src.sm2 import update_topic_after_quiz

def render_quiz_arena(user: Dict[str, Any]):
    """Renders the Quiz Arena tab with automated MCQ generator and subjective challenge evaluator."""
    st.markdown("## 🎯 Quiz Arena & Subjective Evaluator")
    st.caption("Test your recall, receive instant grading, and schedule spaced repetition review.")

    # State initialization
    if "current_quiz" not in st.session_state:
        st.session_state.current_quiz = []
    if "quiz_submitted" not in st.session_state:
        st.session_state.quiz_submitted = False
    if "quiz_score" not in st.session_state:
        st.session_state.quiz_score = 0
    if "quiz_user_answers" not in st.session_state:
        st.session_state.quiz_user_answers = {}
    if "quiz_topic" not in st.session_state:
        st.session_state.quiz_topic = "Chemical Reactions and Equations"
    if "quiz_subject" not in st.session_state:
        st.session_state.quiz_subject = "Science"
    if "subjective_feedback" not in st.session_state:
        st.session_state.subjective_feedback = ""

    tab_mcq, tab_subjective = st.tabs(["📝 Multiple Choice Quiz", "✍️ Open-Ended Challenge Problem"])

    # ================= TAB 1: MCQ QUIZ GENERATOR =================
    with tab_mcq:
        c1, c2, c3 = st.columns([1.5, 0.8, 0.7])
        
        # Discover chapters from indexed books
        available_chapters = rag_engine.get_available_books_and_chapters()
        chapter_map = {f"[{c['subject']}] {c['chapter']}": c for c in available_chapters}
        
        with c1:
            if chapter_map:
                selected_label = st.selectbox(
                    "Select Syllabus Topic for Quiz:",
                    options=list(chapter_map.keys()),
                    key="quiz_topic_selector"
                )
                active_meta = chapter_map[selected_label]
                topic_title = active_meta["chapter"]
                topic_subj = active_meta["subject"]
            else:
                topic_title = st.text_input("Enter Topic Name:", value="Chemical Reactions")
                topic_subj = "Science"

        with c2:
            num_questions = st.select_slider("Questions:", options=[2, 3, 4, 5], value=3)

        with c3:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            generate_btn = st.button("⚡ Generate Quiz", use_container_width=True, type="primary")

        if generate_btn:
            with st.spinner(f"Gemma is generating {num_questions} questions from {topic_title}..."):
                # Retrieve context from RAG
                context = rag_engine.retrieve_context(topic_title, subject=topic_subj, top_k=3)
                if not context:
                    # Fallback to file directly
                    for f in BOOKS_DIR.glob("*"):
                        if topic_title.lower() in f.stem.lower():
                            context = extract_text_from_pdf(f) if f.suffix == ".pdf" else f.read_text(encoding="utf-8", errors="ignore")
                            break

                quiz_items = generate_quiz_json(context or topic_title, count=num_questions)
                
                st.session_state.current_quiz = quiz_items
                st.session_state.quiz_submitted = False
                st.session_state.quiz_score = 0
                st.session_state.quiz_user_answers = {}
                st.session_state.quiz_topic = topic_title
                st.session_state.quiz_subject = topic_subj
                st.rerun()

        # Render active quiz
        if st.session_state.current_quiz:
            st.markdown(f"### 📋 Quiz: {st.session_state.quiz_topic} ({len(st.session_state.current_quiz)} Questions)")
            
            # Form for answering questions
            with st.form(key="quiz_form"):
                user_choices = {}
                for idx, q_item in enumerate(st.session_state.current_quiz):
                    st.markdown(f"**Q{idx + 1}. {q_item['question']}**")
                    options = q_item.get("options", [])
                    user_choices[idx] = st.radio(
                        label=f"q_{idx}_radio",
                        options=list(range(len(options))),
                        format_func=lambda i: options[i],
                        key=f"radio_q_{idx}",
                        label_visibility="collapsed"
                    )
                    st.markdown("---")

                submit_btn = st.form_submit_button("✅ Submit Answers", use_container_width=True)

            if submit_btn:
                # Grade quiz deterministically
                correct_count = 0
                total_q = len(st.session_state.current_quiz)
                
                for idx, q_item in enumerate(st.session_state.current_quiz):
                    if user_choices.get(idx) == q_item.get("correct_index", 0):
                        correct_count += 1

                st.session_state.quiz_submitted = True
                st.session_state.quiz_score = correct_count
                st.session_state.quiz_user_answers = user_choices

                # Persist results in SQLite database
                save_quiz_result(
                    user_id=user["id"],
                    subject=st.session_state.quiz_subject,
                    chapter=st.session_state.quiz_topic,
                    total_questions=total_q,
                    score=float(correct_count)
                )

                # Update Spaced Repetition (SM-2) state
                sm2_stats = update_topic_after_quiz(
                    user_id=user["id"],
                    topic_name=st.session_state.quiz_topic,
                    score=float(correct_count),
                    total=total_q
                )
                st.session_state.latest_sm2 = sm2_stats
                st.rerun()

            # Display review and explanations after submission
            if st.session_state.quiz_submitted:
                score = st.session_state.quiz_score
                total = len(st.session_state.current_quiz)
                pct = round(score / total * 100) if total > 0 else 0

                if pct >= 80:
                    st.balloons()
                    st.success(f"🎉 Outstanding Job! You scored **{score} / {total}** ({pct}%).")
                elif pct >= 50:
                    st.info(f"👍 Good effort! You scored **{score} / {total}** ({pct}%). Review explanations below.")
                else:
                    st.warning(f"💡 Keep practicing! You scored **{score} / {total}** ({pct}%). Check the correct solutions below.")

                # Show SM-2 update notification
                if "latest_sm2" in st.session_state:
                    sm2 = st.session_state.latest_sm2
                    next_date_str = sm2["next_review"].strftime("%d %b %Y")
                    st.info(
                        f"🧠 **Spaced Repetition Updated:** Topic Mastery is now **{sm2['mastery_percentage']}%**. "
                        f"Next scheduled review in **{sm2['interval_days']} day(s)** on **{next_date_str}**."
                    )

                st.markdown("#### 🔍 Question-by-Question Review:")
                for idx, q_item in enumerate(st.session_state.current_quiz):
                    user_ans = st.session_state.quiz_user_answers.get(idx)
                    correct_ans = q_item.get("correct_index", 0)
                    options = q_item.get("options", [])
                    
                    is_correct = (user_ans == correct_ans)
                    badge = "✅ Correct" if is_correct else "❌ Incorrect"
                    
                    with st.expander(f"Question {idx + 1}: {badge}"):
                        st.markdown(f"**Question:** {q_item['question']}")
                        if 0 <= user_ans < len(options):
                            st.markdown(f"- **Your Answer:** {options[user_ans]}")
                        if 0 <= correct_ans < len(options):
                            st.markdown(f"- **Correct Answer:** {options[correct_ans]}")
                        st.markdown(f"- **Explanation:** {q_item.get('explanation', '')}")

        else:
            st.info("👆 Select a topic above and click **Generate Quiz** to begin your test!")

    # ================= TAB 2: SUBJECTIVE CHALLENGE EVALUATOR =================
    with tab_subjective:
        st.subheader("✍️ Short Answer & Subjective Evaluation")
        st.caption("Write a conceptual or scientific explanation and have Gemma grade your answer against reference facts.")

        sample_prompts = [
            ("Why is respiration considered an exothermic reaction?", "Science - Chemical Reactions"),
            ("Why does displacement occur when iron nail is kept in copper sulphate?", "Science - Chemical Reactions"),
            ("Explain the role of hydrochloric acid (HCl) in human stomach.", "Biology - Life Processes"),
            ("What is the difference between speed and velocity?", "Physics - Motion")
        ]
        
        q_selection = st.selectbox(
            "Choose a Challenge Question (or type your own):",
            options=[p[0] for p in sample_prompts] + ["Custom Question..."]
        )

        if q_selection == "Custom Question...":
            challenge_q = st.text_input("Enter Question:", placeholder="e.g. Why do leaves turn yellow in darkness?")
        else:
            challenge_q = q_selection

        student_ans = st.text_area(
            "Your Answer (Write in 2-4 sentences):",
            height=120,
            placeholder="Type your explanation using scientific terms..."
        )

        if st.button("🔍 Evaluate My Answer", type="primary"):
            if not student_ans.strip():
                st.warning("Please type your answer before submitting.")
            else:
                with st.spinner("Gemma is evaluating your explanation..."):
                    # Retrieve ground truth facts
                    facts = rag_engine.retrieve_context(challenge_q, top_k=2)
                    feedback = evaluate_subjective_answer(
                        question=challenge_q,
                        reference_facts=facts,
                        student_answer=student_ans
                    )
                    st.session_state.subjective_feedback = feedback
                    # Log study activity
                    from src.database import log_study_activity
                    log_study_activity(user["id"], minutes_spent=4, questions_answered=1)

        if st.session_state.subjective_feedback:
            st.markdown("### 📊 AI Tutor Feedback & Marks:")
            st.markdown(st.session_state.subjective_feedback)
