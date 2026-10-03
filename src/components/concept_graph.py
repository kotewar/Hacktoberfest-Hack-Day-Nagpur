import re
import streamlit as st
from typing import Dict, Any, List

from config import BOOKS_DIR
from src.rag_engine import rag_engine, extract_text_from_pdf
from src.llm_client import (
    generate_concept_graph,
    explain_concept_node,
    explain_cs_ai_concept_visually,
    query_ollama
)
from src.database import log_study_activity

def render_content_with_diagrams(raw_text: str):
    """
    Renders markdown text and extracts any embedded Mermaid diagrams into clean visual containers.
    """
    mermaid_blocks = re.findall(r"```mermaid\s*(.*?)```", raw_text, re.DOTALL)
    
    if mermaid_blocks:
        parts = re.split(r"```mermaid\s*.*?```", raw_text, flags=re.DOTALL)
        for i, part in enumerate(parts):
            if part.strip():
                st.markdown(part.strip())
            if i < len(mermaid_blocks):
                with st.container(border=True):
                    st.caption("📊 **Interactive Visual Architecture / Workflow Diagram**")
                    st.markdown(f"```mermaid\n{mermaid_blocks[i].strip()}\n```")
    else:
        st.markdown(raw_text)

def render_cs_ai_visual_explainer(user: Dict[str, Any]):
    """
    Dedicated visual, mathematical, and algorithmic explainer for Computer Science
    and Artificial Intelligence university & college students.
    """
    st.markdown("### 💻 Computer Science & AI Visual Explainer")
    st.caption("Master complex algorithms, neural networks, and systems architectures with visual flowcharts, step-by-step code, and interview traps.")

    # State
    if "cs_ai_active_topic" not in st.session_state:
        st.session_state.cs_ai_active_topic = ""
    if "cs_ai_explanation" not in st.session_state:
        st.session_state.cs_ai_explanation = ""

    # Quick launch presets for popular college topics
    st.markdown("##### 🚀 Popular High-Yield College Topics:")
    preset_cols = st.columns(5)
    presets = [
        ("🤖 Attention in Transformers", "Self-Attention Mechanism in Transformers"),
        ("🧠 Neural Backprop & Gradient", "Backpropagation and Gradient Descent"),
        ("🌲 Binary Search Trees", "Binary Search Trees and Traversals"),
        ("⚡ Dynamic Programming", "Dynamic Programming: Memoization vs Tabulation"),
        ("🔄 Dijkstra Shortest Path", "Dijkstra's Algorithm and Graph Search")
    ]

    for idx, (label, query) in enumerate(presets):
        with preset_cols[idx]:
            if st.button(label, key=f"cs_preset_{idx}", use_container_width=True):
                st.session_state.cs_ai_active_topic = query
                with st.spinner(f"Gemma is generating visual architecture and code trace for '{query}'..."):
                    context = rag_engine.retrieve_context(query, subject="Artificial Intelligence", top_k=3)
                    if not context:
                        context = rag_engine.retrieve_context(query, subject="Computer Science", top_k=3)
                    explanation = explain_cs_ai_concept_visually(query, topic_context=context)
                    st.session_state.cs_ai_explanation = explanation
                    log_study_activity(user["id"], minutes_spent=4, questions_answered=0)
                    st.rerun()

    st.markdown("---")

    # Custom Topic Input Box
    c_in, c_act = st.columns([3.0, 1.0])
    with c_in:
        custom_input = st.text_input(
            "Or search any CS / AI topic to visualize:",
            value=st.session_state.cs_ai_active_topic,
            placeholder="e.g. Convolutional Neural Networks, QuickSort Partitioning, Paging & Virtual Memory...",
            key="cs_topic_custom_input"
        )
    with c_act:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        generate_btn = st.button("🔍 Explain Visually", type="primary", use_container_width=True)

    if generate_btn and custom_input.strip():
        target = custom_input.strip()
        st.session_state.cs_ai_active_topic = target
        with st.spinner(f"Gemma is crafting visual diagrams, code, and complexity analysis for '{target}'..."):
            context = rag_engine.retrieve_context(target, top_k=3)
            explanation = explain_cs_ai_concept_visually(target, topic_context=context)
            st.session_state.cs_ai_explanation = explanation
            log_study_activity(user["id"], minutes_spent=4, questions_answered=0)
            st.rerun()

    # Display Explanation Panel
    if st.session_state.cs_ai_explanation:
        st.divider()
        st.markdown(f"## 🎯 Visual Deep-Dive: `{st.session_state.cs_ai_active_topic}`")
        
        with st.container(border=True):
            render_content_with_diagrams(st.session_state.cs_ai_explanation)

        # Interactive Follow-up Doubt Clearing
        st.markdown("#### 💬 Ask a Follow-up Question on this Algorithm / Architecture:")
        c_q, c_q_btn = st.columns([3.2, 0.8])
        with c_q:
            followup_q = st.text_input(
                "Your doubt / code question:",
                placeholder="e.g. Can you trace this with an array [4, 2, 7, 1]? or How is Q, K, V initialized?",
                key="cs_followup_input"
            )
        with c_q_btn:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            ask_btn = st.button("Ask Gemma", key="cs_ask_followup_btn", use_container_width=True)

        if ask_btn and followup_q.strip():
            with st.spinner("Gemma is explaining your doubt..."):
                prompt = (
                    f"Context: {st.session_state.cs_ai_active_topic}\n"
                    f"Student Doubt: {followup_q}\n\n"
                    "Provide a crisp, clear answer with short code or calculation if necessary. Keep it encouraging."
                )
                answer = query_ollama(prompt)
                st.info(f"**💡 Gemma's Response:**\n\n{answer}")
                log_study_activity(user["id"], minutes_spent=2, questions_answered=0)

    else:
        st.info("👆 Click any preset above or enter a Computer Science / AI concept to see its visual architecture, code trace, and complexity analysis!")

