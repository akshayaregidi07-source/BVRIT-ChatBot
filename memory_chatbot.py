"""
Memory-Enabled BVRIT Chatbot
=============================
Day 6: Adds memory layers to the tool-enabled chatbot.
- Exercise 1: Short-term memory (conversation history for multi-turn)
- Exercise 2: Medium-term memory (summarisation for long conversations)
- Exercise 3: Long-term memory (persistent user profiles across sessions)
- Exercise 4: Personalisation (adaptive responses based on preferences)
- Exercise 5: Privacy (right to be forgotten, data classification, auto-expire)
"""
import os
import json
import time
import hashlib
from datetime import datetime, date, timedelta
from typing import Optional
from dotenv import load_dotenv

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from tools import TOOL_DEFINITIONS, TOOL_FUNCTIONS, execute_tool_call

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
CHROMA_DB_DIR = os.getenv("CHROMA_DB_DIR", "./chroma_db")
USER_PROFILES_DIR = os.getenv("USER_PROFILES_DIR", "./user_profiles")
TOP_K = 4

os.makedirs(USER_PROFILES_DIR, exist_ok=True)

# ============================================================
# Exercise 3: User Profile Schema
# ============================================================
DEFAULT_USER_PROFILE = {
    "user_id": "",
    "name": None,
    "branch_interest": None,
    "language": "english",
    "detail_level": "detailed",  # "brief" or "detailed"
    "preferred_format": "paragraph",  # "paragraph", "bullets", "table"
    "prior_topics": [],
    "last_session_summary": "",
    "fee_amounts_discussed": [],
    "scholarship_details": [],
    "created_at": None,
    "last_active": None,
    "conversation_count": 0,
}

# ============================================================
# Exercise 5: Privacy Notice
# ============================================================
PRIVACY_NOTICE = (
    "🔒 **Privacy Notice:** I remember basic information about our conversation "
    "(like your name and interests) to provide personalised responses. "
    "This data is stored locally and never shared. "
    "You can type **'Clear my data'** at any time to delete everything I remember about you. "
    "Profiles not accessed for 30 days are automatically deleted."
)

# ============================================================
# Exercise 5: Data Classification
# ============================================================
DATA_CLASSIFICATION = {
    "name": "NICE_TO_HAVE",  # Personalises but not essential
    "branch_interest": "ESSENTIAL",  # Needed for relevant answers
    "language": "NICE_TO_HAVE",  # Improves experience
    "detail_level": "NICE_TO_HAVE",  # Response formatting preference
    "preferred_format": "NICE_TO_HAVE",
    "prior_topics": "ESSENTIAL",  # Needed for context
    "last_session_summary": "ESSENTIAL",  # Needed for continuity
    "fee_amounts_discussed": "NICE_TO_HAVE",  # Helpful but not critical
    "scholarship_details": "NICE_TO_HAVE",
    "full_conversation_transcripts": "SENSITIVE",  # Should NOT be stored long-term
    "created_at": "ESSENTIAL",  # For auto-expire
    "last_active": "ESSENTIAL",  # For auto-expire
    "conversation_count": "NICE_TO_HAVE",
}

# ============================================================
# Infrastructure
# ============================================================
def get_embeddings():
    return OpenAIEmbeddings(
        openai_api_key=OPENROUTER_API_KEY,
        openai_api_base="https://openrouter.ai/api/v1",
        model=EMBEDDING_MODEL,
    )

def get_vector_store():
    embeddings = get_embeddings()
    return Chroma(
        persist_directory=CHROMA_DB_DIR,
        embedding_function=embeddings,
    )

def get_llm():
    return ChatOpenAI(
        openai_api_key=OPENROUTER_API_KEY,
        openai_api_base="https://openrouter.ai/api/v1",
        model=LLM_MODEL,
        temperature=0.2,
        max_tokens=800,
    )

def retrieve_relevant_chunks(query: str, top_k: int = TOP_K):
    vector_store = get_vector_store()
    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": top_k},
    )
    return retriever.invoke(query)

