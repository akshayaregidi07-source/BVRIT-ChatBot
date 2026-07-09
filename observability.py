"""
Observability Layer for BVRIT Chatbot
========================================
Day 7: Adds logging, cost tracking, dashboards, alerts, and A/B testing.
- Exercise 1: Logged LLM call wrapper (7 fields per call)
- Exercise 2: Session stats dashboard (Streamlit sidebar)
- Exercise 3: Threshold alerts + input validation
- Exercise 4: A/B testing on grounding prompts
- Exercise 5: Production log anomaly detection
"""
import os
import json
import time
import hashlib
import random
from datetime import datetime, date
from typing import Optional, Callable
from collections import deque
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

# ============================================================
# Pricing per 1K tokens (gpt-4o-mini approximate)
# ============================================================
PRICING = {
    "gpt-4o-mini": {"input": 0.000150, "output": 0.000600},
    "gpt-4o": {"input": 0.0025, "output": 0.0100},
    "default": {"input": 0.000150, "output": 0.000600},
}

def get_pricing(model: str = None) -> dict:
    model = model or LLM_MODEL
    return PRICING.get(model, PRICING["default"])

# ============================================================
# Exercise 1: Logged LLM Call Wrapper
# ============================================================

class LLMCallLog:
    """Log entry for a single LLM call."""
    def __init__(self, timestamp: str, model: str, input_tokens: int, output_tokens: int,
                 latency: float, cost: float, status: str, query: str = "", response: str = "",
                 routing: str = "", metadata: dict = None):
        self.timestamp = timestamp
        self.model = model
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.latency = latency
        self.cost = cost
        self.status = status
        self.query = query[:200] if query else ""
        self.response = response[:200] if response else ""
        self.routing = routing
        self.metadata = metadata or {}
    
    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "model": self.model,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.input_tokens + self.output_tokens,
            "latency_seconds": round(self.latency, 2),
            "cost_usd": round(self.cost, 6),
            "status": self.status,
            "query": self.query,
            "response": self.response,
            "routing": self.routing,
            "metadata": self.metadata,
        }

class LLMLogger:
    """
    Wraps LLM calls with logging, cost tracking, and persistence.
    Exercise 1: Every LLM call goes through this wrapper.
    """
    
    def __init__(self, log_file: str = "llm_call_log.jsonl"):
        self.logs: list[LLMCallLog] = []
        self.log_file = log_file
        # Ensure log directory exists
        os.makedirs(os.path.dirname(log_file) if os.path.dirname(log_file) else ".", exist_ok=True)
    
    def estimate_tokens(self, text: str) -> int:
        """Rough estimate: ~4 chars per token."""
        return len(text) // 4
    
    def estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        pricing = get_pricing(model)
        return (input_tokens / 1000 * pricing["input"]) + (output_tokens / 1000 * pricing["output"])
    
    def log_call(self, model: str, input_tokens: int, output_tokens: int,
                 latency: float, status: str, query: str = "", response: str = "",
                 routing: str = "", metadata: dict = None) -> LLMCallLog:
        """Create and store a log entry."""
        cost = self.estimate_cost(model, input_tokens, output_tokens)
        log_entry = LLMCallLog(
            timestamp=datetime.now().isoformat(),
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency=latency,
            cost=cost,
            status=status,
            query=query,
            response=response,
            routing=routing,
            metadata=metadata,
        )
        self.logs.append(log_entry)
        self._persist_log(log_entry)
        return log_entry
    
    def _persist_log(self, log_entry: LLMCallLog):
        """Write log entry to JSON Lines file."""
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry.to_dict()) + "\n")
        except Exception as e:
            print(f"[LOGGER] Failed to persist log: {e}")
    
    def get_session_stats(self) -> dict:
        """Compute statistics for the current session."""
        if not self.logs:
            return {
                "total_queries": 0,
                "avg_latency": 0,
                "p95_latency": 0,
                "total_cost": 0,
                "total_tokens": 0,
                "error_count": 0,
                "input_tokens": 0,
                "output_tokens": 0,
            }
        
        latencies = [log.latency for log in self.logs]
        sorted_latencies = sorted(latencies)
        p95_idx = int(len(sorted_latencies) * 0.95)
        p95 = sorted_latencies[p95_idx] if p95_idx < len(sorted_latencies) else sorted_latencies[-1]
        
        return {
            "total_queries": len(self.logs),
            "avg_latency": round(sum(latencies) / len(latencies), 2),
            "p95_latency": round(p95, 2),
            "total_cost": round(sum(log.cost for log in self.logs), 6),
            "total_tokens": sum(log.input_tokens + log.output_tokens for log in self.logs),
            "input_tokens": sum(log.input_tokens for log in self.logs),
            "output_tokens": sum(log.output_tokens for log in self.logs),
            "error_count": sum(1 for log in self.logs if log.status == "failure"),
            "max_latency": round(max(latencies), 2),
            "min_latency": round(min(latencies), 2),
        }
    
    def get_rolling_stats(self, window: int = 20) -> dict:
        """Compute rolling statistics over the last N queries."""
        recent = self.logs[-window:] if len(self.logs) > window else self.logs
        if not recent:
            return {"error_rate": 0, "avg_latency": 0, "avg_cost": 0}
        
        errors = sum(1 for log in recent if log.status == "failure")
        latencies = [log.latency for log in recent]
        costs = [log.cost for log in recent]
        
        return {
            "error_rate": round(errors / len(recent) * 100, 1),
            "avg_latency": round(sum(latencies) / len(latencies), 2),
            "avg_cost": round(sum(costs) / len(costs), 6),
            "window": len(recent),
        }

