Here is a comprehensive, production-ready specification document formatted specifically for an autonomous coding agent (such as Copilot CLI in agentic mode, Aider, or Claude Code) to build the application end-to-end.

---

# Project Specification: Offline Gemma Study Buddy (`EduGemma`)

## 1. Project Overview & Principles

`EduGemma` is a 100% offline, local-first web application designed for students in low-connectivity areas. It provides an interactive textbook reader, a Socratic AI study co-pilot, an automated quiz generator with subjective grading, and an offline analytics dashboard.

### Core Non-Negotiables:

* **Zero Internet Requirement:** The system must function completely in Airplane Mode. All embeddings, LLM inference, vector storage, and databases run locally on `localhost`.
* **Compute Efficiency:** Default inference target is `gemma2:2b` via Ollama (`http://localhost:11434`), running with 4-bit quantization (`Q4_K_M`) to run smoothly on standard laptop CPUs (under 4 GB RAM footprint).
* **Decoupled Architecture:** Analytics, user sessions, and score tracking must execute deterministically via SQLite without incurring LLM latency.

---

## 2. Recommended Tech Stack

* **Application Framework:** **Streamlit** (Python 3.10+) for instant local web UI and reactive data visualizations without node/npm build complexity.
* **LLM Serving:** **Ollama** running `gemma2:2b` (fallback: `llama.cpp` server).
* **RAG & Vector Search:** **ChromaDB** (embedded persistent mode) + **FastEmbed** (`BAAI/bge-small-en-v1.5` via ONNX runtime—lightweight, PyTorch-free).
* **Persistence & Tracking:** **SQLite** (`data/edugemma.db`).
* **Document Ingestion:** **PyPDF2** or **pdfplumber** for extracting syllabus PDFs (e.g., NCERT textbooks).

---

## 3. Repository File Structure

```text
edugemma/
├── app.py                     # Main entrypoint & Streamlit multi-tab router
├── config.py                  # App configuration, paths, and constants
├── requirements.txt           # Python dependencies
├── data/
│   ├── books/                 # Place raw textbook PDFs here
│   ├── vector_db/             # Persistent ChromaDB store
│   └── edugemma.db            # SQLite user, quiz, and analytics database
├── src/
│   ├── __init__.py
│   ├── database.py            # SQLite schema initialization and CRUD methods
│   ├── rag_engine.py          # Document chunking, indexing, and semantic retrieval
│   ├── llm_client.py          # Ollama client, structured prompts, and error handling
│   ├── sm2.py                 # Spaced repetition calculation engine
│   └── components/            # UI modules (Study Room, Quiz Arena, Analytics)
│       ├── __init__.py
│       ├── study_room.py
│       ├── quiz_arena.py
│       └── dashboard.py
└── scripts/
    └── ingest_books.py        # CLI script to parse PDFs into ChromaDB

```

---

## 4. Database Schema (`data/edugemma.db`)

The agent must create and initialize the following tables on startup:

```sql
-- Students / Profiles
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Subjective and Objective Quiz Records
CREATE TABLE IF NOT EXISTS quiz_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    subject TEXT,
    chapter TEXT,
    total_questions INTEGER,
    score REAL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

-- Topic Mastery Tracking
CREATE TABLE IF NOT EXISTS topic_mastery (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    topic_name TEXT,
    attempts INTEGER DEFAULT 0,
    mastery_percentage REAL DEFAULT 0.0,
    last_practiced TIMESTAMP,
    next_review TIMESTAMP,
    repetitions INTEGER DEFAULT 0,
    interval_days INTEGER DEFAULT 1,
    ease_factor REAL DEFAULT 2.5,
    FOREIGN KEY(user_id) REFERENCES users(id),
    UNIQUE(user_id, topic_name)
);

-- Daily Study Activity Streak
CREATE TABLE IF NOT EXISTS study_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    date DATE DEFAULT CURRENT_DATE,
    minutes_spent INTEGER DEFAULT 0,
    questions_answered INTEGER DEFAULT 0,
    FOREIGN KEY(user_id) REFERENCES users(id),
    UNIQUE(user_id, date)
);

```

---

## 5. Core Subsystem Specifications

### Subsystem A: Local RAG Pipeline (`src/rag_engine.py`)

1. **Document Loading & Chunking:**
* Scan `data/books/` for `.pdf` and `.txt` files.
* Recursive character splitter: `chunk_size=700`, `chunk_overlap=100`.


2. **Offline Embeddings:**
* Use `fastembed.TextEmbedding(model_name="BAAI/bge-small-en-v1.5")`.


3. **Retrieval Method:**
* Vector store persisted in `data/vector_db/`.
* Query method: `retrieve_context(query: str, subject: str = None, top_k: int = 3) -> str`.



### Subsystem B: Prompt Engineering & LLM Control (`src/llm_client.py`)

Must strictly format prompts for Gemma-2 instruction format (`<start_of_turn>user\n...<end_of_turn>\n<start_of_turn>model\n...<end_of_turn>`).

1. **Socratic Tutor Prompt:**
* *Goal:* Guide step-by-step without leaking direct answers.


```text
You are an encouraging, patient offline tutor for school students.
Context: {context}
Student Question: {query}
Instruction: Do not give the direct answer immediately. Guide the student with 1-2 probing, intuitive questions or simple everyday analogies based on the context. Keep explanations concise.

```


