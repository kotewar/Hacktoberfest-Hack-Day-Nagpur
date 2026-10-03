"""
CLI Script to parse and index textbook documents (.pdf, .txt, .md) into the persistent RAG vector store.
Run via: python scripts/ingest_books.py
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import BOOKS_DIR, VECTOR_DB_DIR
from src.rag_engine import rag_engine

def main():
    print("=" * 60)
    print("📚 EduGemma: Offline Textbook Ingestion & Vector Indexer")
    print("=" * 60)
    print(f"Books Directory:    {BOOKS_DIR}")
    print(f"Vector Store Directory: {VECTOR_DB_DIR}")

    files = list(BOOKS_DIR.glob("*"))
    valid_files = [f for f in files if f.suffix.lower() in [".pdf", ".txt", ".md"]]
    
    if not valid_files:
        print(f"No documents found in {BOOKS_DIR}. Please place .pdf or .txt textbooks there.")
        return

    print(f"\nFound {len(valid_files)} textbook file(s):")
    for f in valid_files:
        print(f"  • {f.name} ({round(f.stat().st_size / 1024, 1)} KB)")

    print("\nSplitting into chunks and indexing...")
    num_chunks = rag_engine.index_books(BOOKS_DIR)
    print(f"Successfully processed and indexed {num_chunks} chunks into local vector store!")

    print("\nIndexed Chapters:")
    for item in rag_engine.get_available_books_and_chapters():
        print(f"  - [{item['subject']}] {item['chapter']} (Source: {item['source']})")

    # Quick test retrieval
    test_query = "What is a combination reaction?"
    print(f"\nVerification Query: '{test_query}'")
    context = rag_engine.retrieve_context(test_query, top_k=2)
    print("Retrieved Sample:")
    print("-" * 40)
    print(context[:300] + "..." if len(context) > 300 else context)
    print("-" * 40)
    print("\nIngestion complete! Ready for offline study.")

if __name__ == "__main__":
    main()