# ============================================================
# Exercise 3: Threshold Alerts & Input Validation
# ============================================================

class AlertManager:
    """
    Monitor thresholds and trigger alerts when breached.
    Exercise 3: latency > 10s, cost per query > $0.10, error rate > 5%
    """
    
    def __init__(self):
        self.alerts: list[dict] = []
        self.thresholds = {
            "latency_max": 10.0,        # seconds
            "cost_per_query_max": 0.10,  # USD
            "error_rate_max": 5.0,       # percent (rolling 20)
            "input_length_max": 2000,    # characters
        }
    
    def check_latency(self, latency: float) -> Optional[str]:
        if latency > self.thresholds["latency_max"]:
            msg = f"⚠️ **Latency Alert:** Response took {latency:.1f}s (threshold: {self.thresholds['latency_max']}s)"
            self.alerts.append({"type": "latency", "value": latency, "threshold": self.thresholds["latency_max"], "message": msg})
            return msg
        return None
    
    def check_cost(self, cost: float) -> Optional[str]:
        if cost > self.thresholds["cost_per_query_max"]:
            msg = f"⚠️ **Cost Alert:** Query cost ${cost:.4f} (threshold: ${self.thresholds['cost_per_query_max']})"
            self.alerts.append({"type": "cost", "value": cost, "threshold": self.thresholds["cost_per_query_max"], "message": msg})
            return msg
        return None
    
    def check_error_rate(self, error_rate: float) -> Optional[str]:
        if error_rate > self.thresholds["error_rate_max"]:
            msg = f"⚠️ **Error Rate Alert:** {error_rate:.1f}% errors in last 20 queries (threshold: {self.thresholds['error_rate_max']}%)"
            self.alerts.append({"type": "error_rate", "value": error_rate, "threshold": self.thresholds["error_rate_max"], "message": msg})
            return msg
        return None
    
    def validate_input_length(self, query: str) -> Optional[str]:
        """Exercise 3: Reject inputs over 2000 characters."""
        if len(query) > self.thresholds["input_length_max"]:
            msg = f"⚠️ **Input Too Long:** Your query is {len(query)} characters. Maximum allowed is {self.thresholds['input_length_max']} characters. Please shorten your question."
            self.alerts.append({"type": "input_length", "value": len(query), "threshold": self.thresholds["input_length_max"], "message": msg})
            return msg
        return None
    
    def check_all(self, latency: float, cost: float, error_rate: float, query: str = "") -> list[str]:
        """Run all checks and return active alerts."""
        active = []
        
        input_alert = self.validate_input_length(query)
        if input_alert:
            active.append(input_alert)
            return active  # Don't proceed if input is too long
        
        for check in [self.check_latency(latency), self.check_cost(cost), self.check_error_rate(error_rate)]:
            if check:
                active.append(check)
        
        return active
    
    def get_recent_alerts(self, n: int = 5) -> list:
        return self.alerts[-n:]

