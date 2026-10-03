import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
BOOKS_DIR = DATA_DIR / "books"
VECTOR_DB_DIR = DATA_DIR / "vector_db"
DB_PATH = DATA_DIR / "edugemma.db"

# Auto-create necessary directories
for directory in [DATA_DIR, BOOKS_DIR, VECTOR_DB_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Ollama / LLM Settings
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemma2:2b")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "180"))

# RAG & Embedding Settings
EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"
CHUNK_SIZE = 700
CHUNK_OVERLAP = 100
TOP_K_RETRIEVAL = 3

# UI Constants
APP_TITLE = "EduGemma: Offline Socratic Study Buddy"
APP_TAGLINE = "100% Offline AI Textbook Reader, Socratic Tutor & Spaced Repetition"
