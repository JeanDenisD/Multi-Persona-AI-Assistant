"""
LLM Controller Prompts - For easier engineering of retrieval strategies
SIMPLE FIX: Just replace the get_controller_prompt_template() function
"""

def get_controller_prompt_template() -> str:
    """
    Fixed controller prompt - less aggressive about memory classification
    """
    return """You are a smart retrieval controller for a RAG system with conversation memory.

CRITICAL: Only use MEMORY_PRIORITY for EXPLICIT memory requests, not repeated questions.

USER QUESTION: {query}
PERSONALITY: {personality}
CONVERSATION HISTORY: {memory_context}

MEMORY-BASED QUERIES (Use MEMORY_PRIORITY - very strict):
- "remind me what we discussed"
- "what did we talk about"
- "can you summarize our conversation"
- "what was that thing you mentioned"
- "recall our discussion"
- "what topics have we covered"

FRESH INFORMATION QUERIES (Use NORMAL_SEARCH - default for most questions):
- "how to do X" (even if asked before)
- "tell me about Y" (even if discussed previously) 
- "what is Z" (even if covered earlier)
- "explain the difference between A and B" (even if repeated)
- ANY technical question that could benefit from a fresh perspective

CONTEXT QUERIES (Use CONTEXT_SEARCH - builds on previous):
- "what about that other option"
- "how does that compare to what we discussed"
- Clear follow-up questions with pronouns

DECISION LOGIC:
1. If user wants to recall/reference previous conversation → MEMORY_PRIORITY
2. If user asks the SAME technical question but wants a FRESH perspective → NORMAL_SEARCH  
3. If user asks follow-up building on previous topic → CONTEXT_SEARCH

IMPORTANT: Repeated questions are usually users wanting to:
- Get a different perspective
- Test different personalities
- Get a fresh explanation  
- Compare approaches

Therefore, default to NORMAL_SEARCH unless explicitly asking for memory recall.

OUTPUT FORMAT:
QUERY_TYPE: [MEMORY_PRIORITY|CONTEXT_SEARCH|NORMAL_SEARCH]
SEARCH_TERMS: [specific terms OR "use_memory" if memory priority]
CONTENT_TYPE: [tutorial/explanation/memory_reference/etc]
AVOID_BIAS: [yes/no]
FOCUS_AREA: [domain or "conversation_history"]
REASONING: [explain your decision]

EXAMPLES:
Query: "remind me what we discussed about Docker"
QUERY_TYPE: MEMORY_PRIORITY
SEARCH_TERMS: use_memory
REASONING: User explicitly wants to recall previous conversation

Query: "What's the difference between VLOOKUP and INDEX-MATCH?" (asked before)
QUERY_TYPE: NORMAL_SEARCH
SEARCH_TERMS: VLOOKUP INDEX-MATCH difference Excel
REASONING: Technical question that benefits from fresh explanation, even if asked before

Query: "How do I install Docker?" (asked multiple times)
QUERY_TYPE: NORMAL_SEARCH
SEARCH_TERMS: Docker installation steps  
REASONING: User wants fresh installation guidance, not memory recall"""


def analyze_memory_vs_retrieval_intent(query: str) -> dict:
    """
    Analyze whether query wants memory recall or new information
    """
    query_lower = query.lower().strip()
    
    # Strong memory indicators
    memory_keywords = [
        "remind me", "what did we", "what were we", "earlier you", "you mentioned",
        "we discussed", "we talked", "you said", "before you", "previous",
        "our conversation", "what was that", "that thing", "recall", "remember"
    ]
    
    # Pronoun references that need context
    context_pronouns = ["that", "it", "this", "those", "which one", "the one"]
    
    # Follow-up question indicators  
    followup_keywords = [
        "what about", "how about", "what else", "next step", "after that",
        "in addition", "also", "furthermore", "besides", "alternatively"
    ]
    
    analysis = {
        "intent": "normal_search",
        "confidence": "low",
        "indicators": [],
        "reasoning": ""
    }
    
    # Check for memory intent
    memory_found = [kw for kw in memory_keywords if kw in query_lower]
    if memory_found:
        analysis["intent"] = "memory_priority"
        analysis["confidence"] = "high"
        analysis["indicators"] = memory_found
        analysis["reasoning"] = f"Contains explicit memory keywords: {memory_found}"
        return analysis
    
    # Check for context pronouns
    pronouns_found = [p for p in context_pronouns if f" {p} " in f" {query_lower} "]
    if pronouns_found:
        analysis["intent"] = "context_search"
        analysis["confidence"] = "medium"
        analysis["indicators"] = pronouns_found
        analysis["reasoning"] = f"Contains pronouns needing context: {pronouns_found}"
        return analysis
    
    # Check for follow-up questions
    followup_found = [kw for kw in followup_keywords if kw in query_lower]
    if followup_found:
        analysis["intent"] = "context_search" 
        analysis["confidence"] = "medium"
        analysis["indicators"] = followup_found
        analysis["reasoning"] = f"Follow-up question indicators: {followup_found}"
        return analysis
    
    # Default to normal search
    analysis["reasoning"] = "No memory/context indicators found, treating as new query"
    return analysis


# Test function
def test_controller_analysis():
    """Test the memory analysis logic"""
    test_cases = [
        "remind me what we discussed about Docker",
        "what was that thing you mentioned?", 
        "what about VirtualBox instead?",
        "how do I setup Kubernetes?",
        "can you tell me more about that?",
        "what did we talk about earlier?"
    ]
    
    print("🧪 Testing Controller Memory Analysis:")
    for query in test_cases:
        result = analyze_memory_vs_retrieval_intent(query)
        print(f"'{query}' → {result['intent']} ({result['confidence']})")
        print(f"   Reasoning: {result['reasoning']}")
        print()


if __name__ == "__main__":
    test_controller_analysis()