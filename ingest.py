"""
PDF Ingestion Pipeline for BVRIT RAG Chatbot
==============================================
Loads the college PDF, extracts text and images, splits into chunks,
generates embeddings, and stores them in a persistent ChromaDB vector database.
"""

import os
import sys
import json
import fitz  # PyMuPDF
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

# Load environment variables
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
CHROMA_DB_DIR = os.getenv("CHROMA_DB_DIR", "./chroma_db")
PDF_PATH = os.getenv("PDF_PATH", "./data/BVRIT HYDERABAD Institutional Overview.pdf")
IMAGES_DIR = os.getenv("IMAGES_DIR", "./data/images")

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100


def extract_images_from_pdf(pdf_path: str, output_dir: str) -> dict:
    """
    Extract images from each page of the PDF and save them as PNG files.
    Returns a dict mapping page numbers (1-based) to lists of image file paths.
    """
    print(f"[INFO] Extracting images from PDF to: {output_dir}")
    os.makedirs(output_dir, exist_ok=True)

    doc = fitz.open(pdf_path)
    page_images = {}

    for page_num in range(doc.page_count):
        page = doc[page_num]
        images = page.get_images(full=True)
        page_image_list = []

        for img_idx, img in enumerate(images):
            xref = img[0]
            pix = fitz.Pixmap(doc, xref)

            # Convert to RGB if necessary (handle CMYK/grayscale)
            if pix.n > 4:
                pix = fitz.Pixmap(fitz.csRGB, pix)
            elif pix.n == 4:
                pix = fitz.Pixmap(fitz.csRGB, pix)

            # Save as PNG
            img_filename = f"page{page_num + 1}_img{img_idx + 1}.png"
            img_path = os.path.join(output_dir, img_filename)
            pix.save(img_path)
            page_image_list.append(img_path)
            print(f"  [INFO] Saved: {img_path} ({pix.width}x{pix.height})")

        if page_image_list:
            page_images[page_num + 1] = page_image_list

    doc.close()

    # Save image metadata to JSON
    metadata_path = os.path.join(output_dir, "image_metadata.json")
    with open(metadata_path, "w") as f:
        json.dump(page_images, f, indent=2)
    print(f"[INFO] Image metadata saved to: {metadata_path}")

    return page_images


def load_pdf(file_path: str):
    """Load PDF document using PyPDFLoader."""
    if not os.path.exists(file_path):
        print(f"[ERROR] PDF not found at: {file_path}")
        sys.exit(1)
    print(f"[INFO] Loading PDF from: {file_path}")
    loader = PyPDFLoader(file_path)
    documents = loader.load()
    print(f"[INFO] Loaded {len(documents)} page(s).")
    return documents


def split_documents(documents, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP):
    """Split documents into overlapping chunks."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ".", " ", ""],
        length_function=len,
    )
    chunks = splitter.split_documents(documents)
    print(f"[INFO] Created {len(chunks)} chunks from {len(documents)} document(s).")
    return chunks


def get_embeddings():
    """Get OpenAI-compatible embeddings via OpenRouter."""
    if not OPENROUTER_API_KEY or OPENROUTER_API_KEY == "your-openrouter-api-key-here":
        print("[ERROR] Please set a valid OPENROUTER_API_KEY in your .env file.")
        sys.exit(1)

    embeddings = OpenAIEmbeddings(
        openai_api_key=OPENROUTER_API_KEY,
        openai_api_base="https://openrouter.ai/api/v1",
        model=EMBEDDING_MODEL,
    )
    return embeddings


def create_vector_store(chunks, embeddings, persist_directory=CHROMA_DB_DIR):
    """Create and persist ChromaDB vector store from document chunks."""
    print(f"[INFO] Creating vector store and persisting to: {persist_directory}")
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_directory,
    )
    print(f"[INFO] Vector store created with {vector_store._collection.count()} vectors.")
    return vector_store


def main():
    """Main ingestion pipeline."""
    print("=" * 60)
    print("BVRIT RAG Chatbot - Document Ingestion Pipeline")
    print("=" * 60)

    # Step 1: Extract images from PDF
    page_images = extract_images_from_pdf(PDF_PATH, IMAGES_DIR)

    # Step 2: Load PDF text
    documents = load_pdf(PDF_PATH)

    # Step 3: Split into chunks
    chunks = split_documents(documents)

    # Step 4: Attach image references to chunk metadata
    for chunk in chunks:
        page_num = chunk.metadata.get("page", 0)
        # PyMuPDF uses 0-based, but we stored 1-based
        page_key = page_num + 1 if isinstance(page_num, int) else page_num
        if page_key in page_images:
            chunk.metadata["images"] = page_images[page_key]
        else:
            chunk.metadata["images"] = []

    # Step 5: Get embeddings
    embeddings = get_embeddings()

    # Step 6: Create and persist vector store
    create_vector_store(chunks, embeddings)

    print("[SUCCESS] Ingestion complete. Vector database is ready for queries.")
    print(f"[INFO] Images extracted: {sum(len(v) for v in page_images.values())} total across {len(page_images)} pages.")


if __name__ == "__main__":
    main()