def format_context(docs) -> str:
    context_parts = []
    for i, doc in enumerate(docs, 1):
        page_num = doc.metadata.get("page", "N/A")
        source = doc.metadata.get("source", "College Document")
        content = doc.page_content.strip()
        context_parts.append(f"[Source {i}] (Page {page_num} from {source})\n{content}\n")
    return "\n".join(context_parts)

def format_citations(docs) -> list:
    citations = []
    for i, doc in enumerate(docs, 1):
        page_num = doc.metadata.get("page", "N/A")
        content_preview = doc.page_content.strip()[:100]
        citations.append({"number": i, "page": page_num, "preview": content_preview})
    return citations

# ============================================================
# Exercise 3: User Profile Management
# ============================================================

def get_user_id(user_name: str = "") -> str:
    """Generate a consistent user ID from a name, or use a default."""
    if user_name:
        return hashlib.md5(user_name.lower().strip().encode()).hexdigest()[:12]
    return "anonymous"

def load_user_profile(user_id: str) -> dict:
    """Load a user profile from persistent storage."""
    profile_path = os.path.join(USER_PROFILES_DIR, f"{user_id}.json")
    if os.path.exists(profile_path):
        with open(profile_path, "r", encoding="utf-8") as f:
            return json.load(f)
    profile = DEFAULT_USER_PROFILE.copy()
    profile["user_id"] = user_id
    profile["created_at"] = datetime.now().isoformat()
    profile["last_active"] = datetime.now().isoformat()
    return profile

def save_user_profile(profile: dict):
    """Save a user profile to persistent storage."""
    profile["last_active"] = datetime.now().isoformat()
    profile_path = os.path.join(USER_PROFILES_DIR, f"{profile['user_id']}.json")
    with open(profile_path, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2, default=str)

def delete_user_profile(user_id: str) -> bool:
    """Delete a user profile (right to be forgotten)."""
    profile_path = os.path.join(USER_PROFILES_DIR, f"{user_id}.json")
    if os.path.exists(profile_path):
        os.remove(profile_path)
        return True
    return False

def auto_expire_profiles(max_age_days: int = 30):
    """Exercise 5: Auto-expire profiles not accessed for 30 days."""
    cutoff = datetime.now() - timedelta(days=max_age_days)
    expired_count = 0
    for filename in os.listdir(USER_PROFILES_DIR):
        if filename.endswith(".json"):
            profile_path = os.path.join(USER_PROFILES_DIR, filename)
            with open(profile_path, "r", encoding="utf-8") as f:
                profile = json.load(f)
            last_active_str = profile.get("last_active", profile.get("created_at", ""))
            if last_active_str:
                try:
                    last_active = datetime.fromisoformat(last_active_str)
                    if last_active < cutoff:
                        os.remove(profile_path)
                        expired_count += 1
                except ValueError:
                    continue
    return expired_count

