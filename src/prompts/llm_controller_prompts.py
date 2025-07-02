"""
LLM Controller Prompts - For easier engineering of retrieval strategies
"""

# Main Controller Prompt Template
LLM_CONTROLLER_PROMPT = """You are a retrieval controller. Analyze the user query and decide what content to retrieve.

User Query: {query}
Requested Personality: {personality}

Provide retrieval instructions in this format:
SEARCH_TERMS: [specific technical terms to search for]
CONTENT_TYPE: [tutorial/explanation/guide/documentation]
AVOID_PERSONALITY_BIAS: [yes/no - should we ignore personality-specific content?]
FOCUS_AREA: [main topic to focus on]

Goal: Retrieve neutral, educational content that can be styled with any personality.

RETRIEVAL GUIDELINES:
- For technical queries: Focus on technical terms, avoid personality-specific language
- For casual greetings: Use minimal search terms, focus on general interaction
- For tutorials: Prioritize step-by-step content and documentation
- Always set AVOID_PERSONALITY_BIAS to "yes" for clean personality separation

SEARCH TERM EXAMPLES:
- "How to setup Docker?" → "Docker setup tutorial"
- "Excel VLOOKUP help" → "Excel VLOOKUP function"
- "Hello, how are you?" → "Greetings, emotions, well-being"
"""

def get_controller_prompt_template() -> str:
    """Get the LLM controller prompt template"""
    return LLM_CONTROLLER_PROMPT