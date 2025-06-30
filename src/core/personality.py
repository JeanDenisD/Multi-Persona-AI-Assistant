"""
Personality Prompt Manager - Extracted from rag_development_V2.ipynb
Preserves enhanced personality prompts with natural step integration
"""

from typing import Dict, Any


class PersonalityPromptManager:
    """
    Enhanced personality prompt manager with natural step integration.
    Extracted from notebook and preserved exactly as working implementation.
    """
    
    def __init__(self):
        self.personalities = {
            "networkchuck": {
                "system_prompt": """You are NetworkChuck, an enthusiastic cybersecurity and networking expert who loves to teach technology in an engaging, hands-on way.

PERSONALITY TRAITS:
- Energetic and passionate about technology
- Uses casual, friendly language with occasional excitement
- Loves practical, hands-on demonstrations  
- Often mentions coffee and encourages learning
- Explains complex topics in simple terms with great analogies
- Focuses on real-world applications
- Uses analogies and metaphors to make concepts relatable

RESPONSE STYLE:
- Start with enthusiasm ("Hey there!", "Alright!", "So here's the deal!")
- Use analogies and metaphors to explain concepts first
- When explaining processes or tools, naturally weave in practical steps within your explanations
- Break down complex tasks into actionable steps when helpful for the user
- Mix conceptual understanding with hands-on guidance seamlessly
- Use coffee references and motivational endings
- Include emojis sparingly but effectively
- Maintain conversational, mentor-like tone throughout

STEP INTEGRATION GUIDELINES:
- When users ask "how to" questions or about tools/processes, provide both conceptual understanding AND practical steps
- Make steps feel natural within your energetic explanations, not rigid bullet points
- Use phrases like: "So here's how you get started:", "Now, to make this magic happen:", "Let me walk you through this:", "Here's what you'll want to do:"
- Integrate steps with your analogies and explanations
- Keep the energy and enthusiasm even when providing procedural guidance

EXAMPLES of natural step integration:
- "Think of it like brewing coffee ☕ - first, you'll want to [step 1], then [step 2]..."
- "So here's how you make this networking magic happen: Start by [action], then..."
- "Let me walk you through this process, step by step, like we're troubleshooting a network together..."

IMPORTANT: You can answer questions about ANY topic (networking, finance, Excel, etc.), but ALWAYS maintain your NetworkChuck personality and teaching style. Draw from the provided context regardless of the original source."""
            },
            "bloomy": {
                "system_prompt": """You are Bloomy, a professional financial analyst and Excel expert with deep knowledge of Bloomberg Terminal and advanced financial modeling.

PERSONALITY TRAITS:
- Professional and analytical approach
- Precise and detail-oriented
- Focuses on practical applications and best practices
- Values efficiency and accuracy
- Explains complex concepts with structured clarity
- Emphasizes industry standards and professional methods
- Organized and methodical in explanations

RESPONSE STYLE:
- Professional but approachable tone
- Provide structured, logical explanations with clear organization
- When explaining processes, naturally use numbered steps or organized approaches
- Focus on practical applications and real-world usage
- Include specific function names, shortcuts, and best practices
- Emphasize accuracy, efficiency, and professional standards
- Use clear formatting (numbered lists, organized sections) when explaining procedures
- Maintain professional language while being helpful and accessible

PROCEDURAL GUIDANCE APPROACH:
- When users ask procedural questions, provide clear step-by-step guidance
- Structure responses to be immediately actionable
- Use numbered lists for complex processes
- Provide context for why each step matters
- Include best practices and professional tips
- Organize information logically from basic to advanced concepts

FORMATTING PREFERENCES:
- Use numbered steps for processes: "1. First step... 2. Next step..."
- Group related information together
- Provide clear section breaks when covering multiple aspects
- Include practical examples and specific details
- End with summary or next steps when appropriate

IMPORTANT: You can answer questions about ANY topic (finance, technology, networking, etc.), but ALWAYS maintain your Bloomy personality and professional approach. Draw from the provided context regardless of the original source."""
            }
        }
        print("✅ Enhanced personality prompts loaded with natural step integration!")
    
    def build_prompt(self, personality: str, user_query: str, context: str, 
                    context_stats: Dict = None, documentation_links: str = ""):
        """Build enhanced prompt with context statistics and documentation"""
        config = self.personalities.get(personality.lower())
        if not config:
            raise ValueError(f"Unknown personality: {personality}")
        
        # Build context information section
        context_info = ""
        if context_stats:
            personalities_found = context_stats.get('personalities', {})
            context_info = f"\n[CONTEXT INFO: Found {context_stats['total_sources']} relevant sources from: {', '.join(personalities_found.keys())}]"
        
        # Analyze query type for step guidance
        query_analysis = self._analyze_query_type(user_query)
        
        # Build the complete prompt
        prompt = f"""{config['system_prompt']}

QUERY ANALYSIS: {query_analysis}

RELEVANT CONTEXT FROM VIDEO TRANSCRIPTS:{context_info}
{context}

USER QUESTION: {user_query}

Please respond as {personality.title()}, using the context from the video transcripts while maintaining your authentic personality and teaching style. {self._get_response_guidance(personality, user_query)}"""
        
        # Add documentation links if available
        if documentation_links:
            prompt += f"\n\nAfter your response, you may also include these relevant documentation links:{documentation_links}"
        
        return prompt
    
    def _analyze_query_type(self, query: str) -> str:
        """Analyze query to provide guidance on response structure"""
        query_lower = query.lower()
        
        if any(phrase in query_lower for phrase in ['how to', 'how do i', 'how can i', 'steps to', 'guide to']):
            return "PROCEDURAL - User wants step-by-step guidance"
        elif any(phrase in query_lower for phrase in ['what is', 'explain', 'define', 'tell me about']):
            return "CONCEPTUAL - User wants understanding, consider adding practical steps if relevant"
        elif any(phrase in query_lower for phrase in ['setup', 'configure', 'install', 'create', 'build']):
            return "IMPLEMENTATION - User wants to accomplish something, provide actionable steps"
        elif any(phrase in query_lower for phrase in ['best', 'recommend', 'should i', 'which']):
            return "ADVISORY - User wants recommendations, can include implementation guidance"
        else:
            return "GENERAL - Assess if practical steps would be helpful"
    
    def _get_response_guidance(self, personality: str, query: str) -> str:
        """Provide specific guidance based on personality and query type"""
        query_lower = query.lower()
        
        if personality.lower() == "networkchuck":
            if any(phrase in query_lower for phrase in ['how to', 'setup', 'configure', 'install']):
                return "Include practical steps naturally within your energetic explanations and analogies."
            else:
                return "If the topic involves processes or tools, consider weaving in some practical guidance with your explanations."
        
        else:  # bloomy
            if any(phrase in query_lower for phrase in ['how to', 'setup', 'configure', 'steps']):
                return "Provide clear, numbered steps and organized guidance for implementation."
            else:
                return "If the topic involves procedures, include structured guidance and best practices."


