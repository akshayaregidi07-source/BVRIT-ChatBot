"""
Debug tool call arguments to understand what the LLM is sending.
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import json
import os
from dotenv import load_dotenv

load_dotenv()

from langchain_openai import ChatOpenAI
from tools import TOOL_DEFINITIONS

# Get the LLM
llm = ChatOpenAI(
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    openai_api_base="https://openrouter.ai/api/v1",
    model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
    temperature=0.2,
    max_tokens=800,
)

# Test query
query = "If I get a 15% scholarship, what's my annual CSE fee?"

# Get context
from tool_chatbot import retrieve_relevant_chunks, format_context
docs = retrieve_relevant_chunks(query)
context = format_context(docs)

SYSTEM_PROMPT = """You are an intelligent college FAQ assistant for BVRIT HYDERABAD College of Engineering for Women.

You have access to tools for fee calculations, date checking, and percentage computations.
Follow these rules in order:

## Routing Rules:
1. If the user asks a simple factual question (departments, fees, placements, dates, faculty, etc.):
   USE the retrieved context below. Do NOT call a tool just to repeat what's in the context.

2. If the user asks for a CALCULATION involving fees (total cost for X years, scholarship discounts, combined costs):
   First use the retrieved context to get the fee amounts, THEN call fee_calculator with the retrieved values.
   CRITICAL: When calling fee_calculator, you MUST provide:
   - "operation" field: use "total_tuition" for multiplying fee by years, "apply_scholarship" for scholarship discounts, "combined_cost" for tuition+hostel, "total_hostel" for hostel only
   - "annual_fee" field: the fee amount from context (e.g., 120000)
   - "years" field: for multi-year calculations (e.g., 4 for 4 years of B.Tech)
   - "scholarship_percentage" field: for scholarship calculations (e.g., 15 for 15%)

3. If the user asks whether a deadline is past, upcoming, or days remaining:
   First use the retrieved context to get the date, THEN call date_checker with the date from context.

4. If the user asks for percentage calculations:
   Use the percentage_calculator tool.

5. If the user greets you or makes small talk:
   Respond conversationally without tools or RAG.

6. If the retrieved context does NOT contain the information needed:
   Say "I'm sorry, but I don't have enough information in my knowledge base to answer this question."

## Retrieved Context (use this for factual answers and to extract values for tools):
{context}
"""

messages = [
    {"role": "system", "content": SYSTEM_PROMPT.format(context=context)},
    {"role": "user", "content": query},
]

print(f"Query: {query}")
print(f"\nContext length: {len(context)} chars")
print(f"\nCalling LLM with tools...")

response = llm.invoke(messages, tools=TOOL_DEFINITIONS, tool_choice="auto")

print(f"\nResponse type: {type(response)}")
print(f"Has tool_calls: {hasattr(response, 'tool_calls')}")

if hasattr(response, "tool_calls") and response.tool_calls:
    for tc in response.tool_calls:
        print(f"\nTool call: {tc.get('name')}")
        print(f"Arguments (raw): {tc.get('arguments')}")
        args = tc.get("arguments", {})
        if isinstance(args, str):
            args = json.loads(args)
        print(f"Arguments (parsed): {json.dumps(args, indent=2)}")
        print(f"Has 'operation': {'operation' in args}")
        print(f"operation value: {args.get('operation', 'NOT SET!')}")
else:
    print(f"Text response: {response.content[:200]}")