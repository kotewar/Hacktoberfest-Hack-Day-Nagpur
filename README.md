# EduGemma: Offline Socratic Study Buddy 🎓✈️

> **Hacktoberfest Hack Day Nagpur x GDGC Nagpur Project**  
> *100% Offline, Local-First AI Study Buddy designed for students with low or zero internet connectivity.*

---

## 🌟 Overview & Key Principles

In many rural and semi-urban areas, students face frequent internet outages and high mobile data costs. **EduGemma** provides an enterprise-grade, 100% offline educational environment powered entirely on-device by **Gemma 2** (via Ollama), **SQLite**, and a **lightweight local RAG vector store**.

### Core Non-Negotiables:
- **✈️ Zero Internet Required (Airplane Mode):** LLM inference, embeddings, textbook vector search, and database analytics run entirely on `localhost`.
- **⚡ Compute Efficient:** Optimized for standard laptop CPUs (under 4 GB RAM footprint) targeting `gemma2:2b` 4-bit quantization.
- **🧠 Socratic Guidance:** Instead of spoon-feeding direct answers, Gemma guides students step-by-step with probing questions and real-world analogies (e.g. Indian village/kitchen analogies).
- **🔁 Spaced Repetition (SM-2):** Schedules review intervals based on student recall quality so students remember concepts for school and college exams.
- **📊 Real-time Analytics:** Deterministic tracking of study streaks, quiz accuracy, and topic mastery levels.

---

## 🏛️ System Architecture

```text
Hacktoberfest-Hack-Day-Nagpur/
├── app.py                     # Main Streamlit multi-tab router
├── config.py                  # App paths, model parameters, RAG settings
├── requirements.txt           # Python dependencies
├── data/
│   ├── books/                 # Raw textbook PDFs and TXT files
│   ├── vector_db/             # Persistent local vector store & index
│   └── edugemma.db            # SQLite user profiles, quiz results & study logs
├── src/
│   ├── database.py            # SQLite schema initialization and CRUD methods
│   ├── llm_client.py          # Ollama client with Gemma-2 turn templates & JSON parser
│   ├── rag_engine.py          # Document loader, chunker, and hybrid semantic retrieval
│   ├── sm2.py                 # SuperMemo-2 spaced repetition calculation engine
│   └── components/            # UI Modules
│       ├── study_room.py      # Split-screen reader, RAG co-pilot & analogies
│       ├── quiz_arena.py      # MCQ generator, instant grading & subjective evaluator
│       └── dashboard.py       # Streaks, topic mastery matrix & due reviews
├── scripts/
│   └── ingest_books.py        # CLI script to parse & index textbooks into vector DB
└── tests/
    └── test_edugemma.py       # Automated unit test suite
```

---

## 🚀 Quick Start (Running Offline)

### 1. Prerequisites
- **Python 3.10+**
- **Ollama** installed with `gemma2:2b`:
  ```bash
  ollama run gemma2:2b
  ```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Ingest Syllabus Textbooks (Optional)
Sample chapters for **Class 10 & 11 Science, Physics, and Biology** are already included in [data/books/](data/books/). You can drop additional `.pdf` or `.txt` textbooks into `data/books/` and run:
```bash
python scripts/ingest_books.py
```
*(You can also upload textbooks directly within the app UI!)*

### 4. Launch EduGemma Web App
```bash
streamlit run app.py
```
Open your browser at **`http://localhost:8501`**. You can safely turn off Wi-Fi or turn on Airplane Mode!

---

## 🧪 Running Tests
Run the automated test suite covering database operations, SM-2 math, JSON extraction, and RAG chunking:
```bash
python -m unittest tests/test_edugemma.py
```

---

## 💡 Key Features for Students

1. **📖 Interactive Study Room:**
   - Offline chapter selector with formatted reading pane.
   - One-click **"Explain Simply"**, **"Hindi / Village Analogy"**, and **"Summarize Key Formulas"**.
   - Socratic Chat Co-Pilot that guides students rather than giving away test solutions.

2. **🗺️ Visual Concept Graph & Interactive Mind Map:**
   - Auto-synthesizes visual knowledge graphs and Mermaid mind maps from dense textbook chapters or custom student queries.
   - 1-Click Concept Spotlights providing:
     - 💡 Big Picture Intuition in plain English
     - ⚙️ Underlying scientific mechanism & governing equations
     - 🇮🇳 Vivid Indian village/everyday home analogies (e.g. farming, kitchen, cricket)
     - ⚠️ Common Board Exam traps & misconceptions
     - 🎯 1-minute quick brain check to test recall
   - Interactive doubt-clearing box attached to each concept node.

3. **🎯 Quiz Arena & Subjective Evaluator:**
   - Dynamic multiple-choice questions generated on-the-fly from textbook chapters.
   - Instant deterministic grading with full explanations for every option.
   - **Open-Ended Challenge Problem** evaluator: grades student short answers out of 5 marks and highlights missing scientific terms.

4. **📊 Mastery & Analytics Dashboard:**
   - Active study streak counter (days).
   - Topic Mastery Breakdown: Categorized as 🟢 **Mastered**, 🟡 **In Progress**, or 🔴 **Needs Review**.
   - **Due for Review Queue**: Prioritizes topics needing recall based on the SM-2 algorithm.