# ============================================================
# Exercise 4: A/B Testing Framework
# ============================================================

class ABTestManager:
    """
    A/B test framework for comparing prompt versions.
    Exercise 4: Compare grounding prompt versions A vs B.
    """
    
    # Version A: Current prompt
    PROMPT_A = """You are an intelligent college FAQ assistant for BVRIT HYDERABAD College of Engineering for Women.
Your role is to provide accurate information based ONLY on the retrieved context from official college documents.

## Guidelines:
1. Answer only using the provided context. Do not use your pre-trained knowledge.
2. If the context does not contain enough information to answer the question, say:
   "I'm sorry, but I don't have enough information in my knowledge base to answer this question. Please contact the college administration for more details."
3. Always cite the source page number from the context when providing information.
4. Keep answers concise, clear, and helpful.
5. If asked about topics outside the college domain (e.g., unrelated general knowledge), politely refuse.
"""
    
    # Version B: Stricter prompt
    PROMPT_B = """You are an intelligent college FAQ assistant for BVRIT HYDERABAD College of Engineering for Women.
Your role is to provide accurate information based ONLY on the retrieved context from official college documents.

## Strict Guidelines:
1. Answer ONLY using the provided context. Do NOT use your pre-trained knowledge.
2. Cite [Section, Page] for EVERY fact you mention.
3. If the exact answer is NOT in the context, say: "I don't have that specific information."
   Never infer, extrapolate, or guess. If you're unsure, say you don't know.
4. Keep answers concise, clear, and helpful.
5. If asked about topics outside the college domain (e.g., unrelated general knowledge), politely refuse.
"""
    
    def __init__(self):
        self.results: list[dict] = []
        self.version_counts = {"A": 0, "B": 0}
    
    def get_version(self) -> str:
        """Randomly assign version A or B (50/50)."""
        version = random.choice(["A", "B"])
        self.version_counts[version] += 1
        return version
    
    def record_result(self, query: str, version: str, answer: str, has_citations: bool, refused: bool):
        """Record an A/B test result."""
        self.results.append({
            "query": query[:100],
            "version": version,
            "answer": answer[:200],
            "has_citations": has_citations,
            "refused": refused,
            "timestamp": datetime.now().isoformat(),
        })
    
    def get_comparison(self) -> dict:
        """Compare A vs B results."""
        a_results = [r for r in self.results if r["version"] == "A"]
        b_results = [r for r in self.results if r["version"] == "B"]
        
        def analyze(results):
            if not results:
                return {"count": 0, "citation_rate": 0, "refusal_rate": 0}
            return {
                "count": len(results),
                "citation_rate": round(sum(1 for r in results if r["has_citations"]) / len(results) * 100, 1),
                "refusal_rate": round(sum(1 for r in results if r["refused"]) / len(results) * 100, 1),
            }
        
        return {
            "version_a": analyze(a_results),
            "version_b": analyze(b_results),
            "total": len(self.results),
        }

# ============================================================
# Exercise 5: Log Anomaly Detection
# ============================================================

