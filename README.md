# 🎓 BVRIT College FAQ Assistant

> An AI-powered Retrieval-Augmented Generation (RAG) chatbot that answers college-related queries using official college documents with source citations and automated evaluation.

![License](https://img.shields.io/badge/License-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![LangChain](https://img.shields.io/badge/LangChain-RAG-green)
![ChromaDB](https://img.shields.io/badge/VectorDB-ChromaDB-orange)
![OpenRouter](https://img.shields.io/badge/LLM-OpenRouter-purple)

---

## 📖 Overview

The **BVRIT College FAQ Assistant** is an intelligent AI chatbot built using **Retrieval-Augmented Generation (RAG)**. Instead of relying solely on an LLM's pre-trained knowledge, the chatbot retrieves relevant information from official college documents and generates accurate, grounded responses with citations.

This project demonstrates a complete production-style RAG pipeline, including document ingestion, semantic search, vector databases, LLM-based response generation, and automated evaluation using **RAGAS**.

---

## ✨ Features

- 📄 Upload and index college PDF documents
- 🔍 Semantic search using vector embeddings
- 🤖 AI-powered question answering
- 📚 Source citations with every response
- 🚫 Graceful refusal for out-of-scope questions
- 💬 Modern ChatGPT-inspired interface
- 📊 Retrieval metrics dashboard
- ⚡ Fast document retrieval using ChromaDB
- 📈 Automated evaluation using RAGAS
- 🛡️ Hallucination-resistant grounded responses

---

# 🏗️ System Architecture

```

College PDF
│
▼

Document Loader
│
▼

Text Chunking
│
▼

Embeddings
│
▼

Chroma Vector Database
│
▼

Retriever
│
▼

LLM (OpenRouter)
│
▼

Grounded Response + Citation