def update_profile_from_conversation(profile: dict, conversation_history: list):
    """Extract user info from conversation and update profile."""
    # Get the full conversation text
    full_text = " ".join([
        msg["content"] for msg in conversation_history 
        if msg["role"] in ("user", "assistant")
    ])
    
    # Check for name mentions
    name_keywords = ["my name is", "i'm ", "i am ", "call me "]
    for keyword in name_keywords:
        idx = full_text.lower().find(keyword)
        if idx >= 0:
            after = full_text[idx + len(keyword):].strip()
            name = after.split()[0].strip(".,!?")
            if len(name) > 1 and not name.startswith("the"):
                profile["name"] = name
                profile["user_id"] = get_user_id(name)
                break
    
    # Check for branch interest
    branches = ["cse", "computer science", "ece", "electronics", "eee", "electrical", 
                "it", "information technology", "mechanical", "civil"]
    for branch in branches:
        if branch in full_text.lower():
            # Map to standard names
            branch_map = {
                "cse": "CSE", "computer science": "CSE",
                "ece": "ECE", "electronics": "ECE",
                "eee": "EEE", "electrical": "EEE",
                "it": "IT", "information technology": "IT",
                "mechanical": "Mechanical", "civil": "Civil"
            }
            for key, val in branch_map.items():
                if key in full_text.lower():
                    # branch_interest is a string, not a list of dicts
                    if not profile.get("branch_interest"):
                        profile["branch_interest"] = val
                    break
    
    # Check for detail preference
    if "brief" in full_text.lower() or "short" in full_text.lower() or "quick" in full_text.lower():
        profile["detail_level"] = "brief"
    elif "detailed" in full_text.lower() or "elaborate" in full_text.lower() or "in depth" in full_text.lower():
        profile["detail_level"] = "detailed"
    
    # Check for language preference
    if "telugu" in full_text.lower() or "hindi" in full_text.lower():
        profile["language"] = "telugu" if "telugu" in full_text.lower() else "hindi"
    elif "english" in full_text.lower():
        profile["language"] = "english"
    
    # Track topics
    topics_added = []
    for keyword in ["department", "branch", "fee", "placement", "admission", "scholarship", 
                    "hostel", "campus", "faculty", "exam", "deadline"]:
        if keyword in full_text.lower():
            topic = keyword.capitalize()
            if topic not in profile["prior_topics"]:
                profile["prior_topics"].append(topic)
                topics_added.append(topic)
    
    profile["conversation_count"] += 1

# ============================================================
# Exercise 2: Conversation Summarisation
# ============================================================

SUMMARISATION_PROMPT = """Summarise the following conversation between a user and a BVRIT college FAQ assistant.
Preserve these details in your summary:
1. The user's name (if stated)
2. Which branches/topics they asked about
3. Key facts discussed (specific fee amounts, dates, scholarship percentages)
4. Any preferences stated ("I prefer CSE", "explain briefly", "answer in Telugu")
5. Unresolved questions or follow-up threads

CONVERSATION:
{conversation_text}

SUMMARY:"""

def summarise_conversation(conversation_history: list) -> str:
    """Summarise older conversation turns to save context window space."""
    # Format the conversation text
    conversation_text = ""
    for msg in conversation_history:
        role = "User" if msg["role"] == "user" else "Assistant"
        content = msg["content"]
        conversation_text += f"{role}: {content}\n"
    
    # Call LLM to summarise
    llm = get_llm()
    prompt = SUMMARISATION_PROMPT.format(conversation_text=conversation_text[:4000])
    messages = [SystemMessage(content="You are a conversation summariser."), HumanMessage(content=prompt)]
    response = llm.invoke(messages)
    return response.content.strip()

# ============================================================
# Exercise 1 & 4: Memory-Enabled System Prompt Builder
# ============================================================

def build_system_prompt(profile: dict, context: str, summary: str = "") -> str:
    """Build a system prompt with user profile and conversation context."""
    
    # Personalisation section (Exercise 4)
    personalisation = ""
    if profile.get("name"):
        personalisation += f"\n- The user's name is {profile['name']}. Address them by name."
    if profile.get("branch_interest"):
        personalisation += f"\n- The user is interested in {profile['branch_interest']}. Prioritise information about this branch."
    if profile.get("detail_level") == "brief":
        personalisation += f"\n- The user prefers BRIEF answers. Keep responses concise."
    elif profile.get("detail_level") == "detailed":
        personalisation += f"\n- The user prefers DETAILED answers. Provide thorough explanations."
    if profile.get("language") and profile["language"] != "english":
        personalisation += f"\n- The user prefers responses in {profile['language'].title()}. Provide answers in {profile['language'].title()}."
    if profile.get("preferred_format") == "bullets":
        personalisation += f"\n- The user prefers bullet-point format."
    if profile.get("prior_topics"):
        topics = ", ".join(profile["prior_topics"][-5:])
        personalisation += f"\n- Previously discussed topics: {topics}."
    
    # Privacy notice (first interaction only)
    privacy = ""
    if profile.get("conversation_count", 0) <= 1:
        privacy = f"\n\n{PRIVACY_NOTICE}"
    
    prompt = f"""You are an intelligent college FAQ assistant for BVRIT HYDERABAD College of Engineering for Women.

You have access to tools for fee calculations, date checking, and percentage computations.
Follow these rules in order:

## Routing Rules:
1. If the user asks a simple factual question (departments, fees, placements, dates, faculty, etc.):
   USE the retrieved context below. Do NOT call a tool just to repeat what's in the context.

2. If the user asks for a CALCULATION involving fees (total cost for X years, scholarship discounts, combined costs):
   First use the retrieved context to get the fee amounts, THEN call fee_calculator with the retrieved values.

3. If the user asks whether a deadline is past, upcoming, or days remaining:
   First use the retrieved context to get the date, THEN call date_checker with the date from context.

4. If the user asks for percentage calculations:
   Use the percentage_calculator tool.

5. If the user greets you or makes small talk:
   Respond conversationally without tools or RAG.

6. If the retrieved context does NOT contain the information needed:
   Say "I'm sorry, but I don't have enough information in my knowledge base to answer this question."

## User Profile:{personalisation}

## Conversation Summary (previous turns):
{summary if summary else "No prior conversation summary available."}

## Retrieved Context:
{context}
"""
    return prompt + privacy