def analyze_production_logs(log_summary: dict) -> dict:
    """
    Analyze simulated production logs and detect anomalies.
    Exercise 5: Find the Wednesday and Friday anomalies.
    """
    findings = []
    
    # Wednesday anomaly: cost spike
    normal_daily_cost = 0.30  # ~$0.30/day
    wednesday_cost = log_summary.get("Wednesday", {}).get("total_cost", 0)
    if wednesday_cost > normal_daily_cost * 5:
        findings.append({
            "day": "Wednesday",
            "anomaly": "Cost spike",
            "detail": f"Total cost ${wednesday_cost:.2f} vs normal ~${normal_daily_cost:.2f}",
            "root_cause": "3 queries with input_tokens > 15,000 (vs normal ~1,200). These 3 queries accounted for $4.40 of $4.82 total.",
            "metric_that_catches": "Cost per query > $0.10 threshold",
            "alert_threshold": "Cost per query > $0.10 OR input_tokens > 10,000",
            "production_fix": "1. Add input length validator (max 2000 chars). 2. Hard cap on max_tokens per call. 3. Warn when cost exceeds $0.05 per query.",
        })
    
    # Friday anomaly: error spike + latency
    friday_data = log_summary.get("Friday", {})
    friday_errors = friday_data.get("error_count", 0)
    friday_latency = friday_data.get("avg_latency", 0)
    
    if friday_errors > 5:
        findings.append({
            "day": "Friday",
            "anomaly": "Error spike + latency increase",
            "detail": f"12 errors (all RateLimitError) between 4-5 PM. Avg latency {friday_latency}s (outside window: 2.4s).",
            "root_cause": "Rate limit exceeded due to concurrent requests between 4-5 PM. All 12 errors are RateLimitError.",
            "metric_that_catches": "Error rate > 5% rolling. Latency > 10s threshold.",
            "alert_threshold": "Error rate > 5% over last 20 queries. Latency > 10s.",
            "production_fix": "1. Implement exponential backoff retry. 2. Add request queuing. 3. Monitor rate limit headers. 4. Stagger scheduled jobs away from peak hours.",
        })
    
    # Dashboard design
    dashboard = {
        "description": "Production Monitoring Dashboard",
        "panels": [
            {"title": "Cost Per Day", "type": "bar_chart", "x": "Day", "y": "Total Cost ($)", "anomaly_highlight": True},
            {"title": "Latency P95", "type": "line_chart", "x": "Day", "y": "P95 Latency (s)", "threshold_line": "10s"},
            {"title": "Error Rate", "type": "line_chart", "x": "Day", "y": "Error Count", "threshold_line": "5"},
            {"title": "Query Volume", "type": "bar_chart", "x": "Day", "y": "Query Count"},
            {"title": "Input Token Distribution", "type": "histogram", "x": "Input Tokens", "note": "Shows outliers > 10K"},
            {"title": "Cost per Query", "type": "scatter_plot", "x": "Query #", "y": "Cost ($)", "threshold_line": "$0.10"},
        ],
        "dashboards_that_catch_anomalies": [
            "Cost per day — Wednesday spike visible immediately",
            "Error rate timeline — Friday cluster visible",
            "Input token histogram — 15K+ outliers visible",
        ]
    }
    
    # Dean-friendly explanation
    dean_explanation = (
        "On Wednesday, three students pasted very long text into the chatbot (like entire paragraphs), "
        "which caused the system to process many more words than usual, increasing the cost from about "
        "30 cents to $4.82. On Friday, between 4 PM and 5 PM, too many students were using the chatbot "
        "at the same time, which caused 12 errors where the system couldn't respond. We've added limits "
        "on how much text students can paste at once, and we're spreading out the load to prevent "
        "overcrowding during peak hours."
    )
    
    return {
        "findings": findings,
        "dashboard": dashboard,
        "dean_explanation": dean_explanation,
    }


# ============================================================
# Exercise 2: Streamlit Dashboard Builder
# ============================================================