2. **Bilingual / Simplification Prompt:**
* *Goal:* Convert formal academic English into simple colloquial explanations (e.g., Hinglish / simple Hindi or everyday analogies).


```text
Explain the following passage in simple, everyday conversational language using a real-world home or village analogy.
Passage: {text}

```


3. **Structured Quiz Generator Prompt (Strict JSON Output):**
* *Constraint:* Output **only** valid, parseable JSON without Markdown fences or conversational preamble.


```text
Generate a {count}-question multiple-choice quiz based strictly on the text provided.
Return ONLY a raw JSON list with this schema:
[
  {
    "question": "string",
    "options": ["string", "string", "string", "string"],
    "correct_index": 0,
    "explanation": "string"
  }
]
Text: {text}

```


4. **Subjective Answer Evaluator Prompt:**
* Evaluates short-answer responses against ground truth facts.


```text
Question: {question}
Reference Facts: {reference_facts}
Student's Answer: {student_answer}
Evaluate the student's answer out of 5 marks. Point out what they understood correctly and highlight any key scientific terms they missed.

```



### Subsystem C: Spaced Repetition Logic (`src/sm2.py`)

Implement the SuperMemo-2 (SM-2) algorithm for `topic_mastery`:

* Given student rating $q \in [0, 5]$:

$$\text{EF}' = \max\left(1.3, \, \text{EF} + (0.1 - (5 - q) \times (0.08 + (5 - q) \times 0.02))\right)$$


* If $q < 3$: reset `repetitions = 0`, `interval_days = 1`.
* If $q \ge 3$:
* `repetitions == 0` $\rightarrow$ `interval_days = 1`
* `repetitions == 1` $\rightarrow$ `interval_days = 6`
* `repetitions > 1` $\rightarrow$ `interval_days = round(interval_days * EF')`


* Calculate and persist `next_review = now + interval_days`.

---

## 6. UI & User Experience Spec (`app.py` & `src/components/`)

Use a persistent sidebar with:

* **Active User Profile Selector** (creates/switches profiles instantly).
* **Ollama Status Indicator** (checks `GET http://localhost:11434/api/tags` and displays a green dot if reachable).
* **Navigation Tabs:**

### Tab 1: "Study Room"

* **Left Column (Textbook View):** Dropdown to select Book $\rightarrow$ Chapter. Displays chapter content. Includes a text selection / paste box.
* **Action Buttons:** `Explain Simply`, `Hindi / Local Analogy`, `Summarize Key Formulas`.
* **Right Column (Chat Co-Pilot):** Chat history stream connected to Socratic Gemma with a toggle switch: `[Socratic Mode: ON/OFF]`.

### Tab 2: "Quiz Arena"

* Select topic or click `Generate Quiz from Active Chapter`.
* Renders MCQs with radio buttons.
* On `Submit Quiz`:
* Instant deterministic grading.
* Explanation reveal for each question.
* Persists score into `quiz_results` and updates `topic_mastery`.


* Includes a **"Challenge Problem"** box for open-ended answers with AI evaluation feedback.

### Tab 3: "Mastery & Analytics"

* **Streak & Summary Cards:** Daily active streak (days), total questions solved, average accuracy percentage.
* **Topic Mastery Table / Bar Chart:** Categorized as **Mastered** (Green), **In Progress** (Yellow), or **Needs Review** (Red).
* **Due for Review Queue:** Shows topics whose `next_review` timestamp is $\le$ current date.

---

## 7. Phased Implementation Steps for Agent

The local agent must execute the build in the following ordered phases:

```text
Phase 1: Environment & Persistence
├── Step 1: Write requirements.txt (streamlit, ollama, fastembed, chromadb, pypdf2).
├── Step 2: Implement config.py and ensure directories (data/books, data/vector_db) auto-create.
└── Step 3: Implement src/database.py with SQLite schemas and helper functions.

Phase 2: RAG & Offline Inference
├── Step 4: Implement src/llm_client.py with Ollama wrapper, fallback handling, and JSON parsing.
├── Step 5: Implement src/rag_engine.py with PDF loading, chunking, and ChromaDB persistence.
└── Step 6: Create scripts/ingest_books.py to populate sample chapter data.

Phase 3: Logic & Spaced Repetition
├── Step 7: Implement src/sm2.py with the standard SM-2 algorithm.
└── Step 8: Wire up database update logic for quiz completions and mastery updates.

Phase 4: Streamlit UI
├── Step 9: Build src/components/study_room.py (split layout, RAG chat, prompt shortcuts).
├── Step 10: Build src/components/quiz_arena.py (JSON quiz rendering, scoring, AI evaluator).
├── Step 11: Build src/components/dashboard.py (metrics, charts, reviews).
└── Step 12: Wire everything into app.py and verify offline execution end-to-end.

```

---

## 8. Verification & Test Plan

1. **Air-Gap Verification:** Turn off Wi-Fi on the host machine. Run `streamlit run app.py` and verify all features load without network timeouts.
2. **JSON Resilience Test:** Test `quiz_arena.py` with malformed LLM responses to verify regex extraction fallback:
```python
# Fallback parser handles raw text wrapping JSON
json_match = re.search(r"\[.*\]", raw_response, re.DOTALL)

```


3. **DB Integrity Test:** Verify that answering a quiz correctly increments the student's mastery score and updates `study_logs` for today's date.
