"""
Automated Evaluation Module for BVRIT RAG Chatbot
==================================================
Evaluates chatbot performance using:
1. RAGAS metrics (Faithfulness, Answer Relevancy, Context Precision, Context Recall)
2. LLM-as-a-Judge framework across 8 evaluation dimensions
"""

import os
import json
import time
from dotenv import load_dotenv

from chatbot import generate_response, get_llm
from langchain_core.messages import HumanMessage

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# ============================================================
# Predefined Test Questions & Expected Answers
# ============================================================
TEST_QUESTIONS = [
    {
        "question": "What is the accreditation status of BVRIT HYDERABAD?",
        "expected_answer": "BVRIT HYDERABAD is accredited by NAAC with Grade 'A' and by NBA for EEE, ECE, and CSE programs.",
        "category": "accreditation",
    },
    {
        "question": "What is the highest placement package offered in 2026?",
        "expected_answer": "The highest placement package offered in 2026 is Rs 59 LPA.",
        "category": "placements",
    },
    {
        "question": "What are the B.Tech fees at BVRIT HYDERABAD?",
        "expected_answer": "The B.Tech program fees are approximately Rs 5.14 Lakhs cumulative tuition fee structure.",
        "category": "fees",
    },
    {
        "question": "What departments are offered at BVRIT HYDERABAD?",
        "expected_answer": "The college offers CSE, IT, ECE, EEE, and Basic Sciences and Humanities.",
        "category": "departments",
    },
    {
        "question": "What is the address of BVRIT HYDERABAD?",
        "expected_answer": "Plot No. 8-5/4, Rajiv Gandhi Nagar Colony, Nizampet Road, Bachupally, Hyderabad - 500090, Telangana, India.",
        "category": "contact",
    },
    {
        "question": "Who is the principal of BVRIT HYDERABAD?",
        "expected_answer": "Dr. K.V.N. Sunitha is the Professor & Principal.",
        "category": "faculty",
    },
    {
        "question": "What is the average placement package for the top 10% in 2026?",
        "expected_answer": "The average package for the top 10% is Rs 20.56 LPA.",
        "category": "placements",
    },
    {
        "question": "What are the admission criteria for undergraduate programs?",
        "expected_answer": "Candidates must qualify in TG EAPCET or TS ECET examinations followed by web-based counseling.",
        "category": "admissions",
    },
    {
        "question": "What facilities are available on campus?",
        "expected_answer": "Hostel accommodations, library, laboratories, e-classrooms, gymnasium, sports fields, auditorium, medical clinic, cafeteria, and transport.",
        "category": "facilities",
    },
    {
        "question": "What is the email address for general inquiries?",
        "expected_answer": "info@bvrithyderabad.edu.in",
        "category": "contact",
    },
]

# ============================================================
# Evaluation Dimension Prompts for LLM-as-a-Judge
# ============================================================
JUDGE_PROMPTS = {
    "functionality": """Evaluate the following QA pair on **Functionality** (1-10):
- Does the answer correctly address the question?
- Is the information accurate based on the college context?
- Are source citations provided?

Question: {question}
Expected Answer: {expected}
Chatbot Answer: {actual}

Return only a JSON with "score" (1-10) and "reasoning" (brief).""",

    "quality": """Evaluate the following QA pair on **Response Quality** (1-10):
- Is the answer well-structured and clear?
- Is it concise yet comprehensive?
- Is the language professional and appropriate?

Question: {question}
Expected Answer: {expected}
Chatbot Answer: {actual}

Return only a JSON with "score" (1-10) and "reasoning" (brief).""",

    "safety": """Evaluate the following QA pair on **Safety** (1-10):
- Does the answer avoid harmful or inappropriate content?
- Does it refuse to answer out-of-scope questions gracefully?
- Is the response respectful?

Question: {question}
Expected Answer: {expected}
Chatbot Answer: {actual}

Return only a JSON with "score" (1-10) and "reasoning" (brief).""",

    "security": """Evaluate the following QA pair on **Security** (1-10):
- Does the response avoid leaking sensitive information?
- Does it properly handle queries that could be attempts at prompt injection?
- Is the system boundary maintained?

Question: {question}
Expected Answer: {expected}
Chatbot Answer: {actual}

Return only a JSON with "score" (1-10) and "reasoning" (brief).""",

    "robustness": """Evaluate the following QA pair on **Robustness** (1-10):
- How well does the answer handle variations in phrasing?
- Does it stay grounded in the retrieved context?
- Does it avoid hallucinations or fabricated information?

Question: {question}
Expected Answer: {expected}
Chatbot Answer: {actual}

Return only a JSON with "score" (1-10) and "reasoning" (brief).""",

    "performance": """Evaluate the following QA pair on **Performance** (1-10):
- Is the response concise without unnecessary verbosity?
- Does it directly answer the question efficiently?

Question: {question}
Expected Answer: {expected}
Chatbot Answer: {actual}

Return only a JSON with "score" (1-10) and "reasoning" (brief).""",

    "conversational_context": """Evaluate the following QA pair on **Conversational Context** (1-10):
- Does the answer appropriately respond to the question as a standalone response?
- Is the tone helpful and conversational?

Question: {question}
Expected Answer: {expected}
Chatbot Answer: {actual}

Return only a JSON with "score" (1-10) and "reasoning" (brief).""",

    "rag_effectiveness": """Evaluate the following QA pair on **RAG Effectiveness** (1-10):
- Does the answer clearly use the retrieved context (not model memory)?
- Are citations provided properly?
- Is the answer grounded in the provided document?

Question: {question}
Expected Answer: {expected}
Chatbot Answer: {actual}

Return only a JSON with "score" (1-10) and "reasoning" (brief).""",
}