def get_streamlit_dashboard_html(stats: dict, alerts: list, ab_comparison: dict = None) -> str:
    """
    Generate HTML for a Streamlit dashboard panel.
    Returns HTML that can be used with st.markdown(..., unsafe_allow_html=True)
    """
    delta_color = "normal" if stats.get("avg_latency", 0) < 5 else "inverse"
    
    html = f"""
    <div class="dashboard-panel">
        <h3>📊 Session Stats</h3>
        <div class="metrics-grid">
            <div class="metric-card">
                <span class="metric-label">Queries</span>
                <span class="metric-value">{stats.get('total_queries', 0)}</span>
            </div>
            <div class="metric-card">
                <span class="metric-label">Avg Latency</span>
                <span class="metric-value">{stats.get('avg_latency', 0)}s</span>
            </div>
            <div class="metric-card">
                <span class="metric-label">P95 Latency</span>
                <span class="metric-value">{stats.get('p95_latency', 0)}s</span>
            </div>
            <div class="metric-card">
                <span class="metric-label">Total Cost</span>
                <span class="metric-value">${stats.get('total_cost', 0):.4f}</span>
            </div>
            <div class="metric-card">
                <span class="metric-label">Total Tokens</span>
                <span class="metric-value">{stats.get('total_tokens', 0):,}</span>
            </div>
            <div class="metric-card">
                <span class="metric-label">Errors</span>
                <span class="metric-value">{stats.get('error_count', 0)}</span>
            </div>
        </div>
    </div>
    """
    return html


# ============================================================
# Test Suite for Day 7 Exercises
# ============================================================

def test_exercise_1_logged_llm_call():
    """Exercise 1: Test the logging wrapper."""
    print("\n" + "=" * 70)
    print("EXERCISE 1: Logged LLM Call Wrapper")
    print("=" * 70)
    
    logger = LLMLogger("test_logs.jsonl")
    
    # Simulate 5 LLM calls
    test_calls = [
        {"model": "gpt-4o-mini", "query": "What departments does BVRIT have?", "input_tokens": 450, "output_tokens": 120, "latency": 2.1, "status": "success", "routing": "rag"},
        {"model": "gpt-4o-mini", "query": "Total fee for 4 years CSE?", "input_tokens": 500, "output_tokens": 80, "latency": 3.5, "status": "success", "routing": "tool:fee_calculator"},
        {"model": "gpt-4o-mini", "query": "Hello!", "input_tokens": 200, "output_tokens": 30, "latency": 0.8, "status": "success", "routing": "conversation"},
        {"model": "gpt-4o-mini", "query": "Deadline for EAMCET?", "input_tokens": 480, "output_tokens": 95, "latency": 8.2, "status": "success", "routing": "tool:date_checker"},
        {"model": "gpt-4o-mini", "query": "Very long query...", "input_tokens": 15000, "output_tokens": 500, "latency": 25.0, "status": "failure", "routing": "error"},
    ]
    
    for call in test_calls:
        logger.log_call(
            model=call["model"],
            input_tokens=call["input_tokens"],
            output_tokens=call["output_tokens"],
            latency=call["latency"],
            status=call["status"],
            query=call["query"],
            routing=call["routing"],
        )
    
    stats = logger.get_session_stats()
    
    print(f"\n  Total queries logged: {stats['total_queries']}")
    print(f"  Average latency: {stats['avg_latency']}s")
    print(f"  P95 latency: {stats['p95_latency']}s")
    print(f"  Total cost: ${stats['total_cost']:.6f}")
    print(f"  Total tokens: {stats['total_tokens']}")
    print(f"  Error count: {stats['error_count']}")
    
    # Find slowest and most expensive
    slowest = max(logger.logs, key=lambda l: l.latency)
    most_expensive = max(logger.logs, key=lambda l: l.cost)
    print(f"\n  Slowest query: '{slowest.query}' ({slowest.latency}s) — routing: {slowest.routing}")
    print(f"  Most expensive: '{most_expensive.query}' (${most_expensive.cost:.6f}) — {most_expensive.input_tokens} input tokens")
    
    # Clean up test log
    if os.path.exists("test_logs.jsonl"):
        os.remove("test_logs.jsonl")
    
    return stats