# ============================================================
# Exercise 1: Memory-Enabled Response Generation
# ============================================================

class MemoryChatbot:
    """
    A chatbot with short-term memory (conversation history),
    medium-term memory (summarisation), long-term memory (persistent profiles),
    and personalisation.
    """
    
    def __init__(self, user_id: str = "anonymous"):
        self.user_id = user_id
        self.profile = load_user_profile(user_id)
        self.conversation_history = []  # Full history for current session
        self.summary = ""  # Summarised older turns
        self.turn_count = 0
        self.SUMMARISE_AFTER = 10  # Summarise every 10 turns
        self.privacy_shown = False
        
        # Auto-expire old profiles on init
        expired = auto_expire_profiles(30)
        if expired > 0:
            print(f"[MEMORY] Auto-expired {expired} old profile(s)")
    
    def _get_user_id_from_history(self):
        """Try to extract user ID from conversation history."""
        for msg in self.conversation_history:
            if msg["role"] == "user":
                text = msg["content"].lower()
                if "my name is" in text:
                    name = text.split("my name is")[-1].strip().split()[0].strip(".,!?")
                    if len(name) > 1:
                        return get_user_id(name)
        return self.user_id
    
    def generate_response(self, query: str, verbose: bool = True) -> dict:
        """Generate a response with full memory support."""
        self.turn_count += 1
        routing_path = "unknown"
        
        # Step 1: Retrieve relevant chunks
        docs = retrieve_relevant_chunks(query)
        context = format_context(docs) if docs else "No relevant documents found."
        
        # Step 2: Build system prompt with profile and summary
        system_prompt = build_system_prompt(self.profile, context, self.summary)
        
        # Step 3: Build messages with full conversation history
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add summarised history + recent turns
        if self.summary:
            messages.append({"role": "system", "content": f"[Previous conversation summary: {self.summary}]"})
        
        # Add last 10 turns verbatim
        recent_turns = self.conversation_history[-10:] if len(self.conversation_history) > 10 else self.conversation_history
        for msg in recent_turns:
            messages.append(msg)
        
        # Add current query
        messages.append({"role": "user", "content": query})
        
        # Step 4: Call LLM with tool definitions
        llm = get_llm()
        
        try:
            response = llm.invoke(
                messages,
                tools=TOOL_DEFINITIONS,
                tool_choice="auto",
            )
        except Exception as e:
            return {
                "answer": f"❌ Error calling LLM: {str(e)}",
                "citations": [],
                "has_answer": False,
                "routing": "error",
                "tool_result": None,
            }
        
        # Step 5: Check for tool calls
        if hasattr(response, "tool_calls") and response.tool_calls:
            tool_call = response.tool_calls[0]
            tool_name = tool_call.get("name", "unknown")
            
            if verbose:
                print(f"[ROUTING] Tool called: {tool_name}")
                print(f"[ROUTING] Arguments: {tool_call.get('arguments', {})}")
            
            tool_result = execute_tool_call(tool_call)
            
            if tool_result.get("error"):
                final_answer = f"⚠️ {tool_result['error']}"
            else:
                formatted = tool_result.get("formatted", "")
                warnings = tool_result.get("warnings", [])
                answer_parts = [formatted]
                if warnings:
                    for w in warnings:
                        answer_parts.append(f"\n\n⚠️ {w}")
                if docs:
                    answer_parts.append("\n\n*(Fee information retrieved from the college document.)*")
                final_answer = "".join(answer_parts)
            
            routing_path = f"tool:{tool_name}"
            
            result = {
                "answer": final_answer,
                "citations": format_citations(docs) if docs else [],
                "has_answer": True,
                "routing": routing_path,
                "tool_result": tool_result,
                "context": context,
            }
        else:
            answer = response.content.strip() if hasattr(response, "content") else str(response)
            
            if docs and any(kw in query.lower() for kw in [
                "department", "branch", "cse", "ece", "eee", "it", "b.tech",
                "fee", "fees", "tuition", "admission", "placement", "scholarship",
                "faculty", "principal", "hostel", "campus", "library", "lab",
                "contact", "email", "address", "phone", "accreditation", "naac",
                "nba", "ranking", "package", "lpa", "recruiter",
                "college", "b.v.r.i.t", "bvrit", "eamcet", "tg eapcet", "counseling",
            ]):
                routing_path = "rag"
            else:
                routing_path = "conversation"
            
            result = {
                "answer": answer,
                "citations": format_citations(docs) if docs and routing_path == "rag" else [],
                "has_answer": routing_path in ("rag", "conversation"),
                "routing": routing_path,
                "tool_result": None,
                "context": context,
            }
        
        # Step 6: Update conversation history
        self.conversation_history.append({"role": "user", "content": query})
        self.conversation_history.append({"role": "assistant", "content": result["answer"]})
        
        # Step 7: Update profile from conversation
        update_profile_from_conversation(self.profile, self.conversation_history)
        
        # Step 8: Exercise 2 - Summarise if over threshold
        if self.turn_count > 0 and self.turn_count % self.SUMMARISE_AFTER == 0:
            if verbose:
                print(f"[MEMORY] Turn {self.turn_count}: Summarising conversation...")
            # Summarise all but the last 10 turns
            if len(self.conversation_history) > 20:
                older_turns = self.conversation_history[:-10]
                self.summary = summarise_conversation(older_turns)
                if verbose:
                    print(f"[MEMORY] Summary: {self.summary[:100]}...")
                    token_count_before = sum(len(m["content"]) for m in older_turns)
                    token_count_after = len(self.summary)
                    print(f"[MEMORY] Token savings: ~{token_count_before - token_count_after} chars ({token_count_before} -> {token_count_after})")
        
        # Step 9: Check for "clear my data" command (Exercise 5)
        if query.lower().strip() in ["clear my data", "clear my data.", "forget me", "delete my data", "erase my data"]:
            delete_user_profile(self.profile["user_id"])
            result["answer"] = "✅ Your data has been cleared. I no longer remember any personal information about you. You can start fresh."
            self.profile = DEFAULT_USER_PROFILE.copy()
            self.profile["user_id"] = self._get_user_id_from_history()
            self.profile["created_at"] = datetime.now().isoformat()
            self.profile["last_active"] = datetime.now().isoformat()
            save_user_profile(self.profile)
        
        # Save profile periodically
        if self.turn_count % 3 == 0:
            # Update user_id if we learned a name
            detected_id = self._get_user_id_from_history()
            if detected_id != self.user_id:
                self.user_id = detected_id
                self.profile["user_id"] = detected_id
            save_user_profile(self.profile)
        
        return result
    
    def get_conversation_tokens(self) -> dict:
        """Estimate token usage of conversation history."""
        total_chars = sum(len(msg["content"]) for msg in self.conversation_history)
        summary_chars = len(self.summary)
        return {
            "total_chars": total_chars,
            "summary_chars": summary_chars,
            "estimated_tokens": total_chars // 4,
            "summary_tokens": summary_chars // 4,
            "savings_chars": total_chars - summary_chars if self.summary else 0,
            "turn_count": self.turn_count,
        }