def render_concept_graph(user: Dict[str, Any]):
    """
    Renders the Interactive Visual Concept Graph & Mind Map Explorer tab.
    Offers two complementary modes:
    1. CS & AI Visual Explainer (Architecture, Code Traces, Complexity)
    2. Curriculum Knowledge Trees (Multi-node Mind Maps from chapters)
    """
    st.markdown("## 🗺️ Visual Concept Graph & AI Explainer")
    st.caption("Transform dense science, engineering, and AI topics into intuitive visual diagrams and step-by-step mental models.")

    tab_cs, tab_mindmap = st.tabs([
        "💻 CS & AI Visual Explainer",
        "🌲 Curriculum Knowledge Trees"
    ])

    with tab_cs:
        render_cs_ai_visual_explainer(user)

    with tab_mindmap:
        render_curriculum_knowledge_trees(user)

def render_curriculum_knowledge_trees(user: Dict[str, Any]):
    """Renders the syllabus chapter mind map tree generator."""
    if "active_mindmap" not in st.session_state:
        st.session_state.active_mindmap = None
    if "selected_node_info" not in st.session_state:
        st.session_state.selected_node_info = None
    if "node_explanation" not in st.session_state:
        st.session_state.node_explanation = ""
    if "mindmap_topic_title" not in st.session_state:
        st.session_state.mindmap_topic_title = ""

    # Top Control Bar: Topic Selection or Custom Prompt
    c_source, c_btn = st.columns([2.5, 1.0], gap="medium")
    
    available_chapters = rag_engine.get_available_books_and_chapters()
    chapter_options = [f"[{c['subject']}] {c['chapter']}" for c in available_chapters] + ["✨ Custom Topic / Concept..."]

    with c_source:
        chosen_option = st.selectbox(
            "Select Chapter or Topic to Map:",
            options=chapter_options,
            key="mindmap_select_input"
        )
        if chosen_option == "✨ Custom Topic / Concept...":
            custom_topic = st.text_input(
                "Enter any topic (e.g., Photosynthesis, Newton's Third Law, Graph Traversal):",
                value="Artificial Intelligence - Neural Networks and Transformers",
                placeholder="Type topic..."
            )
            target_topic = custom_topic.strip()
            subject_filter = "General"
        else:
            matching = [c for c in available_chapters if f"[{c['subject']}] {c['chapter']}" == chosen_option]
            if matching:
                target_topic = matching[0]["chapter"]
                subject_filter = matching[0]["subject"]
            else:
                target_topic = chosen_option
                subject_filter = "General"

    with c_btn:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        generate_clicked = st.button("⚡ Generate Mind Map", type="primary", use_container_width=True)

    if generate_clicked:
        with st.spinner(f"Gemma is analyzing '{target_topic}' and synthesizing a visual concept graph..."):
            context = rag_engine.retrieve_context(target_topic, subject=subject_filter, top_k=3)
            if not context:
                for f in BOOKS_DIR.glob("*"):
                    if target_topic.lower() in f.stem.lower():
                        context = extract_text_from_pdf(f) if f.suffix == ".pdf" else f.read_text(encoding="utf-8", errors="ignore")
                        break
            
            payload = f"{target_topic}\n\nContext:\n{context[:1200]}" if context else target_topic
            graph_data = generate_concept_graph(payload)

            st.session_state.active_mindmap = graph_data
            st.session_state.mindmap_topic_title = target_topic
            st.session_state.selected_node_info = None
            st.session_state.node_explanation = ""
            
            log_study_activity(user["id"], minutes_spent=3, questions_answered=0)
            st.rerun()

    if not st.session_state.active_mindmap:
        st.info("👆 Select a chapter above and click **Generate Mind Map** to visualize concept relationships!")
        return

    graph = st.session_state.active_mindmap
    root = graph.get("root", {})
    nodes = graph.get("nodes", [])

    st.divider()

    col_diagram, col_details = st.columns([1.2, 1.0], gap="large")
    node_labels = [n.get("label", f"Concept {i+1}") for i, n in enumerate(nodes)]

    # Left Column: Mind Map
    with col_diagram:
        st.markdown(f"### 🌲 Knowledge Tree: {root.get('label', st.session_state.mindmap_topic_title)}")
        if root.get("desc"):
            st.caption(f"**Core Theme:** {root.get('desc')}")

        mermaid_code = graph.get("mermaid", "")
        if mermaid_code:
            with st.container(border=True):
                st.markdown(f"```mermaid\n{mermaid_code}\n```")

        st.markdown("#### 🔍 Concept Nodes in this Mind Map:")
        for idx, node in enumerate(nodes):
            node_label = node.get("label", f"Concept {idx+1}")
            node_desc = node.get("desc", "")
            importance = node.get("importance", "Medium")
            badge_color = "#3B82F6" if importance == "High" else "#10B981"
            
            with st.container(border=True):
                c_lbl, c_action = st.columns([2.0, 1.0])
                with c_lbl:
                    st.markdown(f"**{node_label}** <span style='background-color:{badge_color}20; color:{badge_color}; padding:2px 8px; border-radius:12px; font-size:0.75rem; font-weight:600;'>{importance} Priority</span>", unsafe_allow_html=True)
                    if node_desc:
                        st.caption(node_desc)
                with c_action:
                    if st.button("💡 Explain Concept", key=f"tree_node_btn_{idx}", use_container_width=True):
                        st.session_state.active_selected_label = node_label
                        st.session_state.selected_node_info = node
                        st.session_state.needs_node_fetch = True
                        st.rerun()

    # Right Column: Deep Dive
    with col_details:
        st.subheader("💡 Concept Spotlight & Explanations")

        selected_from_dropdown = st.selectbox(
            "Select Concept to Inspect:",
            options=node_labels,
            index=node_labels.index(st.session_state.get("active_selected_label")) if st.session_state.get("active_selected_label") in node_labels else 0,
            key="tree_node_dropdown_select"
        )

        if st.session_state.get("active_selected_label") != selected_from_dropdown or st.session_state.get("needs_node_fetch", False):
            st.session_state.active_selected_label = selected_from_dropdown
            st.session_state.needs_node_fetch = False
            matching_nodes = [n for n in nodes if n.get("label") == selected_from_dropdown]
            st.session_state.selected_node_info = matching_nodes[0] if matching_nodes else nodes[0]
            
            with st.spinner(f"Gemma is breaking down '{selected_from_dropdown}'..."):
                context_chunk = rag_engine.retrieve_context(selected_from_dropdown, top_k=2)
                exp = explain_concept_node(
                    concept_name=selected_from_dropdown,
                    topic_context=context_chunk or st.session_state.mindmap_topic_title
                )
                st.session_state.node_explanation = exp
                log_study_activity(user["id"], minutes_spent=3, questions_answered=0)
                st.rerun()

        active_node = st.session_state.selected_node_info
        if active_node and st.session_state.node_explanation:
            st.markdown(f"### 🎯 Deep Dive: **{active_node.get('label')}**")
            with st.container(border=True):
                st.markdown(st.session_state.node_explanation)
        else:
            with st.container(border=True):
                st.markdown("""
                ### 👈 Choose Any Node on the Left
                Click **"💡 Explain Concept"** or select from the dropdown above to reveal:
                - 🌟 **The Big Picture Intuition**
                - ⚙️ **Underlying Scientific Mechanism & Formula**
                - 🇮🇳 **Real-World Indian Village / Home Analogy**
                - ⚠️ **Watch Out: Common Exam Traps**
                - 🎯 **1-Minute Quick Brain Check**
                """)


