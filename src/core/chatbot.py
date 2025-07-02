"""
NetworkChuck Chatbot - fixed personality handling
"""

from ..chains.llm_controlled_rag import LLMControlledRAG


class NetworkChuckChatbot:
    """
    Main chatbot controller - clean direct RAG usage
    """
    
    def __init__(self):
        self.rag = LLMControlledRAG()
        print("✅ NetworkChuck Chatbot ready with direct RAG!")
    
    def chat_response(self, message: str, history: list, personality: str = None) -> str:
        """
        Generate chat response - ALWAYS use personality parameter
        """
        try:
            # Use the personality parameter directly (from UI dropdown)
            selected_personality = personality or "NetworkChuck"
            
            print(f"🎭 DEBUG: Chatbot received personality: {selected_personality}")
            
            # Direct RAG call with explicit personality
            response = self.rag.invoke({
                "question": message,
                "personality": selected_personality.lower()
            })
            
            return response
                
        except Exception as e:
            return f"Sorry, I encountered an error: {str(e)}"
    
    def set_personality(self, personality: str):
        """Set the current personality (not used in this approach)"""
        pass  # Not needed since we use the parameter directly