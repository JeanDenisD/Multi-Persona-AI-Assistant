"""
Simplified NetworkChuck Chatbot - Enhanced memory with GPT-4o-mini
Removes aggressive controller, lets LLM decide naturally
"""

import os
from typing import List, Dict, Any

# Import the simplified RAG system instead of the complex one
from ..chains.simplified_rag import SimplifiedRAG
from ..utils.voice_cleaner import clean_text_for_voice, extract_voice_content


class NetworkChuckChatbot:
    """
    Simplified chatbot using enhanced memory and GPT-4 reasoning
    """
    
    def __init__(self, max_turns: int = 20):
        """Initialize with enhanced memory (20 turns + summarization)"""
        # Use simplified RAG system with GPT-4o-mini
        self.rag_system = SimplifiedRAG(max_turns=max_turns)
        
        print(f"✅ NetworkChuck Chatbot ready with enhanced memory ({max_turns} turns)!")
    
    def chat_response(self, message: str, history: List, personality: str, max_documents: int = 5) -> str:
        """Simplified chat response - let GPT-4 handle everything"""
        try:
            print(f"🎭 Chatbot: {personality}")
            print(f"🧠 History: {len(history)} turns")
            print(f"📄 Max docs: {max_documents}")
            
            # Prepare input for simplified RAG
            rag_input = {
                "question": message,
                "personality": personality, 
                "history": history,
                "max_documents": max_documents
            }
            
            # Get response from simplified RAG
            response = self.rag_system.invoke(rag_input)
            
            return response
            
        except Exception as e:
            print(f"❌ Error in chat_response: {e}")
            return f"I encountered an error: {str(e)}"
    
    def chat_response_with_filters(self, message: str, history: List, personality: str, 
                                 content_settings: dict, similarity_threshold: float, 
                                 llm_temperature: float) -> str:
        """Enhanced chat response with filtering"""
        try:
            print(f"🎭 Chatbot: {personality}")
            print(f"🧠 History: {len(history)} turns")
            print(f"🎯 Settings: {content_settings}")
            print(f"📊 Threshold: {similarity_threshold}, Temp: {llm_temperature}")
            
            # Prepare input for simplified RAG with filters
            rag_input = {
                "question": message,
                "personality": personality,
                "history": history,
                "content_settings": content_settings,
                "similarity_threshold": similarity_threshold,
                "llm_temperature": llm_temperature
            }
            
            # Get response from simplified RAG with filters
            response = self.rag_system.invoke_with_filters(rag_input)
            
            return response
            
        except Exception as e:
            print(f"❌ Error in chat_response_with_filters: {e}")
            # Fallback to regular chat response
            try:
                return self.chat_response(
                    message, history, personality, 
                    content_settings.get('max_documents', 5)
                )
            except Exception as fallback_error:
                return f"I encountered an error processing your request. Please try again."
    
    def get_voice_text(self, response: str) -> str:
        """Get cleaned text suitable for voice synthesis"""
        try:
            # Extract main content (remove video/doc sections)
            voice_content = extract_voice_content(response)
            
            # Clean formatting and asterisks for TTS
            cleaned_text = clean_text_for_voice(voice_content)
            
            return cleaned_text
            
        except Exception as e:
            print(f"⚠️ Voice cleaning error: {e}")
            # Fallback: basic cleaning
            return response.replace('*', '').replace('#', '').replace('•', '')
    
    def get_memory_info(self) -> Dict[str, Any]:
        """Get enhanced memory information"""
        try:
            memory_summary = self.rag_system.get_memory_summary()
            
            # Add enhanced memory info
            memory_summary.update({
                "memory_type": "Enhanced with Summarization",
                "max_turns": 20,
                "summary_available": memory_summary.get("has_summary", False)
            })
            
            return memory_summary
            
        except Exception as e:
            return {
                "error": str(e),
                "total_messages": 0,
                "conversation_turns": 0,
                "memory_active": False,
                "memory_type": "Enhanced"
            }
    
    def clear_conversation_memory(self):
        """Clear the enhanced conversation memory"""
        try:
            self.rag_system.clear_memory()
        except Exception as e:
            print(f"❌ Error clearing memory: {e}")
    
    def get_conversation_summary(self) -> str:
        """Get the current conversation summary if available"""
        try:
            if hasattr(self.rag_system.memory, 'conversation_summary'):
                return self.rag_system.memory.conversation_summary
            return "No summary available."
        except Exception as e:
            return f"Error getting summary: {e}"
    
    def analyze_query_complexity(self, query: str) -> Dict[str, Any]:
        """Simple query analysis (much simpler than before)"""
        query_lower = query.lower()
        
        # Simple checks
        is_greeting = any(word in query_lower for word in ['hello', 'hi', 'hey', 'good morning'])
        is_question = '?' in query
        is_memory_request = any(phrase in query_lower for phrase in ['remind me', 'what did we discuss', 'earlier'])
        has_video_name = any(word in query_lower for word in ['video', 'tutorial', 'guide'])
        
        return {
            "query_type": "memory" if is_memory_request else ("greeting" if is_greeting else "general"),
            "is_question": is_question,
            "mentions_video": has_video_name,
            "word_count": len(query.split()),
            "complexity": "simple" if len(query.split()) < 10 else "complex"
        }


# Test functions (simplified)
def test_simplified_chatbot():
    """Test the simplified chatbot system"""
    print("🧪 Testing Simplified Chatbot with Enhanced Memory")
    
    try:
        # Initialize chatbot
        chatbot = NetworkChuckChatbot(max_turns=20)
        
        # Test basic chat
        response = chatbot.chat_response("What is Docker?", [], "networkchuck")
        print(f"✅ Basic chat: {len(response)} chars")
        
        # Test voice cleaning
        voice_text = chatbot.get_voice_text("**Docker** is *amazing*! 🚀 Check this out.")
        print(f"✅ Voice cleaning: '{voice_text}' (no asterisks: {'*' not in voice_text})")
        
        # Test memory info
        memory_info = chatbot.get_memory_info()
        print(f"✅ Memory info: {memory_info.get('memory_type', 'Unknown')}")
        
        # Test query analysis
        analysis = chatbot.analyze_query_complexity("How do I install Docker on Ubuntu?")
        print(f"✅ Query analysis: {analysis['complexity']} {analysis['query_type']}")
        
        print("✅ Simplified chatbot test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Simplified chatbot test failed: {e}")
        return False


if __name__ == "__main__":
    test_simplified_chatbot()