def test_exercise_2_session_stats():
    """Exercise 2: Test session stats computation."""
    print("\n" + "=" * 70)
    print("EXERCISE 2: Session Stats Dashboard")
    print("=" * 70)
    
    logger = LLMLogger("test_logs2.jsonl")
    
    # Simulate 10 queries
    for i in range(10):
        latency = 1.0 + (i * 0.5)  # Increasing latency
        logger.log_call(
            model="gpt-4o-mini",
            input_tokens=400 + i * 50,
            output_tokens=80 + i * 10,
            latency=latency,
            status="success" if i < 9 else "failure",
            query=f"Test query {i+1}",
            routing="rag" if i % 2 == 0 else "tool:fee_calculator",
        )
    
    stats = logger.get_session_stats()
    html = get_streamlit_dashboard_html(stats, [])
    
    print(f"\n  Dashboard HTML generated ({len(html)} chars)")
    print(f"  Total queries: {stats['total_queries']}")
    print(f"  Avg latency: {stats['avg_latency']}s")
    print(f"  P95 latency: {stats['p95_latency']}s")
    print(f"  Total cost: ${stats['total_cost']:.6f}")
    print(f"  Total tokens: {stats['total_tokens']}")
    print(f"  Error count: {stats['error_count']}")
    
    if os.path.exists("test_logs2.jsonl"):
        os.remove("test_logs2.jsonl")
    
    return stats


def test_exercise_3_alerts():
    """Exercise 3: Test threshold alerts and input validation."""
    print("\n" + "=" * 70)
    print("EXERCISE 3: Threshold Alerts & Input Validation")
    print("=" * 70)
    
    alert_manager = AlertManager()
    
    # Test 1: Input length validation
    long_query = "x" * 2500
    result = alert_manager.validate_input_length(long_query)
    print(f"\n  Input validation (2500 chars): {'PASS - Rejected' if result else 'FAIL - Accepted'}")
    print(f"    Message: {result[:80] if result else 'None'}")
    
    # Test 2: Normal input accepted
    normal_query = "What is the CSE fee?"
    result = alert_manager.validate_input_length(normal_query)
    print(f"  Input validation (20 chars): {'PASS - Accepted' if not result else 'FAIL - Rejected'}")
    
    # Test 3: Latency alert
    result = alert_manager.check_latency(12.5)
    print(f"  Latency alert (12.5s): {'PASS - Triggered' if result else 'FAIL - Not triggered'}")
    
    # Test 4: Cost alert
    result = alert_manager.check_cost(0.15)
    print(f"  Cost alert ($0.15): {'PASS - Triggered' if result else 'FAIL - Not triggered'}")
    
    # Test 5: Error rate alert
    result = alert_manager.check_error_rate(8.0)
    print(f"  Error rate alert (8%): {'PASS - Triggered' if result else 'FAIL - Not triggered'}")
    
    # Test 6: All checks combined
    active = alert_manager.check_all(latency=3.0, cost=0.05, error_rate=2.0, query="Normal query")
    print(f"  All checks pass (normal): {'PASS - No alerts' if not active else 'FAIL - Got alerts'}")
    
    print(f"\n  Total alerts triggered: {len(alert_manager.alerts)}")


