"""
Test that the RAG pipeline is working correctly after the fix.
Saves detailed results to test_rag_results.json
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import json
import os

from tool_chatbot import generate_tool_response

test_queries = [
    ("What departments does BVRIT offer?", "rag"),
    ("What is the annual fee for CSE?", "rag"),
    ("What is the total 4-year tuition for CSE?", "tool"),
    ("Who is the principal of BVRIT?", "rag"),
    ("Hello, how are you?", "conversation"),
    ("If I get a 15% scholarship, what's my annual CSE fee?", "tool"),
]

print("=" * 70)
print("RAG PIPELINE VERIFICATION TEST")
print("=" * 70)

all_pass = True
detailed_results = []

for query, expected_routing in test_queries:
    print(f"\n{'='*70}")
    print(f"Q: {query}")
    print(f"Expected routing: {expected_routing}")
    print("-" * 40)
    
    result = generate_tool_response(query, verbose=True)
    routing = result["routing"]
    answer = result["answer"][:300]
    citations = len(result.get("citations", []))
    
    print(f"\nActual routing: {routing}")
    print(f"Citations: {citations}")
    print(f"Answer: {answer}")
    
    if expected_routing == "rag" and routing == "rag":
        status = "PASS"
        print(f"✅ PASS: RAG routing correct")
    elif expected_routing == "tool" and "tool:" in routing:
        status = "PASS"
        print(f"✅ PASS: Tool routing correct")
    elif expected_routing == "conversation" and routing == "conversation":
        status = "PASS"
        print(f"✅ PASS: Conversation routing correct")
    else:
        status = "FAIL"
        print(f"❌ FAIL: Expected {expected_routing}, got {routing}")
        all_pass = False
    
    detailed_results.append({
        "query": query,
        "expected": expected_routing,
        "actual": routing,
        "status": status,
        "answer_preview": answer[:150],
        "citations": citations,
    })

print(f"\n{'='*70}")
print(f"OVERALL: {'✅ ALL PASSED' if all_pass else '❌ SOME FAILED'}")
print(f"{'='*70}")

# Save detailed results
with open("test_rag_results.json", "w", encoding="utf-8") as f:
    json.dump({
        "all_pass": all_pass,
        "results": detailed_results,
    }, f, indent=2, ensure_ascii=False)

print(f"\nDetailed results saved to test_rag_results.json")