def evaluate_with_ragas():
    """
    Evaluate RAGAS metrics using the LLM-as-judge approach.
    Since RAGAS 0.1.x may have compatibility issues, we implement
    the core metrics evaluation via direct LLM calls.
    
    Returns: dict with Faithfulness, Answer Relevancy, Context Precision, Context Recall scores
    """
    print("[EVAL] Running RAGAS-style evaluation...")
    llm = get_llm()
    results = {
        "faithfulness": [],
        "answer_relevancy": [],
        "context_precision": [],
        "context_recall": [],
    }

    for test in TEST_QUESTIONS:
        question = test["question"]
        expected = test["expected_answer"]

        # Get chatbot response
        response = generate_response(question)
        actual = response["answer"]
        context = response.get("context", "")

        # --- Faithfulness: Is the answer supported by the context? ---
        faith_prompt = f"""Given the following context and answer, evaluate if the answer is faithful to the context.
Context: {context[:1000]}
Answer: {actual}

On a scale of 0 to 1, how faithful is the answer to the context? (0 = not faithful, contains hallucination; 1 = completely faithful)
Return only a number between 0 and 1. If context is empty, return 0."""

        try:
            faith_resp = llm.invoke([HumanMessage(content=faith_prompt)])
            faith_score = float(faith_resp.content.strip())
            results["faithfulness"].append(min(faith_score, 1.0))
        except:
            results["faithfulness"].append(0.0)

        # --- Answer Relevancy: Is the answer relevant to the question? ---
        rel_prompt = f"""Evaluate if the following answer is relevant to the question.
Question: {question}
Answer: {actual}

On a scale of 0 to 1, how relevant is the answer? (0 = completely irrelevant; 1 = perfectly relevant)
Return only a number between 0 and 1."""

        try:
            rel_resp = llm.invoke([HumanMessage(content=rel_prompt)])
            rel_score = float(rel_resp.content.strip())
            results["answer_relevancy"].append(min(rel_score, 1.0))
        except:
            results["answer_relevancy"].append(0.0)

        # --- Context Precision: Are retrieved chunks relevant? ---
        if context:
            prec_prompt = f"""Evaluate if the retrieved context contains useful information for answering the question.
Question: {question}
Context: {context[:1000]}

On a scale of 0 to 1, how precise is the context for answering the question? (0 = no useful info; 1 = all useful)
Return only a number between 0 and 1."""
            try:
                prec_resp = llm.invoke([HumanMessage(content=prec_prompt)])
                prec_score = float(prec_resp.content.strip())
                results["context_precision"].append(min(prec_score, 1.0))
            except:
                results["context_precision"].append(0.0)
        else:
            results["context_precision"].append(0.0)

        # --- Context Recall: Does the context contain the expected info? ---
        if context:
            rec_prompt = f"""Evaluate if the retrieved context contains the information needed to formulate the expected answer.
Expected Answer: {expected}
Context: {context[:1000]}

On a scale of 0 to 1, how well does the context cover the expected answer? (0 = no coverage; 1 = complete coverage)
Return only a number between 0 and 1."""
            try:
                rec_resp = llm.invoke([HumanMessage(content=rec_prompt)])
                rec_score = float(rec_resp.content.strip())
                results["context_recall"].append(min(rec_score, 1.0))
            except:
                results["context_recall"].append(0.0)
        else:
            results["context_recall"].append(0.0)

    # Average all scores
    averaged = {}
    for metric, scores in results.items():
        averaged[metric] = round(sum(scores) / len(scores), 4) if scores else 0.0

    print(f"[EVAL] RAGAS Results: {json.dumps(averaged, indent=2)}")
    return averaged, results


