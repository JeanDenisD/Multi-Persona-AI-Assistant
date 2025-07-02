"""
NetworkChuck Chatbot
"""

from ..chains.llm_controlled_rag import LLMControlledRAG


class NetworkChuckChatbot:
    """
    Main chatbot controller with memory support
    """
    
    def __init__(self, memory_window_size: int = 10):
        self.rag = LLMControlledRAG(memory_window_size=memory_window_size)
        print(f"✅ NetworkChuck Chatbot ready with memory (window: {memory_window_size})!")
    
    def chat_response(self, message: str, history: list, personality: str = None) -> str:
        """
        Generate chat response with memory integration
        
        Args:
            message: Current user message
            history: Gradio chat history [[user_msg, bot_msg], ...]
            personality: Selected personality from UI dropdown
        """
        try:
            # Use the personality parameter directly (from UI dropdown)
            selected_personality = personality or "networkchuck"
            
            print(f"🎭 DEBUG: Chatbot received personality: {selected_personality}")
            print(f"🧠 DEBUG: History length: {len(history)} turns")
            
            # RAG call with memory integration
            response = self.rag.invoke({
                "question": message,
                "personality": selected_personality.lower(),
                "history": history  # Pass Gradio history to memory system
            })
            
            return response
                
        except Exception as e:
            print(f"❌ Error in chat_response: {str(e)}")
            return f"Sorry, I encountered an error: {str(e)}"
    
    def get_memory_info(self) -> dict:
        """Get information about current memory state"""
        try:
            return self.rag.get_memory_summary()
        except Exception as e:
            return {"error": str(e), "memory_active": False}
    
    def clear_conversation_memory(self):
        """Clear the conversation memory"""
        try:
            self.rag.clear_memory()
            print("🧠 Conversation memory cleared")
            return True
        except Exception as e:
            print(f"❌ Error clearing memory: {str(e)}")
            return False
    
    def set_personality(self, personality: str):
        """Set the current personality (legacy method - not used in current approach)"""
        pass  # Not needed since we use the parameter directly


class MemoryDebugger:
    """
    Helper class for debugging memory integration
    """
    
    @staticmethod
    def test_memory_integration(chatbot: NetworkChuckChatbot):
        """Test the memory integration with sample conversation"""
        print("🧪 Testing Memory Integration...")
        
        # Sample conversation history (Gradio format)
        test_history = [
            ["How do I install Docker?", "Great question! Docker is a containerization platform..."],
            ["What about Docker Compose?", "Docker Compose is perfect for multi-container applications..."],
        ]
        
        # Test with memory
        response1 = chatbot.chat_response(
            "Can you remind me what we discussed about containers?", 
            test_history, 
            "networkchuck"
        )
        
        print("📝 Memory Test Response:")
        print(response1[:200] + "...")
        
        # Get memory info
        memory_info = chatbot.get_memory_info()
        print(f"🧠 Memory Info: {memory_info}")
        
        # Test memory clearing
        chatbot.clear_conversation_memory()
        memory_info_after = chatbot.get_memory_info()
        print(f"🧠 Memory After Clear: {memory_info_after}")
        
        return True


# Usage example for testing
def test_chatbot_memory():
    """Test function to verify memory integration"""
    print("🚀 Testing NetworkChuck Chatbot with Memory...")
    
    try:
        # Initialize chatbot with memory
        chatbot = NetworkChuckChatbot(memory_window_size=5)
        
        # Run memory integration test
        debugger = MemoryDebugger()
        success = debugger.test_memory_integration(chatbot)
        
        if success:
            print("✅ Memory Integration Test PASSED!")
        else:
            print("❌ Memory Integration Test FAILED!")
            
        return success
        
    except Exception as e:
        print(f"❌ Chatbot Memory Test FAILED: {e}")
        return False


if __name__ == "__main__":
    # Run test when file is executed directly
    test_chatbot_memory()