"""
RAG Chatbot Core Module for BVRIT FAQ Chatbot
==============================================
Handles vector store retrieval, LLM-based response generation,
citations, image display, and refusal for out-of-knowledge-base queries.
"""

import os
from dotenv import load_dotenv

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
CHROMA_DB_DIR = os.getenv("CHROMA_DB_DIR", "./chroma_db")

# Number of relevant chunks to retrieve
TOP_K = 4

# System prompt template
SYSTEM_PROMPT = """You are an intelligent college FAQ assistant for BVRIT HYDERABAD College of Engineering for Women. 
Your role is to provide accurate information based ONLY on the retrieved context from official college documents.

## Guidelines:
1. Answer only using the provided context. Do not use your pre-trained knowledge.
2. If the context does not contain enough information to answer the question, say:
   "I'm sorry, but I don't have enough information in my knowledge base to answer this question. Please contact the college administration for more details."
3. Always cite the source page number from the context when providing information.
4. Keep answers concise, clear, and helpful.
5. If asked about topics outside the college domain (e.g., unrelated general knowledge), politely refuse.
6. If the context mentions images are available for a topic (e.g., campus images, facilities), mention that relevant images are available below.

## Retrieved Context:
{context}
"""


def get_embeddings():
    """Get OpenAI-compatible embeddings via OpenRouter."""
    return OpenAIEmbeddings(
        openai_api_key=OPENROUTER_API_KEY,
        openai_api_base="https://openrouter.ai/api/v1",
        model=EMBEDDING_MODEL,
    )


def get_vector_store():
    """Load the persisted ChromaDB vector store."""
    embeddings = get_embeddings()
    vector_store = Chroma(
        persist_directory=CHROMA_DB_DIR,
        embedding_function=embeddings,
    )
    return vector_store


def get_llm():
    """Get the LLM via OpenRouter."""
    return ChatOpenAI(
        openai_api_key=OPENROUTER_API_KEY,
        openai_api_base="https://openrouter.ai/api/v1",
        model=LLM_MODEL,
        temperature=0.3,
        max_tokens=500,
    )


def retrieve_relevant_chunks(query: str, top_k: int = TOP_K):
    """Retrieve the most relevant document chunks for the query."""
    vector_store = get_vector_store()
    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": top_k},
    )
    docs = retriever.invoke(query)
    return docs


def format_context(docs) -> str:
    """Format retrieved documents into a context string for the LLM."""
    context_parts = []
    for i, doc in enumerate(docs, 1):
        page_num = doc.metadata.get("page", "N/A")
        source = doc.metadata.get("source", "College Document")
        content = doc.page_content.strip()
        # Add page number info for the LLM to know which page to reference
        context_parts.append(
            f"[Source {i}] (Page {page_num} from {source})\n{content}\n"
        )
    return "\n".join(context_parts)


def format_citations(docs) -> list:
    """Extract source citations and images from retrieved documents."""
    citations = []
    for i, doc in enumerate(docs, 1):
        page_num = doc.metadata.get("page", "N/A")
        content_preview = doc.page_content.strip()[:100]
        # Get images associated with this chunk's page
        images = doc.metadata.get("images", [])
        citations.append({
            "number": i,
            "page": page_num,
            "preview": content_preview,
            "images": images,
        })
    return citations


def collect_images_from_citations(citations) -> list:
    """Collect all unique image paths from citations."""
    seen = set()
    images = []
    for cit in citations:
        for img_path in cit.get("images", []):
            if img_path not in seen:
                seen.add(img_path)
                images.append(img_path)
    return images


def generate_response(query: str) -> dict:
    """
    Generate a response for the given query.
    Returns a dict with 'answer', 'citations', 'images', and 'has_answer'.
    """
    # Retrieve relevant chunks
    docs = retrieve_relevant_chunks(query)

    # Check if we have enough relevant content
    if not docs:
        return {
            "answer": "I'm sorry, but I don't have enough information in my knowledge base to answer this question. Please contact the college administration for more details.",
            "citations": [],
            "images": [],
            "has_answer": False,
        }

    # Format context
    context = format_context(docs)
    citations = format_citations(docs)

    # Collect unique images from all retrieved chunks
    images = collect_images_from_citations(citations)

    # If no images found in retrieved chunks, check ALL chunks for images
    # This ensures queries like "campus images" still return images even if
    # the text similarity doesn't match the image-only pages.
    if not images:
        import json, os
        metadata_path = os.path.join("data", "images", "image_metadata.json")
        if os.path.exists(metadata_path):
            with open(metadata_path) as f:
                all_page_images = json.load(f)
            # Check which pages the retrieved docs come from
            retrieved_pages = set()
            for d in docs:
                p = d.metadata.get("page")
                if isinstance(p, int):
                    retrieved_pages.add(str(p + 1))  # convert 0-indexed to 1-indexed
            # Add images from any page that was retrieved
            for page_key, imgs in all_page_images.items():
                if page_key in retrieved_pages:
                    for img in imgs:
                        if os.path.exists(img):
                            images.append(img)
            # If still no images, check if query is about visual topics
            if not images:
                visual_keywords = ["image", "images", "picture", "pictures", "photo", "photos",
                                   "campus", "facilities", "infrastructure", "building", "buildings",
                                   "look", "view", "gallery", "tour", "virtual"]
                query_lower = query.lower()
                is_visual_query = any(kw in query_lower for kw in visual_keywords)
                if is_visual_query:
                    # Add images from ALL pages that have them
                    for page_key, imgs in all_page_images.items():
                        for img in imgs:
                            if os.path.exists(img):
                                images.append(img)
                    if images:
                        # Add a note about these images being available
                        context += "\n\n[Note: Campus images are available from the college document.]"
                        for img in images:
                            context += f"\n[Image available: {os.path.basename(img)}]"
                        # Include in citations too
                        citations.append({
                            "number": len(citations) + 1,
                            "page": f"Page with campus images",
                            "preview": "Campus images from the college document",
                            "images": images,
                        })

    # Create the prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "Question: {query}\n\nPlease answer based on the provided context."),
    ])

    # Generate response
    llm = get_llm()
    messages = prompt.format_messages(context=context, query=query)
    response = llm.invoke(messages)
    answer = response.content.strip()

    return {
        "answer": answer,
        "citations": citations,
        "images": images,
        "has_answer": True,
        "context": context,
    }