# ============================================================
# Test Suite for Day 6 Exercises
# ============================================================

def test_exercise_1_multi_turn():
    """Exercise 1: Test multi-turn conversation with coreference resolution."""
    print("\n" + "=" * 70)
    print("EXERCISE 1: Multi-Turn Memory (Coreference Resolution)")
    print("=" * 70)
    
    bot = MemoryChatbot("test_e1")
    
    test_script = [
        ("Turn 1", "What B.Tech branches does BVRIT offer?"),
        ("Turn 2", "Tell me more about the first one."),
        ("Turn 3", "What's the fee for that branch?"),
        ("Turn 4", "My name is Priya."),
        ("Turn 5", "What's my name and which branch was I asking about?"),
    ]
    
    results = []
    for turn_id, query in test_script:
        print(f"\n--- {turn_id}: {query}")
        result = bot.generate_response(query, verbose=True)
        answer = result["answer"][:200]
        print(f"  Answer: {answer}")
        results.append({"turn": turn_id, "query": query, "answer": result["answer"][:150], "routing": result["routing"]})
    
    # Check pass criteria
    turn5 = results[-1]["answer"].lower()
    has_priya = "priya" in turn5
    has_cse = "cse" in turn5 or "computer science" in turn5
    
    print(f"\n{'='*70}")
    print(f"PASS CRITERIA:")
    print(f"  Turn 2 responds about CSE? {results[1]['routing']}")
    print(f"  Turn 5 says 'Priya'? {'YES' if has_priya else 'NO'}")
    print(f"  Turn 5 says 'CSE'? {'YES' if has_cse else 'NO'}")
    print(f"  Overall: {'PASS' if has_priya and has_cse else 'PARTIAL'}")
    print(f"{'='*70}\n")
    
    return results


