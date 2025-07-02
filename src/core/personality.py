"""
Personality Prompt Manager - Now uses extracted prompts
"""

from typing import Dict, Any
from ..prompts.personality_prompts import (
    get_personality_prompt, 
    analyze_query_type, 
    get_response_guidance
)


class PersonalityPromptManager:
    """
    Enhanced personality prompt manager using extracted prompts
    """
    
    def __init__(self):
        print("✅ Enhanced personality prompts loaded from external files!")
    
    def build_prompt(self, personality: str, user_query: str, context: str, 
                    context_stats: Dict = None, documentation_links: str = ""):
        """Build enhanced prompt using extracted personality prompts"""
        
        # Get the personality system prompt
        system_prompt = get_personality_prompt(personality)
        
        # Build context information section
        context_info = ""
        if context_stats:
            personalities_found = context_stats.get('personalities', {})
            context_info = f"\n[CONTEXT INFO: Found {context_stats['total_sources']} relevant sources from: {', '.join(personalities_found.keys())}]"
        
        # Analyze query type for step guidance
        query_analysis = analyze_query_type(user_query)
        
        # Get response guidance
        response_guidance = get_response_guidance(personality, user_query)
        
        # Build the complete prompt
        prompt = f"""{system_prompt}

QUERY ANALYSIS: {query_analysis}

RELEVANT CONTEXT FROM VIDEO TRANSCRIPTS:{context_info}
{context}

USER QUESTION: {user_query}

Please respond as {personality.title()}, using the context from the video transcripts while maintaining your authentic personality and teaching style. {response_guidance}"""
        
        # Add documentation links if available
        if documentation_links:
            prompt += f"\n\nAfter your response, you may also include these relevant documentation links:{documentation_links}"
        
        return prompt