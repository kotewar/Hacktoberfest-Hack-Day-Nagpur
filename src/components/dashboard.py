import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List

from src.database import (
    get_study_summary,
    get_topic_mastery,
    get_due_reviews,
    get_user_quiz_results,
    get_daily_study_logs
)

def render_styled_table(df: pd.DataFrame) -> None:
    """Renders a clean styled HTML table that works with zero external binary dependencies."""
    table_html = df.to_html(classes="edugemma-table", index=False, escape=False)
    styled_html = f"""<style>
.edugemma-table-wrapper {{
    overflow-x: auto;
    margin-top: 10px;
    margin-bottom: 10px;
    border-radius: 8px;
    border: 1px solid rgba(128, 128, 128, 0.25);
    background: rgba(128, 128, 128, 0.05);
}}
.edugemma-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.92rem;
    text-align: left;
    color: inherit;
}}
.edugemma-table th {{
    background-color: rgba(128, 128, 128, 0.12);
    color: #60A5FA;
    font-weight: 600;
    padding: 10px 14px;
    border-bottom: 2px solid rgba(128, 128, 128, 0.2);
}}
.edugemma-table td {{
    padding: 9px 14px;
    border-bottom: 1px solid rgba(128, 128, 128, 0.08);
    color: inherit;
}}
.edugemma-table tr:hover {{
    background-color: rgba(128, 128, 128, 0.1);
}}
</style>
<div class="edugemma-table-wrapper">
{table_html}
</div>"""
    st.html(styled_html)

def render_activity_visual(daily_logs: List[Dict[str, Any]]) -> None:
    """Renders a visual 14-day study activity timeline using pure SVG and CSS bars."""
    max_minutes = max([item["minutes_spent"] for item in daily_logs] + [10])
    
    cards_html = """
    <style>
        .activity-grid {
            display: flex;
            gap: 12px;
            overflow-x: auto;
            padding: 12px 4px;
        }
        .activity-bar-card {
            min-width: 82px;
            background: #F9FAFB;
            border: 1px solid #E5E7EB;
            border-radius: 8px;
            padding: 8px;
            text-align: center;
        }
        .activity-date {
            font-size: 0.75rem;
            font-weight: 600;
            color: #6B7280;
            margin-bottom: 6px;
        }
        .activity-bar-outer {
            background: #E5E7EB;
            height: 90px;
            width: 22px;
            margin: 0 auto;
            border-radius: 4px;
            display: flex;
            align-items: flex-end;
            overflow: hidden;
        }
        .activity-bar-inner {
            background: linear-gradient(180deg, #3B82F6, #1D4ED8);
            width: 100%;
            border-radius: 4px 4px 0 0;
            transition: height 0.3s ease;
        }
        .activity-val {
            font-size: 0.78rem;
            font-weight: 700;
            color: #1F2937;
            margin-top: 6px;
        }
        .activity-sub {
            font-size: 0.70rem;
            color: #9CA3AF;
        }
    </style>
    <div class="activity-grid">
    """
    
    for log in daily_logs:
        mins = log.get("minutes_spent", 0)
        qs = log.get("questions_answered", 0)
        d_str = log.get("date", "")
        # Format date as 'DD Mon'
        try:
            d_fmt = datetime.strptime(d_str, "%Y-%m-%d").strftime("%d %b")
        except Exception:
            d_fmt = d_str[-5:]
            
        height_pct = min(100, max(8, int((mins / max_minutes) * 100))) if mins > 0 else 4
        bar_color = "linear-gradient(180deg, #10B981, #059669)" if qs > 0 else "linear-gradient(180deg, #3B82F6, #1D4ED8)"

        cards_html += f"""
        <div class="activity-bar-card">
            <div class="activity-date">{d_fmt}</div>
            <div class="activity-bar-outer">
                <div class="activity-bar-inner" style="height: {height_pct}%; background: {bar_color};"></div>
            </div>
            <div class="activity-val">{mins}m</div>
            <div class="activity-sub">{qs} Qs</div>
        </div>
        """
        
    cards_html += "</div>"
    st.markdown(cards_html, unsafe_allow_html=True)

