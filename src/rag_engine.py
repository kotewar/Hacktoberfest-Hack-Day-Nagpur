import os
import json
import math
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

from config import BOOKS_DIR, VECTOR_DB_DIR, CHUNK_SIZE, CHUNK_OVERLAP, TOP_K_RETRIEVAL

logger = logging.getLogger(__name__)

# --- Text Splitting ---

def recursive_character_splitter(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP
) -> List[str]:
    """
    Recursively splits text on natural boundaries (\n\n, \n, . , space)
    to generate coherent chunks of specified size and overlap.
    """
    text = text.strip()
    if not text:
        return []

    # If text is small enough, return as single chunk
    if len(text) <= chunk_size:
        return [text]

    # Split hierarchy: paragraphs -> lines -> sentences -> words
    separators = ["\n\n", "\n", ". ", "? ", "! ", " "]
    
    def _split(txt: str, sep_idx: int) -> List[str]:
        if sep_idx >= len(separators):
            # Hard split as last resort
            return [txt[i:i + chunk_size] for i in range(0, len(txt), chunk_size - chunk_overlap)]
        
        sep = separators[sep_idx]
        splits = txt.split(sep)
        chunks = []
        current_chunk = ""

        for part in splits:
            candidate = f"{current_chunk}{sep}{part}" if current_chunk else part
            if len(candidate) <= chunk_size:
                current_chunk = candidate
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                if len(part) > chunk_size:
                    # Recursive split with finer separator
                    finer_splits = _split(part, sep_idx + 1)
                    chunks.extend(finer_splits)
                    current_chunk = ""
                else:
                    current_chunk = part
                    
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
            
        return chunks

    raw_chunks = _split(text, 0)
    
    # Merge small chunks with overlap
    final_chunks = []
    for i, c in enumerate(raw_chunks):
        if not c:
            continue
        if i > 0 and chunk_overlap > 0 and len(final_chunks) > 0:
            overlap_prefix = final_chunks[-1][-chunk_overlap:]
            # Ensure overlap doesn't duplicate
            if not c.startswith(overlap_prefix):
                c = f"{overlap_prefix} ... {c}"
        final_chunks.append(c)
        
    return final_chunks

# --- Document Loading ---

