"""
Debug the complete RAG pipeline step by step.
Identifies exactly where the pipeline is failing.
"""
import os
import sys
import json
import time
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
CHROMA_DB_DIR = os.getenv("CHROMA_DB_DIR", "./chroma_db")
PDF_PATH = os.getenv("PDF_PATH", "./data/bvrit_college_info.pdf")

print("=" * 70)
print("RAG PIPELINE DEBUGGER")
print("=" * 70)

# ============================================================
# STEP 0: Environment Check
# ============================================================
print("\n[STEP 0] Environment Check")
print("-" * 40)
print(f"  OPENROUTER_API_KEY set: {bool(OPENROUTER_API_KEY)}")
print(f"  OPENROUTER_API_KEY length: {len(OPENROUTER_API_KEY) if OPENROUTER_API_KEY else 0}")
print(f"  EMBEDDING_MODEL: {EMBEDDING_MODEL}")
print(f"  CHROMA_DB_DIR: {CHROMA_DB_DIR}")
print(f"  PDF_PATH: {PDF_PATH}")
print(f"  PDF exists: {os.path.exists(PDF_PATH)}")
if os.path.exists(PDF_PATH):
    print(f"  PDF size: {os.path.getsize(PDF_PATH)} bytes")
print(f"  ChromaDB exists: {os.path.exists(os.path.join(CHROMA_DB_DIR, 'chroma.sqlite3'))}")

# ============================================================
# STEP 1: PDF Loading
# ============================================================
print("\n[STEP 1] PDF Loading")
print("-" * 40)
try:
    from langchain_community.document_loaders import PyPDFLoader
    loader = PyPDFLoader(PDF_PATH)
    docs = loader.load()
    print(f"  ✅ Loaded {len(docs)} pages")
    total_chars = sum(len(d.page_content) for d in docs)
    print(f"  Total characters: {total_chars}")
    for i, d in enumerate(docs[:5]):
        preview = d.page_content[:100].replace('\n', ' ').strip()
        print(f"  Page {i+1}: {len(d.page_content)} chars -> '{preview}...'")
except Exception as e:
    print(f"  ❌ FAILED: {e}")
    docs = []

# ============================================================
# STEP 2: Text Splitting
# ============================================================
print("\n[STEP 2] Text Splitting")
print("-" * 40)
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        separators=["\n\n", "\n", ".", " ", ""],
    )
    chunks = splitter.split_documents(docs)
    print(f"  ✅ Created {len(chunks)} chunks from {len(docs)} pages")
    for i, c in enumerate(chunks[:5]):
        preview = c.page_content[:80].replace('\n', ' ').strip()
        print(f"  Chunk {i+1} (page {c.metadata.get('page', '?')}): {len(c.page_content)} chars -> '{preview}...'")
except Exception as e:
    print(f"  ❌ FAILED: {e}")
    chunks = []

# ============================================================
# STEP 3: Embeddings
# ============================================================
print("\n[STEP 3] Embeddings Generation")
print("-" * 40)
try:
    from langchain_openai import OpenAIEmbeddings
    embeddings = OpenAIEmbeddings(
        openai_api_key=OPENROUTER_API_KEY,
        openai_api_base="https://openrouter.ai/api/v1",
        model=EMBEDDING_MODEL,
    )
    print(f"  ✅ Embeddings model created: {embeddings.model}")
    
    # Test single embedding
    t0 = time.time()
    test_embed = embeddings.embed_query("What departments does BVRIT offer?")
    t1 = time.time()
    print(f"  ✅ Test embedding generated: {len(test_embed)} dimensions in {t1-t0:.2f}s")
    print(f"  First 5 values: {test_embed[:5]}")
except Exception as e:
    print(f"  ❌ FAILED: {e}")
    embeddings = None

# ============================================================
# STEP 4: ChromaDB Ingestion
# ============================================================
print("\n[STEP 4] ChromaDB Ingestion")
print("-" * 40)
try:
    from langchain_chroma import Chroma
    
    # Check existing store
    if os.path.exists(os.path.join(CHROMA_DB_DIR, 'chroma.sqlite3')):
        try:
            existing_store = Chroma(
                persist_directory=CHROMA_DB_DIR,
                embedding_function=embeddings,
            )
            existing_count = existing_store._collection.count()
            print(f"  Existing ChromaDB has {existing_count} vectors")
        except Exception as e:
            print(f"  ⚠️ Could not read existing store: {e}")
            existing_count = 0
    else:
        existing_count = 0
        print(f"  No existing ChromaDB found")
    
    if existing_count == 0 and chunks and embeddings:
        print(f"  ⚠️ Store is empty! Running ingestion now...")
        t0 = time.time()
        vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=CHROMA_DB_DIR,
        )
        t1 = time.time()
        new_count = vector_store._collection.count()
        print(f"  ✅ Ingestion complete: {new_count} vectors stored in {t1-t0:.2f}s")
    elif existing_count > 0:
        print(f"  ✅ Store already has data, no ingestion needed")
    else:
        print(f"  ❌ Cannot ingest: no chunks or no embeddings")
except Exception as e:
    print(f"  ❌ FAILED: {e}")
    import traceback
    traceback.print_exc()

# ============================================================
# STEP 5: Retrieval Test
# ============================================================
print("\n[STEP 5] Retrieval Test")
print("-" * 40)
try:
    from langchain_chroma import Chroma
    vector_store = Chroma(
        persist_directory=CHROMA_DB_DIR,
        embedding_function=embeddings,
    )
    count = vector_store._collection.count()
    print(f"  Store has {count} vectors")
    
    if count > 0:
        retriever = vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 4},
        )
        
        test_queries = [
            "What departments does BVRIT offer?",
            "What is the fee for CSE?",
            "Tell me about placements",
            "Who is the principal?",
            "What is the admission process?",
        ]
        
        for q in test_queries:
            print(f"\n  Query: '{q}'")
            t0 = time.time()
            results = retriever.invoke(q)
            t1 = time.time()
            print(f"  Retrieved {len(results)} results in {t1-t0:.3f}s")
            for i, r in enumerate(results):
                preview = r.page_content[:100].replace('\n', ' ').strip()
                page = r.metadata.get('page', '?')
                source = r.metadata.get('source', 'unknown')
                print(f"  [{i+1}] Page {page} ({source}): '{preview}...'")
    else:
        print(f"  ❌ Cannot test retrieval: store is empty")
except Exception as e:
    print(f"  ❌ FAILED: {e}")
    import traceback
    traceback.print_exc()

# ============================================================
# STEP 6: Full Pipeline Test (tool_chatbot)
# ============================================================
print("\n[STEP 6] Full Pipeline Test (tool_chatbot)")
print("-" * 40)
try:
    from tool_chatbot import generate_tool_response
    
    test_queries = [
        "What departments does BVRIT offer?",
        "What is the annual fee for CSE?",
        "Who is the principal of BVRIT?",
    ]
    
    for q in test_queries:
        print(f"\n  Query: '{q}'")
        t0 = time.time()
        result = generate_tool_response(q, verbose=True)
        t1 = time.time()
        print(f"  Time: {t1-t0:.2f}s")
        print(f"  Routing: {result['routing']}")
        print(f"  Answer: {result['answer'][:200]}")
        print(f"  Citations: {len(result.get('citations', []))}")
except Exception as e:
    print(f"  ❌ FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("DEBUG COMPLETE")
print("=" * 70)