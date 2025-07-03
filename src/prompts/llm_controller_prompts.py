"""
LLM Controller Prompts - FIXED to prevent over-detection of memory queries
"""

def get_controller_prompt_template() -> str:
    """
    ULTRA-STRICT controller prompt - prevents false memory detection
    """
    return """You are a smart retrieval controller for a RAG system with conversation memory.

CRITICAL RULE: MEMORY_PRIORITY is ONLY for explicit conversation recall requests. Default to NORMAL_SEARCH.

USER QUESTION: {query}
PERSONALITY: {personality}
CONVERSATION HISTORY: {memory_context}

**STRICT MEMORY-ONLY QUERIES** (Use MEMORY_PRIORITY):
Must contain these EXACT phrases:
- "remind me" + conversation reference
- "what did we discuss/talk about"  
- "summarize our conversation"
- "recall our discussion"
- "what topics have we covered"
- "what was that thing you mentioned"

**NEVER MEMORY_PRIORITY for:**
- Simple greetings: "hello", "hi", "how are you"
- Technical questions: "what is X", "how to Y", "explain Z"
- Requests for information: "tell me about", "show me"
- ANY question that could want fresh information

**NORMAL_SEARCH (DEFAULT for almost everything):**
- ALL greetings and casual conversation
- ALL technical questions (even if repeated)
- ALL "what is..." questions
- ALL "how to..." questions
- ALL "explain..." requests
- Information requests

**CONTEXT_SEARCH (Building on previous):**
- Clear follow-ups with pronouns: "what about that", "how does it work"
- Comparative questions: "how does that compare"

**DECISION PROCESS:**
1. Is this a simple greeting? → NORMAL_SEARCH
2. Does query contain EXACT memory keywords? → Check if truly asking for recall
3. Is this asking for information/explanation? → NORMAL_SEARCH
4. When in doubt → NORMAL_SEARCH

**EXAMPLES:**

Query: "Hello, how are you?"
QUERY_TYPE: NORMAL_SEARCH
REASONING: Simple greeting, not a memory request

Query: "What is Docker?"
QUERY_TYPE: NORMAL_SEARCH  
REASONING: Information request, not memory recall

Query: "How do I install Python?"
QUERY_TYPE: NORMAL_SEARCH
REASONING: Technical question wanting fresh guidance

Query: "What is AI?"
QUERY_TYPE: NORMAL_SEARCH
REASONING: Definition request, not conversation recall

Query: "remind me what we discussed about Docker"
QUERY_TYPE: MEMORY_PRIORITY
REASONING: Contains "remind me" + conversation reference

Query: "what did we talk about earlier?"
QUERY_TYPE: MEMORY_PRIORITY  
REASONING: Contains "what did we talk about" - explicit memory request

OUTPUT FORMAT:
QUERY_TYPE: [MEMORY_PRIORITY|CONTEXT_SEARCH|NORMAL_SEARCH]
SEARCH_TERMS: [specific terms OR "use_memory" if memory priority]
CONTENT_TYPE: [tutorial/explanation/memory_reference/etc]
AVOID_BIAS: [yes/no]
FOCUS_AREA: [domain or "conversation_history"]
REASONING: [explain your decision]"""


def analyze_memory_vs_retrieval_intent(query: str) -> dict:
    """
    ULTRA-STRICT analysis to prevent false memory detection
    """
    query_lower = query.lower().strip()
    
    # VERY STRICT memory indicators - must be explicit
    strict_memory_phrases = [
        "remind me",
        "what did we discuss",
        "what did we talk about", 
        "what were we talking about",
        "summarize our conversation",
        "recall our discussion",
        "what topics have we covered",
        "what was that thing you mentioned"
    ]
    
    # Immediate disqualifiers (never memory)
    greeting_patterns = [
        "hello", "hi", "hey", "good morning", "good afternoon", 
        "how are you", "what's up", "greetings"
    ]
    
    info_request_patterns = [
        "what is", "what's", "tell me about", "explain", "how to",
        "how do i", "show me", "describe", "define"
    ]
    
    analysis = {
        "intent": "normal_search",
        "confidence": "high",
        "indicators": [],
        "reasoning": ""
    }
    
    # Check if it's a greeting - NEVER memory
    if any(greeting in query_lower for greeting in greeting_patterns):
        analysis["reasoning"] = "Greeting detected - not a memory request"
        return analysis
    
    # Check if it's an information request - NEVER memory  
    if any(pattern in query_lower for pattern in info_request_patterns):
        analysis["reasoning"] = "Information request detected - not memory recall"
        return analysis
    
    # Only check for memory if not a greeting or info request
    memory_found = [phrase for phrase in strict_memory_phrases if phrase in query_lower]
    if memory_found:
        analysis["intent"] = "memory_priority"
        analysis["indicators"] = memory_found
        analysis["reasoning"] = f"Explicit memory request: {memory_found[0]}"
        return analysis
    
    # Context pronouns (but not for simple questions)
    context_pronouns = ["that one", "which one", "the other", "what about that"]
    pronouns_found = [p for p in context_pronouns if p in query_lower]
    if pronouns_found and not any(pattern in query_lower for pattern in info_request_patterns):
        analysis["intent"] = "context_search"
        analysis["confidence"] = "medium"
        analysis["indicators"] = pronouns_found
        analysis["reasoning"] = f"Context pronouns detected: {pronouns_found}"
        return analysis
    
    # Default to normal search with high confidence
    analysis["reasoning"] = "No explicit memory indicators - treating as fresh information request"
    return analysis


def test_controller_analysis():
    """Test the FIXED memory analysis logic"""
    test_cases = [
        # Should be NORMAL_SEARCH
        ("Hello, how are you?", "normal_search"),
        ("What is Docker?", "normal_search"), 
        ("How do I install Python?", "normal_search"),
        ("Tell me about AI", "normal_search"),
        ("Explain machine learning", "normal_search"),
        ("What's the difference between X and Y?", "normal_search"),
        
        # Should be MEMORY_PRIORITY
        ("remind me what we discussed about Docker", "memory_priority"),
        ("what did we talk about earlier?", "memory_priority"),
        ("summarize our conversation", "memory_priority"),
        
        # Should be CONTEXT_SEARCH
        ("what about that other option", "context_search"),
        ("how does that one compare", "context_search")
    ]
    
    print("🧪 Testing FIXED Controller Analysis:")
    print("=" * 50)
    
    correct = 0
    total = len(test_cases)
    
    for query, expected in test_cases:
        result = analyze_memory_vs_retrieval_intent(query)
        actual = result['intent']
        status = "✅" if actual == expected else "❌"
        
        print(f"{status} '{query}'")
        print(f"   Expected: {expected} | Actual: {actual}")
        print(f"   Reasoning: {result['reasoning']}")
        
        if actual == expected:
            correct += 1
        print()
    
    print(f"Accuracy: {correct}/{total} ({correct/total*100:.1f}%)")


if __name__ == "__main__":
    # test_controller_analysis()
    pass  # Run tests if needed