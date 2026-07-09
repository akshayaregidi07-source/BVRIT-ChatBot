"""
FastAPI Server for Tool-Enabled BVRIT Chatbot
===============================================
Provides a REST API that the frontend React app calls to get responses.
Handles RAG, fee_calculator, date_checker, and percentage_calculator tools.
"""
import os
import json
import sys
import io

# Force UTF-8 for console output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from tool_chatbot import generate_tool_response

app = FastAPI(title="BVRIT Tool-Enabled Chatbot API")

# Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    answer: str
    routing: str
    tool_called: str = ""
    tool_arguments: str = ""
    tool_result: str = ""
    citations: list = []

@app.get("/")
def root():
    return {"status": "BVRIT Tool-Enabled Chatbot API is running", "tools": ["fee_calculator", "date_checker", "percentage_calculator"]}

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """Process a chat query through the tool-enabled RAG pipeline."""
    query = request.query
    
    # Generate response using the tool-enabled chatbot
    result = generate_tool_response(query, verbose=False)
    
    answer = result.get("answer", "I'm sorry, I couldn't generate a response.")
    routing = result.get("routing", "unknown")
    citations = result.get("citations", [])
    
    # Extract tool info if a tool was called
    tool_called = ""
    tool_arguments = ""
    tool_result_str = ""
    
    if routing and routing.startswith("tool:"):
        tool_called = routing.replace("tool:", "")
        tool_result = result.get("tool_result", {})
        if tool_result:
            tool_arguments = json.dumps(tool_result.get("arguments", {}), default=str)
            # Clean up the result for display
            formatted = tool_result.get("formatted", "")
            warnings = tool_result.get("warnings", [])
            if warnings:
                formatted += "\n⚠️ " + "\n".join(warnings)
            tool_result_str = formatted
    
    # Format citations for frontend
    citation_list = []
    for c in citations:
        citation_list.append({
            "source": c.get("preview", "Document")[:50],
            "page": c.get("page", 1),
            "confidence": 85,  # Default confidence since we don't compute it
        })
    
    return ChatResponse(
        answer=answer,
        routing=routing,
        tool_called=tool_called,
        tool_arguments=tool_arguments,
        tool_result=tool_result_str,
        citations=citation_list,
    )

if __name__ == "__main__":
    import uvicorn
    print("Starting BVRIT Tool-Enabled Chatbot API server...")
    print("API available at: http://localhost:8000")
    print("API docs at: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)