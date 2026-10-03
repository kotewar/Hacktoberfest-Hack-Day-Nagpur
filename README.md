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

## 🚀 End-to-End Setup Guide (Run on Any Local Machine)

Follow these steps to set up and run EduGemma on Windows, macOS, or Linux. Once step 4 is completed, **you can disconnect from the internet or enable Airplane Mode**—everything runs 100% locally.

---

### Prerequisites
1. **Python 3.10+** installed: [python.org/downloads](https://www.python.org/downloads/)
2. **Git** installed: [git-scm.com](https://git-scm.com/)
3. **Ollama** installed: [ollama.com/download](https://ollama.com/download)

---

### Step 1: Clone the Repository
```bash
git clone https://github.com/kotewar/Hacktoberfest-Hack-Day-Nagpur.git
cd Hacktoberfest-Hack-Day-Nagpur
```

---

### Step 2: Create & Activate a Virtual Environment

**On Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
*(If you see an execution policy error on PowerShell, run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` once).*

**On macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

---

### Step 4: Download the Local Gemma Model (One-Time Only)
Start Ollama and pull the lightweight 4-bit quantized Gemma 2 model:
```bash
ollama run gemma2:2b
```
*Once you see the `>>>` prompt, type `/bye` and press Enter to exit back to your terminal.*  
*(Optional higher-tier model: `ollama pull gemma4:e4b`)*.

---

### Step 5: Index Curriculum Textbooks
Ingest the included sample chapters (Biology, Physics, Chemistry, CS & AI) into the local vector index:
```bash
python scripts/ingest_books.py
```

---

### Step 6: Launch EduGemma Cockpit
```bash
streamlit run app.py
```
Open your browser at **http://localhost:8501**.

> ✈️ **Verify Airplane Mode:** Disconnect your Wi-Fi or turn on Airplane Mode. Every feature—textbook reader, Socratic Co-Pilot with thinking traces, visual mind maps, and quiz evaluations—continues to run smoothly with zero network access!

---

### Step 7: View Presentation & Architecture
- **Interactive Presentation Deck:** Open [presentation.html](presentation.html) in any web browser (`file:///.../presentation.html`).
- **Architecture Specification:** See [architecture.md](architecture.md) and [architecture.svg](architecture.svg).

---

## 🧹 Complete Teardown & Reset Guide

When you are done testing or want to completely remove the application and free up disk space:

### 1. Stop the Web Application
In the terminal running Streamlit, press:
```text
Ctrl + C
```

---

### 2. Stop the Ollama Service

**On Windows (PowerShell):**
```powershell
# Stop any background Ollama processes
Stop-Process -Name "*ollama*" -Force -ErrorAction SilentlyContinue
```
*(Or right-click the Ollama llama icon in the Windows taskbar tray and click **Quit Ollama**).*

**On macOS / Linux:**
```bash
pkill ollama
```

---

### 3. Deactivate the Virtual Environment
```bash
deactivate
```

---

### 4. (Optional) Reset Student Progress / Fresh Start
To clear quiz history, streaks, and reset student progress without deleting the code:

**On Windows:**
```powershell
Remove-Item -Path "data\edugemma.db" -Force -ErrorAction SilentlyContinue
python scripts\ingest_books.py
```

**On macOS / Linux:**
```bash
rm -f data/edugemma.db
python scripts/ingest_books.py
```

---

### 5. (Optional) Remove Downloaded Gemma Model
To reclaim disk space used by the local LLM (~1.6 GB):
```bash
ollama rm gemma2:2b
```

---

### 6. (Optional) Full Workspace Removal
To completely remove the project directory and virtual environment from your computer:

**On Windows (from parent folder):**
```powershell
cd ..
Remove-Item -Recurse -Force "Hacktoberfest-Hack-Day-Nagpur"
```

**On macOS / Linux (from parent folder):**
```bash
cd ..
rm -rf Hacktoberfest-Hack-Day-Nagpur
```

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