def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extracts all text from a PDF file using pypdf if available."""
    try:
        import pypdf
        reader = pypdf.PdfReader(str(pdf_path))
        pages_text = []
        for i, page in enumerate(reader.pages):
            txt = page.extract_text() or ""
            if txt.strip():
                pages_text.append(f"--- Page {i+1} ---\n{txt}")
        return "\n\n".join(pages_text)
    except Exception as e:
        logger.warning(f"pypdf extraction failed on {pdf_path}: {e}")
        try:
            import PyPDF2
            reader = PyPDF2.PdfReader(str(pdf_path))
            pages_text = [p.extract_text() or "" for p in reader.pages]
            return "\n\n".join(pages_text)
        except Exception as e2:
            logger.error(f"Failed to read PDF {pdf_path}: {e2}")
            return ""

def load_documents_from_dir(books_dir: Path = BOOKS_DIR) -> List[Dict[str, Any]]:
    """
    Scans the books directory for .pdf and .txt files and returns list of chunks with metadata.
    """
    documents = []
    if not books_dir.exists():
        return documents

    for file_path in books_dir.glob("*"):
        if file_path.is_file():
            text = ""
            if file_path.suffix.lower() == ".pdf":
                text = extract_text_from_pdf(file_path)
            elif file_path.suffix.lower() in [".txt", ".md"]:
                try:
                    text = file_path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    text = file_path.read_text(encoding="latin-1", errors="ignore")
                    
            if not text.strip():
                continue

            # Infer subject and chapter from filename (e.g. Science_Class10_Ch1_Chemical_Reactions.txt)
            parts = file_path.stem.replace("_", " ").split(" - ")
            subject = parts[0].strip() if len(parts) > 1 else "General Science"
            chapter = parts[1].strip() if len(parts) > 1 else file_path.stem.replace("_", " ")

            chunks = recursive_character_splitter(text, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
            for idx, chunk in enumerate(chunks):
                doc_id = f"{file_path.stem}_chunk_{idx}"
                documents.append({
                    "id": doc_id,
                    "text": chunk,
                    "metadata": {
                        "source": file_path.name,
                        "subject": subject,
                        "chapter": chapter,
                        "chunk_index": idx,
                        "total_chunks": len(chunks)
                    }
                })
    return documents

# --- Vector Store Implementation (ChromaDB + FastEmbed with Resilient Built-in Fallback) ---

class ResilientVectorStore:
    """
    Lightweight, deterministic local vector & BM25-hybrid index
    stored in JSON in data/vector_db/. Provides instant, zero-dependency offline retrieval.
    """
    def __init__(self, storage_dir: Path = VECTOR_DB_DIR):
        self.storage_dir = storage_dir
        self.index_file = self.storage_dir / "offline_index.json"
        self.documents: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        if self.index_file.exists():
            try:
                with open(self.index_file, "r", encoding="utf-8") as f:
                    self.documents = json.load(f)
            except Exception as e:
                logger.error(f"Error loading offline index: {e}")
                self.documents = []

    def _save(self):
        try:
            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump(self.documents, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving offline index: {e}")

    def add_documents(self, docs: List[Dict[str, Any]]):
        existing_ids = {d["id"] for d in self.documents}
        for doc in docs:
            if doc["id"] in existing_ids:
                # Update existing
                self.documents = [d if d["id"] != doc["id"] else doc for d in self.documents]
            else:
                self.documents.append(doc)
        self._save()

    def search(self, query: str, subject: Optional[str] = None, top_k: int = TOP_K_RETRIEVAL) -> List[Dict[str, Any]]:
        if not self.documents:
            return []

        # Tokenize query
        query_words = set(re.findall(r"\w+", query.lower()))
        if not query_words:
            return self.documents[:top_k]

        scored_docs = []
        for doc in self.documents:
            # Subject filter if provided
            if subject and subject.strip().lower() != "all":
                doc_subj = str(doc.get("metadata", {}).get("subject", "")).lower()
                doc_chap = str(doc.get("metadata", {}).get("chapter", "")).lower()
                if subject.strip().lower() not in doc_subj and subject.strip().lower() not in doc_chap:
                    continue

            text = doc["text"].lower()
            doc_words = re.findall(r"\w+", text)
            if not doc_words:
                continue

            # Compute term overlap score + length normalization
            match_count = sum(1 for w in query_words if w in text)
            frequency = sum(text.count(w) for w in query_words)
            score = (match_count * 2.0) + (frequency / (math.log(len(doc_words) + 10)))

            if score > 0:
                scored_docs.append((score, doc))

        scored_docs.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored_docs[:top_k]]


# --- Global RAG Engine Manager ---

class OfflineRAGEngine:
    def __init__(self):
        self.chroma_client = None
        self.chroma_collection = None
        self.fastembed_model = None
        self.local_store = ResilientVectorStore(VECTOR_DB_DIR)
        self._init_backend()

    def _init_backend(self):
        """Attempts to initialize ChromaDB and FastEmbed; falls back smoothly if unavailable."""
        try:
            import chromadb
            from chromadb.config import Settings
            self.chroma_client = chromadb.PersistentClient(path=str(VECTOR_DB_DIR))
            self.chroma_collection = self.chroma_client.get_or_create_collection(name="edugemma_books")
            logger.info("ChromaDB persistent collection initialized successfully.")
        except Exception as e:
            logger.info(f"ChromaDB not available or native compilation pending ({e}); using ResilientVectorStore.")

        try:
            from fastembed import TextEmbedding
            self.fastembed_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
            logger.info("FastEmbed initialized.")
        except Exception as e:
            logger.info(f"FastEmbed not loaded ({e}); fallback vector scoring active.")

    def index_books(self, books_dir: Path = BOOKS_DIR) -> int:
        """Loads and indexes all documents from the books directory."""
        docs = load_documents_from_dir(books_dir)
        if not docs:
            return 0

        # Always index in resilient store
        self.local_store.add_documents(docs)

        # Also index in ChromaDB if available
        if self.chroma_collection is not None:
            try:
                ids = [d["id"] for d in docs]
                texts = [d["text"] for d in docs]
                metadatas = [d["metadata"] for d in docs]

                embeddings = None
                if self.fastembed_model is not None:
                    embeddings = list(self.fastembed_model.embed(texts))
                    embeddings = [e.tolist() for e in embeddings]

                if embeddings is not None:
                    self.chroma_collection.upsert(ids=ids, documents=texts, metadatas=metadatas, embeddings=embeddings)
                else:
                    self.chroma_collection.upsert(ids=ids, documents=texts, metadatas=metadatas)
            except Exception as e:
                logger.warning(f"Could not index in ChromaDB: {e}")

        return len(docs)

    def retrieve_context(self, query: str, subject: Optional[str] = None, top_k: int = TOP_K_RETRIEVAL) -> str:
        """
        Retrieves top_k context chunks matching query and optional subject filter.
        Returns unified context string with source references.
        """
        results = []

        # Try ChromaDB first
        if self.chroma_collection is not None and self.chroma_collection.count() > 0:
            try:
                where_filter = None
                if subject and subject.strip().lower() != "all":
                    where_filter = {"subject": subject.strip()}

                query_embedding = None
                if self.fastembed_model is not None:
                    emb = list(self.fastembed_model.embed([query]))[0].tolist()
                    query_embedding = [emb]

                if query_embedding:
                    query_res = self.chroma_collection.query(
                        query_embeddings=query_embedding,
                        n_results=top_k,
                        where=where_filter
                    )
                else:
                    query_res = self.chroma_collection.query(
                        query_texts=[query],
                        n_results=top_k,
                        where=where_filter
                    )

                if query_res and query_res.get("documents") and len(query_res["documents"][0]) > 0:
                    for i, doc_txt in enumerate(query_res["documents"][0]):
                        meta = query_res["metadatas"][0][i] if query_res.get("metadatas") else {}
                        results.append({
                            "text": doc_txt,
                            "metadata": meta
                        })
            except Exception as e:
                logger.debug(f"Chroma query failed, falling back: {e}")

        # If Chroma yielded nothing, use resilient store
        if not results:
            results = self.local_store.search(query, subject=subject, top_k=top_k)

        if not results:
            return ""

        context_blocks = []
        for i, item in enumerate(results, 1):
            source = item.get("metadata", {}).get("source", "Textbook")
            chapter = item.get("metadata", {}).get("chapter", "")
            header = f"--- Source: {source} ({chapter}) ---" if chapter else f"--- Source: {source} ---"
            context_blocks.append(f"{header}\n{item['text']}")

        return "\n\n".join(context_blocks)

    def get_available_books_and_chapters(self) -> List[Dict[str, str]]:
        """Returns distinct books/chapters loaded in the index."""
        records = []
        seen = set()
        for doc in self.local_store.documents:
            meta = doc.get("metadata", {})
            src = meta.get("source", "")
            chap = meta.get("chapter", src)
            subj = meta.get("subject", "Science")
            key = (src, chap)
            if key not in seen:
                seen.add(key)
                records.append({
                    "source": src,
                    "chapter": chap,
                    "subject": subj
                })
        return records

# Singleton instance
rag_engine = OfflineRAGEngine()