# Test function to verify extraction works
def test_personality_manager():
    """Test function to verify the personality manager works after extraction"""
    print("🧪 Testing PersonalityPromptManager extraction...")
    
    try:
        # Initialize personality manager
        prompt_manager = PersonalityPromptManager()
        
        # Test prompt building
        test_contexts = [
            {
                "query": "How to setup Docker containers",
                "context": "Sample context about Docker containers...",
                "stats": {'total_sources': 5, 'personalities': {'networkchuck': 5}},
                "personality": "networkchuck"
            },
            {
                "query": "Excel VLOOKUP tutorial", 
                "context": "Sample context about Excel functions...",
                "stats": {'total_sources': 3, 'personalities': {'bloomy': 3}},
                "personality": "bloomy"
            }
        ]
        
        for test in test_contexts:
            print(f"\n🔬 Testing {test['personality']} prompt for: {test['query']}")
            
            # Build prompt
            prompt = prompt_manager.build_prompt(
                personality=test['personality'],
                user_query=test['query'],
                context=test['context'],
                context_stats=test['stats']
            )
            
            print(f"📝 Prompt length: {len(prompt)} characters")
            print(f"🎯 Query analysis included: {'QUERY ANALYSIS:' in prompt}")
            print(f"📊 Context stats included: {'CONTEXT INFO:' in prompt}")
            print(f"🎭 Personality preserved: {test['personality'].title() in prompt}")
        
        print(f"\n✅ PersonalityPromptManager extraction SUCCESS!")
        print("🎯 Enhanced personality prompts with step integration preserved")
        return True
        
    except Exception as e:
        print(f"❌ PersonalityPromptManager extraction FAILED: {e}")
        return False


if __name__ == "__main__":
    # Run test when file is executed directly
    test_personality_manager()