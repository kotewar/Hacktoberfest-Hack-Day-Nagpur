---
marp: true
theme: default
paginate: true
header: "EduGemma • Hacktoberfest Hack Day Nagpur x GDGC Nagpur"
footer: "100% Offline AI Study Buddy powered by Google Gemma 2"
style: |
  section {
    background-color: #F8FAFC;
    color: #1E293B;
    font-family: 'Segoe UI', system-ui, sans-serif;
  }
  h1 { color: #1E3A8A; font-weight: 800; }
  h2 { color: #2563EB; font-weight: 700; }
  .highlight { color: #059669; font-weight: bold; }
  .badge { background: #ECFDF5; color: #065F46; padding: 4px 12px; border-radius: 9999px; font-size: 0.75rem; border: 1px solid #A7F3D0; }
  .card { background: white; border: 1px solid #E2E8F0; border-radius: 12px; padding: 16px; margin: 8px 0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
---

# 🎓 EduGemma
### 100% Offline Socratic Study Buddy & AI Learning Cockpit

**Built for Students with Low or Zero Internet Connectivity**  
*Hacktoberfest Hack Day Nagpur x GDGC Nagpur*

<span class="badge">✈️ 100% Airplane Mode Verified</span>
<span class="badge">🧠 Powered by Google Gemma 2:2B</span>
<span class="badge">⚡ Zero-Latency On-Device RAG</span>

---

## 🌍 The Problem: The Education Connectivity Divide

* **Unreliable / Expensive Internet:** Millions of students in rural & tier-2/3 regions (e.g. Vidarbha) face frequent power/network outages and high mobile data costs.
* **Passive Rote Memorization:** Textbook reading without interactive guidance leads to poor concept retention and exam anxiety.
* **Lack of 24/7 Personalized Tutoring:** High teacher-to-student ratios mean students cannot get doubts clarified at home.
* **Cloud AI Failure:** Cloud LLMs fail completely when the internet disconnects.

---

## 💡 The Solution: EduGemma

An **on-device, zero-internet personal AI tutor** that turns any standard laptop or school desktop into an elite Socratic study workstation.

* ✈️ **100% Offline:** LLM inference, vector embeddings, textbook search, and database run locally on `localhost`.
* ⚡ **Ultra Compute Efficient:** Runs `gemma2:2b` (4-bit Q4 quantization) under **2.1 GB RAM footprint** on plain CPUs.
* 🧠 **Socratic Learning Loop:** Guides students step-by-step with probing questions and relatable analogies instead of spoon-feeding.
* 🔁 **SM-2 Spaced Repetition:** Calculates scientifically optimal review schedules so students retain formulas and theorems forever.

---

## 🏛️ System Architecture

```mermaid
graph LR
    classDef client fill:#EFF6FF,stroke:#3B82F6,stroke-width:2px;
    classDef engine fill:#EEF2FF,stroke:#6366F1,stroke-width:2px;
    classDef store fill:#ECFDF5,stroke:#10B981,stroke-width:2px;

    UI["💻 Unified Streamlit Cockpit"]:::client
    RAG["📚 Hybrid Vector RAG Engine"]:::engine
    LLM["🧠 Ollama (Gemma 2:2B Q4 CPU)"]:::engine
    DB["💾 SQLite (edugemma.db + SM-2)"]:::store

    UI -->|"Topic Select / Query"| RAG
    RAG -->|"Grounded Context"| LLM
    LLM -->|"Streaming Thoughts + Socratic Hints"| UI
    UI -->|"Instant Quiz Results"| DB
    DB -->|"Streak & Mastery Updates"| UI
```

---

## 🌟 4 Core Superpowers of EduGemma

1. **📖 Unified Knowledge Canvas:**
   * One-click chapter reader for Science, Physics, Biology, and College CS/AI.
   * Instant shortcuts: **"Explain Simply"**, **"Hindi / Village Analogy"**, and **"Key Formulas"**.
2. **🗺️ Visual Mind Maps & CS/AI Architecture Traces:**
   * Generates interactive Mermaid dataflow graphs and dependency trees.
   * College deep-dives on Transformers, Backprop, BSTs, Dynamic Programming, and Dijkstra.
3. **🤖 Socratic Tutor with Visible Chain-of-Thought:**
   * Gemma reveals its internal pedagogical reasoning before answering!
4. **🎯 Active Recall & SuperMemo-2 Spaced Repetition:**
   * Generates 3-question MCQs + subjective evaluator; auto-schedules next review.

---

## 🎬 Live Demo Walkthrough (5 Key Moments)

* **Moment 1: Airplane Mode Verification**  
  * Show browser working with zero internet on `localhost:8501`.
* **Moment 2: Global Topic Command Bar**  
  * Select *"Artificial Intelligence - Neural Networks and Transformers"* $\rightarrow$ Canvas, co-pilot, and quiz update simultaneously.
* **Moment 3: Visual CS/AI Explainer**  
  * Click *"Attention in Transformers"* $\rightarrow$ Visual Mermaid projection pipeline + Python code trace.
* **Moment 4: Gemma's Inner Thinking**  
  * Ask *"Why is ReLU preferred over Sigmoid?"* $\rightarrow$ Expand Gemma's pedagogical thought process.
* **Moment 5: Active Recall & Mastery Update**  
  * Take a 3-question test $\rightarrow$ Watch topic mastery percentage & study streak update live!

---

## 📊 Impact & Future Roadmap

* **Zero-Cost Scaling:** Can be pre-installed on low-cost government school tablets or community center PCs.
* **Multilingual Expansion:** Native Marathi and Hindi dialect voice synthesis via Web Speech API.
* **P2P "Sneakernet" Sync:** Offline QR-code sync between classmates to compare quiz scores and share custom flashcards.
* **Standardized Exam Packs:** Expand syllabus banks for JEE, NEET, CBSE Class 10/12, and GATE CS.

---

# 🚀 Thank You!

### **EduGemma: Empowering Every Student, Anywhere, Offline.**

* **Team:** Hacktoberfest Hack Day Nagpur x GDGC Nagpur
* **Repository:** `github.com/kotewar/Hacktoberfest-Hack-Day-Nagpur`
* **Model:** Google Gemma 2 (2B Parameters, Quantized CPU Localhost)

**Questions & Demo Feedback Welcome!**