def render_dashboard(user: Dict[str, Any]):
    """Renders the Mastery & Analytics Dashboard tab."""
    st.markdown("## 📊 Study Progress & Spaced Repetition Analytics")
    st.caption("Track your daily study streaks, topic mastery levels, and upcoming reviews.")

    # 1. Summary Cards
    summary = get_study_summary(user["id"])
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric(
            label="🔥 Active Daily Streak",
            value=f"{summary['streak_days']} Day(s)",
            help="Consecutive days with recorded study logs."
        )
    with c2:
        st.metric(
            label="❓ Total Questions Solved",
            value=f"{summary['total_questions']}",
            help="Total MCQs and challenge questions answered."
        )
    with c3:
        st.metric(
            label="🎯 Overall Accuracy",
            value=f"{summary['avg_accuracy']}%",
            help="Average score across all completed quizzes."
        )
    with c4:
        st.metric(
            label="⏱️ Total Study Time",
            value=f"{summary['total_minutes']} mins",
            help="Estimated active minutes spent in Study Room & Quizzes."
        )

    st.divider()

    # 2. Daily Activity Chart
    st.subheader("📈 14-Day Study Activity")
    daily_logs = get_daily_study_logs(user["id"], days=14)
    if daily_logs:
        render_activity_visual(daily_logs)
    else:
        st.info("Start reading chapters and taking quizzes to view your daily activity trend!")

    st.divider()

    # 3. Two-column layout: Due for Review Queue & Topic Mastery
    col_due, col_mastery = st.columns([1.0, 1.2], gap="medium")

    # ================= LEFT: DUE FOR SPACED REPETITION REVIEW =================
    with col_due:
        st.subheader("⏰ Due for Spaced Review")
        st.caption("Topics scheduled by the SM-2 algorithm for memory reinforcement.")

        due_topics = get_due_reviews(user["id"])
        if due_topics:
            for item in due_topics:
                with st.container(border=True):
                    st.markdown(f"**{item['topic_name']}**")
                    c_m1, c_m2 = st.columns(2)
                    with c_m1:
                        st.caption(f"Mastery: **{item['mastery_percentage']}%**")
                    with c_m2:
                        st.caption(f"Interval: **{item['interval_days']} day(s)**")
                    
                    if st.button(f"🎯 Practice Now", key=f"btn_due_{item['id']}", use_container_width=True):
                        st.session_state.quiz_topic = item["topic_name"]
                        st.session_state.active_tab_index = 1
                        st.info(f"Selected '{item['topic_name']}'. Head over to the Quiz Arena tab to start!")
        else:
            st.success("🎉 You're all caught up! No topics are overdue for review today.")

    # ================= RIGHT: TOPIC MASTERY BREAKDOWN =================
    with col_mastery:
        st.subheader("🧠 Topic Mastery Breakdown")
        st.caption("Categorized by performance and review intervals.")

        mastery_list = get_topic_mastery(user["id"])
        if mastery_list:
            df_m = pd.DataFrame(mastery_list)
            
            # Map status
            def get_category(pct):
                if pct >= 80:
                    return "🟢 Mastered"
                elif pct >= 50:
                    return "🟡 In Progress"
                else:
                    return "🔴 Needs Review"
                    
            df_m["Status"] = df_m["mastery_percentage"].apply(get_category)
            
            # Display metrics summary
            mastered_cnt = (df_m["mastery_percentage"] >= 80).sum()
            in_prog_cnt = ((df_m["mastery_percentage"] >= 50) & (df_m["mastery_percentage"] < 80)).sum()
            needs_rev_cnt = (df_m["mastery_percentage"] < 50).sum()

            s1, s2, s3 = st.columns(3)
            s1.metric("🟢 Mastered", mastered_cnt)
            s2.metric("🟡 In Progress", in_prog_cnt)
            s3.metric("🔴 Needs Review", needs_rev_cnt)

            display_cols = ["topic_name", "mastery_percentage", "attempts", "Status", "next_review"]
            df_display = df_m[display_cols].rename(columns={
                "topic_name": "Topic",
                "mastery_percentage": "Mastery %",
                "attempts": "Attempts",
                "next_review": "Next Review"
            })
            render_styled_table(df_display)
        else:
            st.info("No topic mastery records yet. Complete a quiz in the Quiz Arena to track your mastery!")

    st.divider()

    # 4. Recent Quiz Log
    st.subheader("📜 Recent Quiz History")
    results = get_user_quiz_results(user["id"], limit=10)
    if results:
        df_res = pd.DataFrame(results)
        df_res["Accuracy %"] = (df_res["score"] / df_res["total_questions"] * 100).round(1).astype(str) + "%"
        df_res_display = df_res[["timestamp", "subject", "chapter", "score", "total_questions", "Accuracy %"]].rename(columns={
            "timestamp": "Date & Time",
            "subject": "Subject",
            "chapter": "Chapter / Topic",
            "score": "Score",
            "total_questions": "Total Qs"
        })
        render_styled_table(df_res_display)
    else:
        st.caption("No quizzes completed yet.")