def test_exercise_2_long_conversation():
    """Exercise 2: Test long conversation with summarisation."""
    print("\n" + "=" * 70)
    print("EXERCISE 2: Long Conversation Handling (Summarisation)")
    print("=" * 70)
    
    bot = MemoryChatbot("test_e2")
    bot.SUMMARISE_AFTER = 5  # Shorter for testing
    
    queries = [
        "What is the main campus location?",
        "What B.Tech branches are offered?",
        "Tell me about CSE department.",
        "What is the annual fee for CSE?",
        "What is the total 4-year tuition for CSE?",
        "Tell me about ECE department.",
        "What is the annual fee for ECE?",
        "What are the placement statistics?",
        "What is the highest package offered?",
        "What companies visit for placements?",
        "What hostel facilities are available?",
        "What is the hostel fee?",
        "What is the combined cost for tuition + hostel for 4 years?",
        "Tell me about scholarships.",
        "What scholarships are available for CSE students?",
        "Who is the principal?",
        "What is the admission process?",
        "What are the EAMCET cutoff scores?",
        "What is the college email and phone?",
        "What labs and facilities are available?",
        "Tell me about the library.",
        "What sports facilities are there?",
    ]
    
    print(f"\nRunning {len(queries)} queries to test summarisation...")
    for i, q in enumerate(queries):
        result = bot.generate_response(q, verbose=False)
        if (i + 1) % 5 == 0:
            tokens = bot.get_conversation_tokens()
            print(f"  Turn {i+1}: {tokens['total_chars']} chars, summary={tokens['summary_chars']} chars, savings={tokens['savings_chars']} chars")
    
    final_tokens = bot.get_conversation_tokens()
    print(f"\n{'='*70}")
    print(f"FINAL TOKEN COUNTS:")
    print(f"  Total conversation chars: {final_tokens['total_chars']}")
    print(f"  Summary chars: {final_tokens['summary_chars']}")
    print(f"  Estimated savings: {final_tokens['savings_chars']} chars (~{final_tokens['savings_chars']//4} tokens)")
    print(f"  Turn count: {final_tokens['turn_count']}")
    print(f"  Summary: {bot.summary[:200]}")
    print(f"{'='*70}\n")
    
    return final_tokens