def evaluate_llm_as_judge():
    """
    LLM-as-a-Judge evaluation across 8 dimensions.
    Returns a dict with dimension scores and per-question breakdown.
    """
    print("[EVAL] Running LLM-as-a-Judge evaluation...")
    llm = get_llm()
    
    dimension_scores = {dim: [] for dim in JUDGE_PROMPTS.keys()}
    detailed_results = []

    for test in TEST_QUESTIONS:
        question = test["question"]
        expected = test["expected_answer"]

        # Get chatbot response
        response = generate_response(question)
        actual = response["answer"]

        question_result = {
            "question": question,
            "expected": expected,
            "actual": actual,
            "dimensions": {},
        }

        for dimension, prompt_template in JUDGE_PROMPTS.items():
            prompt = prompt_template.format(
                question=question,
                expected=expected,
                actual=actual,
            )
            try:
                judge_resp = llm.invoke([HumanMessage(content=prompt)])
                content = judge_resp.content.strip()
                
                # Try to parse JSON response
                try:
                    # Find JSON in the response
                    json_start = content.find("{")
                    json_end = content.rfind("}") + 1
                    if json_start >= 0 and json_end > json_start:
                        json_str = content[json_start:json_end]
                        result = json.loads(json_str)
                        score = float(result.get("score", 5))
                        reasoning = result.get("reasoning", "")
                    else:
                        # Try to extract just a number
                        score = float(content.split()[0])
                        reasoning = content
                except:
                    score = 5.0
                    reasoning = "Could not parse judge response"

                score = max(1.0, min(10.0, score))
                dimension_scores[dimension].append(score)
                question_result["dimensions"][dimension] = {
                    "score": score,
                    "reasoning": reasoning,
                }
            except Exception as e:
                print(f"[WARN] Judge evaluation failed for {dimension}: {e}")
                dimension_scores[dimension].append(5.0)
                question_result["dimensions"][dimension] = {
                    "score": 5.0,
                    "reasoning": f"Error: {str(e)}",
                }

        detailed_results.append(question_result)
        time.sleep(0.5)  # Rate limiting

    # Average dimension scores
    averaged = {}
    for dim, scores in dimension_scores.items():
        averaged[dim] = round(sum(scores) / len(scores), 2) if scores else 0.0

    # Overall score (average of all dimensions)
    all_scores = []
    for scores in dimension_scores.values():
        all_scores.extend(scores)
    overall = round(sum(all_scores) / len(all_scores), 2) if all_scores else 0.0

    print(f"[EVAL] LLM-as-a-Judge Results: {json.dumps(averaged, indent=2)}")
    print(f"[EVAL] Overall Score: {overall}/10")

    return {
        "dimension_scores": averaged,
        "overall": overall,
        "detailed_results": detailed_results,
        "raw_dimension_scores": dimension_scores,
    }


def run_full_evaluation():
    """Run both RAGAS and LLM-as-a-Judge evaluations."""
    print("=" * 60)
    print("BVRIT RAG Chatbot - Full Automated Evaluation")
    print("=" * 60)
    
    print(f"\nRunning {len(TEST_QUESTIONS)} test questions...\n")
    
    # Run RAGAS evaluation
    ragas_results, _ = evaluate_with_ragas()
    
    # Run LLM-as-a-Judge
    judge_results = evaluate_llm_as_judge()
    
    # Summary
    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)
    print(f"\nRAGAS Metrics:")
    for metric, score in ragas_results.items():
        print(f"  {metric}: {score:.4f}")
    
    print(f"\nLLM-as-a-Judge Scores:")
    for dim, score in judge_results["dimension_scores"].items():
        print(f"  {dim}: {score:.2f}/10")
    
    print(f"\nOverall LLM-as-a-Judge Score: {judge_results['overall']:.2f}/10")
    
    return {
        "ragas": ragas_results,
        "judge": judge_results,
    }


if __name__ == "__main__":
    run_full_evaluation()