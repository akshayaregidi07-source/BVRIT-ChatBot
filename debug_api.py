"""
Systematic API Debug Script
Tests every step of the pipeline and reports exactly where it fails.
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import os
import json
import traceback
import urllib.request
import urllib.error

def test_step(name, fn):
    """Run a test step and report result."""
    try:
        result = fn()
        print(f"  ✅ {name}: {result}")
        return True, result
    except Exception as e:
        print(f"  ❌ {name}: {type(e).__name__}: {str(e)[:200]}")
        traceback.print_exc()
        return False, str(e)

print("=" * 60)
print("BVRIT Chatbot - Systematic API Debugging")
print("=" * 60)

# Step 1: Check if API server is running
print("\n[Step 1] Backend API Availability")
test_step("Port 8000 connectivity", 
    lambda: "OK" if urllib.request.urlopen("http://127.0.0.1:8000/", timeout=5).getcode() == 200 else "FAIL")

test_step("GET / response",
    lambda: json.loads(urllib.request.urlopen("http://127.0.0.1:8000/", timeout=5).read())["status"])

# Step 2: Test chat endpoint
print("\n[Step 2] Chat Endpoint")
test_data = json.dumps({"query": "What departments does BVRIT offer?"}).encode()
req = urllib.request.Request("http://127.0.0.1:8000/chat", data=test_data, 
                             headers={"Content-Type": "application/json"})
try:
    resp = urllib.request.urlopen(req, timeout=60)
    result = json.loads(resp.read())
    print(f"  ✅ POST /chat: Status {resp.status}")
    print(f"     Routing: {result.get('routing')}")
    print(f"     Answer: {result.get('answer', '')[:150]}")
except urllib.error.HTTPError as e:
    print(f"  ❌ POST /chat: HTTP {e.code}")
    body = e.read().decode('utf-8', errors='replace')
    print(f"     Body: {body[:500]}")

# Step 3: Test proxy through frontend
print("\n[Step 3] Frontend Proxy")
test_step("GET /api/ through proxy",
    lambda: json.loads(urllib.request.urlopen("http://localhost:5176/api/", timeout=5).read())["status"])

# Step 4: Test chat through proxy
print("\n[Step 4] Chat through Proxy")
test_data = json.dumps({"query": "What departments does BVRIT offer?"}).encode()
req = urllib.request.Request("http://localhost:5176/api/chat", data=test_data,
                             headers={"Content-Type": "application/json"})
try:
    resp = urllib.request.urlopen(req, timeout=60)
    result = json.loads(resp.read())
    print(f"  ✅ POST /api/chat: Status {resp.status}")
    print(f"     Routing: {result.get('routing')}")
    print(f"     Answer: {result.get('answer', '')[:150]}")
except urllib.error.HTTPError as e:
    print(f"  ❌ POST /api/chat: HTTP {e.code}")
    body = e.read().decode('utf-8', errors='replace')
    print(f"     Body: {body[:500]}")
except Exception as e:
    print(f"  ❌ POST /api/chat: {type(e).__name__}: {str(e)[:200]}")

print("\n" + "=" * 60)
print("Debug complete.")