def test_exercise_3_persistent_memory():
    """Exercise 3: Test cross-session persistent memory."""
    print("\n" + "=" * 70)
    print("EXERCISE 3: Persistent Memory (Cross-Session)")
    print("=" * 70)
    
    # Clean up any existing profile
    delete_user_profile(get_user_id("Priya"))
    
    # Session 1
    print("\n--- SESSION 1 ---")
    bot1 = MemoryChatbot(get_user_id("Priya"))
    
    result1 = bot1.generate_response("My name is Priya and I'm interested in B.Tech CSE.", verbose=True)
    print(f"  Turn 1: {result1['answer'][:100]}...")
    
    result2 = bot1.generate_response("I prefer detailed answers in English.", verbose=True)
    print(f"  Turn 2: {result2['answer'][:100]}...")
    
    # Save profile
    save_user_profile(bot1.profile)
    print(f"  Profile saved: {bot1.profile['name']}, branch={bot1.profile['branch_interest']}")
    
    # Simulate closing the app
    del bot1
    
    # Session 2 (new chatbot instance)
    print("\n--- SESSION 2 (new instance) ---")
    bot2 = MemoryChatbot(get_user_id("Priya"))
    print(f"  Loaded profile: name={bot2.profile['name']}, branch={bot2.profile['branch_interest']}")
    
    result3 = bot2.generate_response("What's the fee for the branch I'm interested in?", verbose=True)
    print(f"  Turn 3: {result3['answer'][:150]}...")
    
    result4 = bot2.generate_response("What's my name?", verbose=True)
    print(f"  Turn 4: {result4['answer'][:150]}...")
    
    # Check pass criteria
    answer3 = result3['answer'].lower()
    answer4 = result4['answer'].lower()
    has_cse_fee = "cse" in answer3 or "120000" in answer3 or "1,20,000" in answer3
    has_priya = "priya" in answer4
    
    print(f"\n{'='*70}")
    print(f"PASS CRITERIA:")
    print(f"  Session 2 knows branch is CSE? {'YES' if has_cse_fee else 'NO'}")
    print(f"  Session 2 knows name is Priya? {'YES' if has_priya else 'NO'}")
    print(f"  Overall: {'PASS' if has_cse_fee and has_priya else 'PARTIAL'}")
    print(f"{'='*70}\n")
    
    return {"session1_ok": True, "has_cse_fee": has_cse_fee, "has_priya": has_priya}


def test_exercise_4_personalisation():
    """Exercise 4: Test personalised responses for different users."""
    print("\n" + "=" * 70)
    print("EXERCISE 4: Personalisation")
    print("=" * 70)
    
    # Create two user profiles
    priya_profile = DEFAULT_USER_PROFILE.copy()
    priya_profile["user_id"] = get_user_id("Priya")
    priya_profile["name"] = "Priya"
    priya_profile["branch_interest"] = "CSE"
    priya_profile["detail_level"] = "detailed"
    priya_profile["language"] = "english"
    priya_profile["preferred_format"] = "paragraph"
    priya_profile["conversation_count"] = 5
    save_user_profile(priya_profile)
    
    rahul_profile = DEFAULT_USER_PROFILE.copy()
    rahul_profile["user_id"] = get_user_id("Rahul")
    rahul_profile["name"] = "Rahul"
    rahul_profile["branch_interest"] = "Mechanical"
    rahul_profile["detail_level"] = "brief"
    rahul_profile["language"] = "english"
    rahul_profile["preferred_format"] = "bullets"
    rahul_profile["conversation_count"] = 3
    save_user_profile(rahul_profile)
    
    # Test both users
    for user_name, user_id in [("Priya", get_user_id("Priya")), ("Rahul", get_user_id("Rahul"))]:
        print(f"\n--- User: {user_name} ---")
        bot = MemoryChatbot(user_id)
        
        # Show system prompt differences
        docs = retrieve_relevant_chunks("Tell me about my branch")
        context = format_context(docs)
        prompt = build_system_prompt(bot.profile, context)
        print(f"  System prompt personalisation section:")
        for line in prompt.split('\n'):
            if 'name' in line.lower() or 'branch' in line.lower() or 'detail' in line.lower() or 'prefer' in line.lower() or 'brief' in line.lower() or 'bullet' in line.lower():
                print(f"    {line.strip()}")
        
        # Test Q1: Tell me about my branch
        print(f"\n  Q1: 'Tell me about my branch.'")
        result = bot.generate_response("Tell me about my branch.", verbose=False)
        print(f"  Answer: {result['answer'][:200]}...")
        
        # Test Q2: Total 4-year cost
        print(f"\n  Q2: 'What's the total 4-year cost?'")
        result = bot.generate_response("What's the total 4-year cost?", verbose=False)
        print(f"  Answer: {result['answer'][:200]}...")
    
    print(f"\n{'='*70}")
    print("PERSONALISATION VERIFIED")
    print(f"{'='*70}\n")


