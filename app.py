import streamlit as st
import sys
from pathlib import Path

# Ensure root workspace directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import APP_TITLE, APP_TAGLINE, DEFAULT_MODEL
from src.database import init_db, get_all_users, get_or_create_user
from src.llm_client import check_ollama_status, get_ollama_latest_logs
from src.components.study_room import render_study_room
from src.components.concept_graph import render_concept_graph
from src.components.quiz_arena import render_quiz_arena
from src.components.dashboard import render_dashboard

# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="EduGemma - Offline AI Study Buddy",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database on first launch
init_db()

# Custom CSS for polished educational interface
st.markdown("""
<style>
    .main-header {
        font-size: 2.1rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.2rem;
    }
    .offline-badge {
        display: inline-block;
        background-color: #ECFDF5;
        color: #065F46;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        border: 1px solid #A7F3D0;
    }
    .status-pill-ok {
        color: #059669;
        font-weight: 600;
    }
    .status-pill-bad {
        color: #DC2626;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # --- Sidebar: User Profiles, Offline Mode & Ollama Health ---
    with st.sidebar:
        st.markdown("### 🎓 EduGemma")
        st.markdown("<span class='offline-badge'>✈️ 100% Offline / Airplane Mode</span>", unsafe_allow_html=True)
        st.caption("Zero-latency, private, on-device study assistant powered by Gemma.")
        st.divider()

        # 1. User Profile Selector / Creator
        st.markdown("#### 👤 Student Profile")
        users = get_all_users()
        user_names = [u["username"] for u in users]
        
        selected_username = st.selectbox(
            "Active Student:",
            options=user_names,
            index=0 if user_names else 0,
            key="active_user_select"
        )
        
        # New profile input
        with st.expander("➕ Switch / Create Student"):
            new_name = st.text_input("New Student Name:", placeholder="e.g. Priya, Aarav...")
            if st.button("Save Profile", use_container_width=True):
                if new_name.strip():
                    new_user = get_or_create_user(new_name)
                    st.success(f"Welcome, {new_name}!")
                    st.rerun()

        # Get active user record
        active_user = get_or_create_user(selected_username if selected_username else "Student")
        st.divider()

        # 2. Ollama Status & Model Details
        st.markdown("#### 🖥️ Local AI Inference")
        ollama_ok, models = check_ollama_status()
        
        if ollama_ok:
            st.markdown("● **Ollama Status:** <span class='status-pill-ok'>Connected (Localhost)</span>", unsafe_allow_html=True)
            if models:
                st.caption(f"Detected Models: `{', '.join(models)}`")
                # Choose active model
                default_idx = models.index(DEFAULT_MODEL) if DEFAULT_MODEL in models else 0
                chosen_model = st.selectbox("Active Gemma Model:", options=models, index=default_idx)
                st.session_state.selected_model = chosen_model
            else:
                st.caption("No models detected. Pull one with `ollama run gemma2:2b`.")

            # Live Ollama Terminal Logs Viewer
            with st.expander("📟 Live Ollama Terminal Logs & Speeds", expanded=False):
                st.caption("Recent raw engine output (tokens/sec, prompt eval, slots):")
                latest_logs = get_ollama_latest_logs(n_lines=15)
                st.code(latest_logs, language="text")
                if st.button("🔄 Refresh Logs", use_container_width=True):
                    st.rerun()
                st.caption("💡 **Tip to tail live in PowerShell:**\n`Get-Content $env:LOCALAPPDATA\\Ollama\\server.log -Wait -Tail 30`")

        else:
            st.markdown("● **Ollama Status:** <span class='status-pill-bad'>Disconnected</span>", unsafe_allow_html=True)
            st.warning("Start Ollama locally: `ollama run gemma2:2b`")

        st.divider()
        st.caption("EduGemma v1.0 • Built with Streamlit, Gemma-2, SQLite & ChromaDB")

    # --- Header ---
    c_head1, c_head2 = st.columns([3, 1])
    with c_head1:
        st.markdown(f"<div class='main-header'>📖 {APP_TITLE}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='sub-header'>{APP_TAGLINE}</div>", unsafe_allow_html=True)
    with c_head2:
        st.markdown(f"**Logged in as:** `{active_user['username']}`")

    # --- Main Navigation Tabs ---
    tab_study, tab_mindmap, tab_quiz, tab_dash = st.tabs([
        "📖 Study Room",
        "🗺️ Concept Mind Map",
        "🎯 Quiz Arena",
        "📊 Mastery & Analytics"
    ])

    with tab_study:
        render_study_room(active_user)

    with tab_mindmap:
        render_concept_graph(active_user)

    with tab_quiz:
        render_quiz_arena(active_user)

    with tab_dash:
        render_dashboard(active_user)

if __name__ == "__main__":
    main()
