import re
import sys
from pathlib import Path
from datetime import datetime
import streamlit as st
import pandas as pd

# Base setup
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import APP_TITLE, APP_TAGLINE, DEFAULT_MODEL, BOOKS_DIR
from src.database import (
    init_db,
    get_all_users,
    get_or_create_user,
    get_study_summary,
    get_topic_mastery_record,
    get_topic_mastery,
    get_due_reviews,
    get_user_quiz_results,
    get_daily_study_logs,
    save_quiz_result,
    log_study_activity
)
from src.sm2 import update_topic_after_quiz
from src.rag_engine import rag_engine, extract_text_from_pdf
from src.llm_client import (
    check_ollama_status,
    get_ollama_latest_logs,
    ask_socratic_tutor_with_thinking,
    ask_socratic_tutor,
    explain_simply_analogy,
    summarize_key_formulas,
    generate_quiz_json,
    evaluate_subjective_answer,
    generate_concept_graph,
    explain_concept_node,
    explain_cs_ai_concept_visually,
    query_ollama,
    CS_AI_PRESET_EXPLANATIONS
)

# Page configuration
st.set_page_config(
    page_title="EduGemma - Offline AI Study Cockpit",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
init_db()

# Custom CSS for high-impact single-page cockpit
st.markdown("""
<style>
    .cockpit-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding-bottom: 8px;
        border-bottom: 1px solid rgba(128, 128, 128, 0.25);
        margin-bottom: 14px;
    }
    .cockpit-title {
        font-size: 2.1rem;
        font-weight: 800;
        background: linear-gradient(90deg, #60A5FA, #A78BFA);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.5px;
    }
    .offline-badge {
        background-color: rgba(16, 185, 129, 0.15);
        color: #34D399;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.82rem;
        font-weight: 700;
        border: 1px solid rgba(16, 185, 129, 0.4);
    }
    .stat-pill-streak {
        display: inline-flex;
        align-items: center;
        background: rgba(245, 158, 11, 0.15);
        border: 1px solid rgba(245, 158, 11, 0.4);
        color: #FBBF24;
        padding: 6px 12px;
        border-radius: 8px;
        font-size: 0.84rem;
        font-weight: 600;
    }
    .stat-pill-mastery {
        display: inline-flex;
        align-items: center;
        background: rgba(16, 185, 129, 0.15);
        border: 1px solid rgba(16, 185, 129, 0.4);
        color: #34D399;
        padding: 6px 12px;
        border-radius: 8px;
        font-size: 0.84rem;
        font-weight: 600;
    }
    .stat-pill-interval {
        display: inline-flex;
        align-items: center;
        background: rgba(99, 102, 241, 0.15);
        border: 1px solid rgba(99, 102, 241, 0.4);
        color: #A5B4FC;
        padding: 6px 12px;
        border-radius: 8px;
        font-size: 0.84rem;
        font-weight: 600;
    }
    .stat-pill-review {
        display: inline-flex;
        align-items: center;
        background: rgba(56, 189, 248, 0.15);
        border: 1px solid rgba(56, 189, 248, 0.4);
        color: #38BDF8;
        padding: 6px 12px;
        border-radius: 8px;
        font-size: 0.84rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

def render_styled_table(df: pd.DataFrame) -> None:
    """Renders a clean styled HTML table that works with zero external binary dependencies."""
    table_html = df.to_html(classes="cockpit-table", index=False, escape=False)
    styled_html = f"""
    <style>
        .cockpit-table-wrapper {{
            overflow-x: auto;
            margin-top: 6px;
            margin-bottom: 6px;
            border-radius: 8px;
            border: 1px solid rgba(128, 128, 128, 0.25);
            background: rgba(128, 128, 128, 0.05);
        }}
        .cockpit-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.88rem;
            text-align: left;
            color: inherit;
        }}
        .cockpit-table th {{
            background-color: rgba(128, 128, 128, 0.12);
            color: #60A5FA;
            font-weight: 600;
            padding: 9px 12px;
            border-bottom: 1px solid rgba(128, 128, 128, 0.2);
        }}
        .cockpit-table td {{
            padding: 8px 12px;
            border-bottom: 1px solid rgba(128, 128, 128, 0.08);
            color: inherit;
        }}
        .cockpit-table tr:hover {{
            background-color: rgba(128, 128, 128, 0.1);
        }}
    </style>
    <div class="cockpit-table-wrapper">
        {table_html}
    </div>
    """
    st.markdown(styled_html, unsafe_allow_html=True)

def render_diagram_text(raw_text: str):
    """Renders text extracting any embedded Mermaid diagrams into native visual blocks."""
    mermaid_blocks = re.findall(r"```mermaid\s*(.*?)```", raw_text, re.DOTALL)
    if mermaid_blocks:
        parts = re.split(r"```mermaid\s*.*?```", raw_text, flags=re.DOTALL)
        for i, part in enumerate(parts):
            if part.strip():
                st.markdown(part.strip())
            if i < len(mermaid_blocks):
                with st.container(border=True):
                    st.caption("📊 **Interactive Flowchart / Architecture Diagram**")
                    st.markdown(f"```mermaid\n{mermaid_blocks[i].strip()}\n```")
    else:
        st.markdown(raw_text)

def main():
    # ================= SIDEBAR: STUDENT PROFILE & OLLAMA STATUS =================
    with st.sidebar:
        st.markdown("### 🎓 EduGemma")
        st.markdown("<span class='offline-badge'>✈️ 100% Offline / Airplane Mode</span>", unsafe_allow_html=True)
        st.caption("Unified on-device AI cockpit for students in low/no connectivity areas.")
        st.divider()

        # Student Switcher
        st.markdown("#### 👤 Student Profile")
        users = get_all_users()
        user_names = [u["username"] for u in users]
        selected_username = st.selectbox("Active Profile:", options=user_names, index=0)
        
        with st.expander("➕ Add New Profile"):
            new_name = st.text_input("Name:", placeholder="e.g., Priya, Aarav...")
            if st.button("Create Profile", use_container_width=True) and new_name.strip():
                get_or_create_user(new_name)
                st.rerun()

        active_user = get_or_create_user(selected_username if selected_username else "Student")
        st.divider()

        # Local Engine Health
        st.markdown("#### 🖥️ Local AI Inference")
        ollama_ok, models = check_ollama_status()
        if ollama_ok:
            st.markdown("● **Ollama Engine:** <span style='color:#059669; font-weight:700;'>Connected (localhost)</span>", unsafe_allow_html=True)
            if models:
                default_idx = models.index(DEFAULT_MODEL) if DEFAULT_MODEL in models else 0
                chosen_model = st.selectbox("Active Gemma Model:", options=models, index=default_idx)
                st.session_state.selected_model = chosen_model
            
            with st.expander("📟 Live Terminal Engine Logs", expanded=False):
                latest_logs = get_ollama_latest_logs(n_lines=12)
                st.code(latest_logs, language="text")
                if st.button("🔄 Refresh Logs", use_container_width=True):
                    st.rerun()
                st.caption("PowerShell live tail: `Get-Content $env:LOCALAPPDATA\\Ollama\\server.log -Wait -Tail 25`")
        else:
            st.markdown("● **Ollama Engine:** <span style='color:#DC2626; font-weight:700;'>Disconnected</span>", unsafe_allow_html=True)
            st.warning("Start Ollama locally: `ollama run gemma2:2b`")

        st.divider()
        st.caption("EduGemma v1.0 • Built with Streamlit, Gemma-2, SQLite & ChromaDB")

    # ================= TOP COCKPIT COMMAND BAR =================
    # Discover available books
    available_files = list(BOOKS_DIR.glob("*"))
    valid_files = [f for f in available_files if f.suffix.lower() in [".pdf", ".txt", ".md"]]
    file_map = {f.name: f for f in valid_files}

    c_hdr1, c_hdr2 = st.columns([3, 1])
    with c_hdr1:
        st.markdown(f"<div class='cockpit-header'><div class='cockpit-title'>🎓 {APP_TITLE}</div></div>", unsafe_allow_html=True)
    with c_hdr2:
        st.markdown(f"<div style='text-align:right; padding-top:10px;'>👤 <b>Student:</b> <code>{active_user['username']}</code> &nbsp;|&nbsp; ⚡ <b>Model:</b> <code>{st.session_state.get('selected_model', DEFAULT_MODEL)}</code></div>", unsafe_allow_html=True)

    # Global Topic Selector & Real-Time Mastery Strip in a native theme-aware container
    with st.container(border=True):
        col_sel, col_stat = st.columns([1.5, 2.0], gap="medium")

        with col_sel:
            selected_file_name = st.selectbox(
                "🎯 Active Study Topic / Chapter:",
                options=list(file_map.keys()),
                index=0 if valid_files else 0,
                key="cockpit_chapter_selector"
            )
            target_file = file_map[selected_file_name]
            parts = target_file.stem.replace("_", " ").split(" - ")
            active_subject = parts[0].strip() if len(parts) > 1 else "General"
            active_chapter = parts[1].strip() if len(parts) > 1 else target_file.stem.replace("_", " ")

        # Topic-specific Mastery & Repetition Stats from SQLite
        topic_rec = get_topic_mastery_record(active_user["id"], active_chapter)
        summary_stats = get_study_summary(active_user["id"])

        mastery_pct = topic_rec["mastery_percentage"] if topic_rec else 0.0
        attempts = topic_rec["attempts"] if topic_rec else 0
        interval = topic_rec["interval_days"] if topic_rec else 1
        next_rev = topic_rec["next_review"] if topic_rec else "Not Scheduled"

        if mastery_pct >= 80:
            status_badge = "🟢 Mastered"
        elif mastery_pct >= 50:
            status_badge = "🟡 In Progress"
        else:
            status_badge = "🔴 Needs Practice"

        with col_stat:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            st.markdown(f"""
            <div style='display:flex; flex-wrap:wrap; gap:8px; align-items:center;'>
                <span class='stat-pill-streak'>🔥 Streak: <b>{summary_stats['streak_days']} Day(s)</b></span>
                <span class='stat-pill-mastery'>🎯 Mastery: <b>{mastery_pct}% ({status_badge})</b></span>
                <span class='stat-pill-interval'>🔁 Interval: <b>{interval}d</b></span>
                <span class='stat-pill-review'>⏰ Review: <b>{next_rev[:10] if next_rev != 'Not Scheduled' else 'Today'}</b></span>
            </div>
            """, unsafe_allow_html=True)

    # Load active chapter text
    if target_file.suffix.lower() == ".pdf":
        active_content = extract_text_from_pdf(target_file)
    else:
        try:
            active_content = target_file.read_text(encoding="utf-8")
        except Exception:
            active_content = target_file.read_text(encoding="latin-1", errors="ignore")

    st.session_state.active_chapter = active_chapter
    st.session_state.active_subject = active_subject
    st.session_state.active_content = active_content

    # ================= TWO-COLUMN INTERACTIVE LEARNING CANVAS =================
    col_canvas, col_copilot = st.columns([1.15, 1.0], gap="medium")

    # ---------- LEFT COLUMN: KNOWLEDGE CANVAS ----------
    with col_canvas:
        canvas_mode = st.radio(
            "Canvas View:",
            options=["📖 Chapter Notes", "🗺️ Concept Mind Map", "💻 CS & AI Deep Dive"],
            horizontal=True,
            label_visibility="collapsed",
            key="canvas_view_mode"
        )

        if canvas_mode == "📖 Chapter Notes":
            with st.container(height=420, border=True):
                st.markdown(f"### {active_chapter} (`{active_subject}`)")
                st.markdown(active_content)

            # Quick Action Pills
            c_act1, c_act2, c_act3 = st.columns(3)
            with c_act1:
                if st.button("💡 Explain Simply", use_container_width=True):
                    with st.spinner("Gemma is simplifying with analogies..."):
                        ans = explain_simply_analogy(active_content[:700])
                        st.session_state.study_messages.append({"role": "user", "content": f"Explain '{active_chapter}' simply with analogies."})
                        st.session_state.study_messages.append({"role": "assistant", "content": ans})
                        log_study_activity(active_user["id"], minutes_spent=2, questions_answered=0)
                        st.rerun()
            with c_act2:
                if st.button("🇮🇳 Village / Home Analogy", use_container_width=True):
                    with st.spinner("Crafting real-world rural/home analogy..."):
                        p = f"Explain the core principle of {active_chapter} using a vivid Indian kitchen, village farm, or cricket analogy:\n{active_content[:700]}"
                        ans = query_ollama(p)
                        st.session_state.study_messages.append({"role": "user", "content": f"Give a village/kitchen analogy for {active_chapter}."})
                        st.session_state.study_messages.append({"role": "assistant", "content": ans})
                        log_study_activity(active_user["id"], minutes_spent=2, questions_answered=0)
                        st.rerun()
            with c_act3:
                if st.button("📐 Key Formulas & Laws", use_container_width=True):
                    with st.spinner("Extracting formulas and definitions..."):
                        ans = summarize_key_formulas(active_content[:1000])
                        st.session_state.study_messages.append({"role": "user", "content": f"Key formulas and laws for {active_chapter}."})
                        st.session_state.study_messages.append({"role": "assistant", "content": ans})
                        log_study_activity(active_user["id"], minutes_spent=2, questions_answered=0)
                        st.rerun()

        elif canvas_mode == "🗺️ Concept Mind Map":
            with st.container(height=470, border=True):
                st.markdown(f"#### 🌲 Visual Knowledge Tree: {active_chapter}")
                if "cockpit_mindmap_cache" not in st.session_state:
                    st.session_state.cockpit_mindmap_cache = {}

                if active_chapter not in st.session_state.cockpit_mindmap_cache:
                    with st.spinner("Generating visual knowledge graph..."):
                        st.session_state.cockpit_mindmap_cache[active_chapter] = generate_concept_graph(f"{active_chapter}\n{active_content[:1000]}")
                
                g_data = st.session_state.cockpit_mindmap_cache[active_chapter]
                st.markdown(f"```mermaid\n{g_data.get('mermaid', '')}\n```")
                
                # Clickable concept nodes
                st.markdown("##### 🔍 Concept Node Spotlights:")
                nodes = g_data.get("nodes", [])
                for idx, node in enumerate(nodes[:4]):
                    n_lbl = node.get("label", f"Node {idx+1}")
                    if st.button(f"💡 Explain: {n_lbl}", key=f"cockpit_node_{idx}"):
                        with st.spinner(f"Gemma is breaking down {n_lbl}..."):
                            exp = explain_concept_node(n_lbl, topic_context=active_content[:800])
                            st.session_state.study_messages.append({"role": "user", "content": f"Explain concept node: {n_lbl}"})
                            st.session_state.study_messages.append({"role": "assistant", "content": exp})
                            st.rerun()

        elif canvas_mode == "💻 CS & AI Deep Dive":
            with st.container(height=470, border=True):
                st.markdown("#### 💻 Engineering & AI Deep Dive")
                preset_options = list(CS_AI_PRESET_EXPLANATIONS.keys())
                selected_preset = st.selectbox("High-Yield Topic Architecture:", options=preset_options, key="cs_cockpit_preset")
                
                if selected_preset:
                    render_diagram_text(CS_AI_PRESET_EXPLANATIONS[selected_preset])

    # ---------- RIGHT COLUMN: SOCRATIC CO-PILOT ----------
    with col_copilot:
        st.markdown("### 🤖 Socratic Study Co-Pilot")
        
        c_ctl1, c_ctl2 = st.columns([1.5, 0.7])
        with c_ctl1:
            socratic_mode = st.toggle("Socratic Guide Mode", value=True, help="Guides with probing questions instead of spoon-feeding direct answers.")
            show_thoughts = st.checkbox("🧠 Show Gemma's Inner Thinking", value=True)
        with c_ctl2:
            if st.button("🧹 Clear", use_container_width=True):
                st.session_state.study_messages = [
                    {"role": "assistant", "content": f"Namaste! I'm your offline Gemma tutor for **{active_chapter}**. What concept can I help you master?"}
                ]
                st.rerun()

        # Chat history
        if "study_messages" not in st.session_state or len(st.session_state.study_messages) == 0:
            st.session_state.study_messages = [
                {"role": "assistant", "content": f"Namaste! I'm your offline Gemma tutor for **{active_chapter}**. What concept can I help you master?"}
            ]

        with st.container(height=340, border=True):
            for msg in st.session_state.study_messages:
                with st.chat_message(msg["role"]):
                    if msg.get("thought"):
                        with st.expander("🧠 Gemma's Internal Thinking & Pedagogical Plan", expanded=False):
                            st.markdown(msg["thought"])
                    st.markdown(msg["content"])
                    if msg.get("telemetry"):
                        t = msg["telemetry"]
                        st.caption(f"⚡ Inferred locally in {t.get('elapsed_sec', 0)}s on CPU (`{t.get('model', 'gemma')}`)")

        # Quick Question Chips
        q1, q2, q3 = st.columns(3)
        chip_query = None
        with q1:
            if st.button("💡 Real-world analogy?", key="chip_1", use_container_width=True):
                chip_query = f"Can you give me a real-world intuition or analogy for {active_chapter}?"
        with q2:
            if st.button("⚠️ Common exam trap?", key="chip_2", use_container_width=True):
                chip_query = f"What is the #1 mistake students make on exams regarding {active_chapter}?"
        with q3:
            if st.button("❓ Test my concept", key="chip_3", use_container_width=True):
                chip_query = f"Ask me 1 probing question to test my understanding of {active_chapter}."

        user_input = st.chat_input("Ask a doubt or enter an excerpt...") or chip_query

        if user_input:
            st.session_state.study_messages.append({"role": "user", "content": user_input})
            context = rag_engine.retrieve_context(user_input, subject=active_subject, top_k=2) or active_content[:800]
            
            with st.spinner("Gemma is thinking and reasoning..."):
                if show_thoughts:
                    thought, reply, telem = ask_socratic_tutor_with_thinking(
                        query=user_input,
                        context=context,
                        socratic_mode=socratic_mode
                    )
                    st.session_state.study_messages.append({
                        "role": "assistant",
                        "content": reply,
                        "thought": thought,
                        "telemetry": telem
                    })
                else:
                    reply = ask_socratic_tutor(user_input, context=context, socratic_mode=socratic_mode)
                    st.session_state.study_messages.append({"role": "assistant", "content": reply})

            log_study_activity(active_user["id"], minutes_spent=3, questions_answered=0)
            st.rerun()

    # ================= BOTTOM UNIFIED PRACTICE & RECALL DRAWER =================
    st.divider()
    st.markdown("### ⚡ Active Recall, Quiz & Spaced Repetition Arena")
    
    tab_quiz_mcq, tab_sub_eval, tab_analytics = st.tabs([
        "📝 Quick 3-Question Active Recall Quiz",
        "✍️ Subjective Problem Evaluator",
        "📊 Student Mastery Matrix & Daily Streak"
    ])

    # 1. Quick MCQ Quiz on Active Topic
    with tab_quiz_mcq:
        c_qhead1, c_qhead2 = st.columns([3, 1])
        with c_qhead1:
            st.caption(f"Generated directly from the active chapter: **{active_chapter}**")
        with c_qhead2:
            if st.button("⚡ Generate New Quiz", type="primary", use_container_width=True):
                with st.spinner(f"Gemma is generating questions for {active_chapter}..."):
                    quiz_items = generate_quiz_json(active_content[:1500], count=3)
                    st.session_state.cockpit_quiz = quiz_items
                    st.session_state.cockpit_quiz_submitted = False
                    st.session_state.cockpit_quiz_topic = active_chapter
                    st.session_state.cockpit_quiz_subject = active_subject
                    st.rerun()

        if "cockpit_quiz" in st.session_state and st.session_state.cockpit_quiz:
            with st.form("cockpit_quiz_form"):
                user_choices = {}
                for idx, q_item in enumerate(st.session_state.cockpit_quiz):
                    st.markdown(f"**Q{idx + 1}. {q_item['question']}**")
                    options = q_item.get("options", [])
                    user_choices[idx] = st.radio(
                        f"q_{idx}",
                        options=list(range(len(options))),
                        format_func=lambda i: options[i],
                        key=f"cq_{idx}",
                        label_visibility="collapsed"
                    )
                    st.markdown("---")

                submit_btn = st.form_submit_button("✅ Submit Answers", use_container_width=True)

            if submit_btn:
                correct_count = sum(1 for idx, q in enumerate(st.session_state.cockpit_quiz) if user_choices.get(idx) == q.get("correct_index", 0))
                total_q = len(st.session_state.cockpit_quiz)
                st.session_state.cockpit_quiz_submitted = True
                st.session_state.cockpit_quiz_score = correct_count
                st.session_state.cockpit_user_choices = user_choices

                # Persist in SQLite
                save_quiz_result(active_user["id"], active_subject, active_chapter, total_q, float(correct_count))
                sm2_stats = update_topic_after_quiz(active_user["id"], active_chapter, float(correct_count), total_q)
                st.session_state.cockpit_sm2 = sm2_stats
                st.rerun()

            if st.session_state.get("cockpit_quiz_submitted", False):
                score = st.session_state.get("cockpit_quiz_score", 0)
                tot = len(st.session_state.cockpit_quiz)
                pct = round(score / tot * 100) if tot > 0 else 0
                st.success(f"🎉 You scored **{score} / {tot}** ({pct}%). Topic mastery updated live at the top bar!")
                
                for idx, q in enumerate(st.session_state.cockpit_quiz):
                    u_ans = st.session_state.cockpit_user_choices.get(idx)
                    c_ans = q.get("correct_index", 0)
                    opts = q.get("options", [])
                    status_lbl = "✅ Correct" if u_ans == c_ans else "❌ Incorrect"
                    with st.expander(f"Question {idx+1}: {status_lbl}"):
                        st.markdown(f"**Question:** {q['question']}")
                        if 0 <= u_ans < len(opts):
                            st.markdown(f"- Your Answer: `{opts[u_ans]}`")
                        if 0 <= c_ans < len(opts):
                            st.markdown(f"- Correct Answer: `{opts[c_ans]}`")
                        st.markdown(f"- **Explanation:** {q.get('explanation', '')}")
        else:
            st.info(f"Click **⚡ Generate New Quiz** above to test your recall on **{active_chapter}**!")

    # 2. Subjective Problem Evaluator
    with tab_sub_eval:
        st.markdown(f"##### ✍️ Short Conceptual / Problem Evaluator for `{active_chapter}`")
        subj_q = st.text_input("Problem / Question:", value=f"Explain the primary mechanism and significance of {active_chapter}.", key="subj_eval_q")
        student_ans = st.text_area("Your Explanation (2-3 sentences):", height=90, placeholder="Write your conceptual answer here...", key="subj_eval_ans")
        
        if st.button("🔍 Grade My Answer Out of 5 Marks", type="primary"):
            if student_ans.strip():
                with st.spinner("Gemma is evaluating your answer against textbook ground truth..."):
                    context_chunk = rag_engine.retrieve_context(subj_q, subject=active_subject, top_k=2) or active_content[:800]
                    evaluation = evaluate_subjective_answer(subj_q, reference_facts=context_chunk, student_answer=student_ans)
                    st.markdown("### 📊 AI Tutor Evaluation:")
                    st.markdown(evaluation)
                    log_study_activity(active_user["id"], minutes_spent=4, questions_answered=1)

    # 3. Overall Student Mastery Matrix & Daily Streak
    with tab_analytics:
        col_m1, col_m2 = st.columns([1.2, 1.0])
        with col_m1:
            st.markdown("##### 🧠 All Practiced Topics (SM-2 Spaced Repetition):")
            all_topics = get_topic_mastery(active_user["id"])
            if all_topics:
                df_top = pd.DataFrame(all_topics)[["topic_name", "mastery_percentage", "attempts", "interval_days", "next_review"]].rename(columns={
                    "topic_name": "Topic", "mastery_percentage": "Mastery %", "attempts": "Attempts", "interval_days": "Interval (days)", "next_review": "Next Due Review"
                })
                render_styled_table(df_top)
            else:
                st.info("Complete a quiz above to start tracking topic mastery!")
        with col_m2:
            st.markdown("##### 📜 Recent Quiz History:")
            q_res = get_user_quiz_results(active_user["id"], limit=6)
            if q_res:
                df_q = pd.DataFrame(q_res)[["timestamp", "chapter", "score", "total_questions"]].rename(columns={
                    "timestamp": "Time", "chapter": "Topic", "score": "Score", "total_questions": "Total"
                })
                render_styled_table(df_q)
            else:
                st.caption("No quiz history yet.")

if __name__ == "__main__":
    main()