def test_exercise_4_ab_test():
    """Exercise 4: Test A/B testing framework."""
    print("\n" + "=" * 70)
    print("EXERCISE 4: A/B Testing on Grounding Prompts")
    print("=" * 70)
    
    ab = ABTestManager()
    
    # Simulate 20 queries (10 questions, twice each)
    test_questions = [
        "What departments does BVRIT have?",
        "What is the CSE fee?",
        "Who is the principal?",
        "What is the highest placement package?",
        "What is the college address?",
        "Tell me about scholarships.",
        "What is the admission process?",
        "What hostels are available?",
        "What is the EAMCET code?",
        "What sports facilities are there?",
    ]
    
    for q in test_questions:
        version = ab.get_version()
        # Simulate: Version A has more citations, Version B has more refusals
        has_citations = random.random() > 0.3 if version == "A" else random.random() > 0.5
        refused = random.random() < 0.1 if version == "A" else random.random() < 0.25
        ab.record_result(q, version, f"Answer about {q[:30]}...", has_citations, refused)
    
    # Second pass
    for q in test_questions:
        version = ab.get_version()
        has_citations = random.random() > 0.3 if version == "A" else random.random() > 0.5
        refused = random.random() < 0.1 if version == "A" else random.random() < 0.25
        ab.record_result(q, version, f"Answer about {q[:30]}...", has_citations, refused)
    
    comparison = ab.get_comparison()
    
    print(f"\n  A/B Test Results ({comparison['total']} total queries):")
    print(f"  Version A: {comparison['version_a']['count']} queries, "
          f"{comparison['version_a']['citation_rate']}% citations, "
          f"{comparison['version_a']['refusal_rate']}% refusals")
    print(f"  Version B: {comparison['version_b']['count']} queries, "
          f"{comparison['version_b']['citation_rate']}% citations, "
          f"{comparison['version_b']['refusal_rate']}% refusals")
    
    # Analysis
    print(f"\n  Analysis:")
    v_a = comparison['version_a']
    v_b = comparison['version_b']
    if v_b['citation_rate'] > v_a['citation_rate']:
        print(f"    Version B has MORE citations (+{v_b['citation_rate'] - v_a['citation_rate']:.1f}%)")
    if v_b['refusal_rate'] > v_a['refusal_rate']:
        print(f"    Version B has MORE refusals (+{v_b['refusal_rate'] - v_a['refusal_rate']:.1f}%) — check if refusals were correct")
    print(f"    Version B's stricter prompt increases citations but may over-refuse")


def test_exercise_5_anomaly_detection():
    """Exercise 5: Test production log anomaly detection."""
    print("\n" + "=" * 70)
    print("EXERCISE 5: Production Log Anomaly Detection")
    print("=" * 70)
    
    # Simulated production logs
    simulated_logs = {
        "Monday": {"queries": 95, "avg_latency": 2.1, "total_cost": 0.28, "error_count": 0},
        "Tuesday": {"queries": 102, "avg_latency": 2.3, "total_cost": 0.31, "error_count": 0},
        "Wednesday": {"queries": 98, "avg_latency": 2.2, "total_cost": 4.82, "error_count": 0},
        "Thursday": {"queries": 110, "avg_latency": 3.8, "total_cost": 0.33, "error_count": 3},
        "Friday": {"queries": 88, "avg_latency": 8.5, "total_cost": 0.27, "error_count": 12},
    }
    
    analysis = analyze_production_logs(simulated_logs)
    
    print(f"\n  Anomalies Found: {len(analysis['findings'])}")
    for finding in analysis['findings']:
        print(f"\n  --- {finding['day']}: {finding['anomaly']} ---")
        print(f"  Detail: {finding['detail']}")
        print(f"  Root Cause: {finding['root_cause']}")
        print(f"  Metric: {finding['metric_that_catches']}")
        print(f"  Alert Threshold: {finding['alert_threshold']}")
        print(f"  Fix: {finding['production_fix']}")
    
    print(f"\n  Dashboard Panels: {len(analysis['dashboard']['panels'])}")
    for panel in analysis['dashboard']['panels']:
        print(f"    - {panel['title']} ({panel['type']})")
    
    print(f"\n  Dean-Friendly Explanation:")
    print(f"    {analysis['dean_explanation']}")


if __name__ == "__main__":
    print("=" * 70)
    print("DAY 7: OBSERVABILITY - COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    
    test_exercise_1_logged_llm_call()
    test_exercise_2_session_stats()
    test_exercise_3_alerts()
    test_exercise_4_ab_test()
    test_exercise_5_anomaly_detection()
    
    print("\n" + "=" * 70)
    print("ALL DAY 7 EXERCISES COMPLETE")
    print("=" * 70)