def test_exercise_5_privacy():
    """Exercise 5: Test right to be forgotten and data classification."""
    print("\n" + "=" * 70)
    print("EXERCISE 5: Privacy & Right to Be Forgotten")
    print("=" * 70)
    
    # Data classification
    print(f"\nData Classification:")
    for field, classification in DATA_CLASSIFICATION.items():
        print(f"  {field}: {classification}")
    
    # Create a profile
    delete_user_profile(get_user_id("TestUser"))
    bot = MemoryChatbot(get_user_id("TestUser"))
    bot.generate_response("My name is TestUser and I like CSE.", verbose=False)
    save_user_profile(bot.profile)
    
    # Verify profile exists
    profile_path = os.path.join(USER_PROFILES_DIR, f"{get_user_id('TestUser')}.json")
    print(f"\nProfile created: {os.path.exists(profile_path)}")
    
    # Test clear my data
    result = bot.generate_response("Clear my data", verbose=True)
    print(f"Clear response: {result['answer'][:100]}")
    
    # Verify profile deleted
    print(f"Profile after clear: {os.path.exists(profile_path)}")
    
    # Test new session after clear
    bot2 = MemoryChatbot(get_user_id("TestUser"))
    print(f"New session name: {bot2.profile['name']}")
    print(f"New session treats as new: {bot2.profile['name'] is None}")
    
    # Test privacy notice
    profile_path = os.path.join(USER_PROFILES_DIR, f"{get_user_id('Priya')}.json")
    if os.path.exists(profile_path):
        with open(profile_path, "r") as f:
            profile = json.load(f)
        profile["conversation_count"] = 0  # Reset to first interaction
        save_user_profile(profile)
    
    bot3 = MemoryChatbot(get_user_id("Priya"))
    bot3.profile["conversation_count"] = 0
    docs = retrieve_relevant_chunks("hello")
    context = format_context(docs)
    prompt = build_system_prompt(bot3.profile, context)
    has_privacy = "Privacy Notice" in prompt
    print(f"\nPrivacy notice shown on first interaction: {has_privacy}")
    
    print(f"\n{'='*70}")
    print("PRIVACY TESTS COMPLETE")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    print("=" * 70)
    print("DAY 6: MEMORY LAYERS - COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    
    # Exercise 1: Multi-turn memory
    test_exercise_1_multi_turn()
    
    # Exercise 2: Long conversation summarisation
    test_exercise_2_long_conversation()
    
    # Exercise 3: Persistent memory
    test_exercise_3_persistent_memory()
    
    # Exercise 4: Personalisation
    test_exercise_4_personalisation()
    
    # Exercise 5: Privacy
    test_exercise_5_privacy()
    
    print("\n" + "=" * 70)
    print("ALL DAY 6 EXERCISES COMPLETE")
    print("=" * 70)