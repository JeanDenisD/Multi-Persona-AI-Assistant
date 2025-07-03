"""
NetworkChuck AI Chatbot - Enhanced with Max Documents Control
Complete chatbot orchestration with memory, personality, and advanced filtering
"""

import os
from typing import List, Dict, Any
from langchain.schema import HumanMessage, AIMessage

from ..chains.llm_controlled_rag import LLMControlledRAG


class NetworkChuckChatbot:
    """
    Main chatbot class that orchestrates all components with max documents support
    """
    
    def __init__(self, memory_window_size: int = 10):
        """Initialize the NetworkChuck AI chatbot"""
        # Initialize the LLM-controlled RAG chain with modern memory
        self.rag_chain = LLMControlledRAG(memory_window_size=memory_window_size)
        
        print(f"✅ NetworkChuck Chatbot ready with memory (window: {memory_window_size})!")
    
    def chat_response(self, message: str, history: List, personality: str, max_documents: int = 5) -> str:
        """
        Regular chat response with max_documents support for backward compatibility
        """
        try:
            print(f"🎭 DEBUG: Chatbot received personality: {personality}")
            print(f"🧠 DEBUG: History length: {len(history)} turns")
            print(f"📄 DEBUG: Max documents: {max_documents}")
            
            # Prepare input for LLM-controlled RAG
            rag_input = {
                "question": message,
                "personality": personality, 
                "history": history,
                "max_documents": max_documents
            }
            
            # Get response from LLM-controlled RAG
            response = self.rag_chain.invoke(rag_input)
            
            return response
            
        except Exception as e:
            print(f"❌ Error in chat_response: {e}")
            return f"I encountered an error: {str(e)}"
    
    def chat_response_with_filters(self, message: str, history: List, personality: str, content_settings: dict, similarity_threshold: float, llm_temperature: float) -> str:
        """
        Enhanced chat response with advanced filtering options including max documents
        """
        try:
            print(f"🎭 DEBUG: Chatbot received personality: {personality}")
            print(f"🧠 DEBUG: History length: {len(history)} turns")
            print(f"🎯 DEBUG: Content settings: {content_settings}")
            print(f"📊 DEBUG: Similarity threshold: {similarity_threshold}, Temperature: {llm_temperature}")
            
            # Extract max_documents from content_settings
            max_documents = content_settings.get('max_documents', 5)
            
            # Prepare input for LLM-controlled RAG with max_documents
            rag_input = {
                "question": message,
                "personality": personality,
                "history": history,
                "content_settings": content_settings,  # This now includes max_documents
                "similarity_threshold": similarity_threshold,
                "llm_temperature": llm_temperature
            }
            
            # Get response from LLM-controlled RAG
            response = self.rag_chain.invoke_with_filters(rag_input)
            
            return response
            
        except Exception as e:
            print(f"❌ Error in chat_response_with_filters: {e}")
            # Fallback to regular chat response
            try:
                return self.chat_response(message, history, personality, content_settings.get('max_documents', 5))
            except Exception as fallback_error:
                return f"I encountered an error processing your request. Please try again."
    
    def get_memory_info(self) -> Dict[str, Any]:
        """Get information about current memory state"""
        try:
            return self.rag_chain.get_memory_summary()
        except Exception as e:
            return {
                "error": str(e),
                "total_messages": 0,
                "conversation_turns": 0,
                "memory_window_size": 10,
                "memory_active": False
            }
    
    def clear_conversation_memory(self):
        """Clear the conversation memory"""
        try:
            self.rag_chain.clear_memory()
        except Exception as e:
            print(f"❌ Error clearing memory: {e}")
    
    def export_conversation(self) -> Dict[str, Any]:
        """Export conversation for debugging/analysis"""
        try:
            memory_info = self.get_memory_info()
            
            # Get raw messages if available
            raw_messages = []
            if hasattr(self.rag_chain.memory, 'chat_memory') and hasattr(self.rag_chain.memory.chat_memory, 'messages'):
                for msg in self.rag_chain.memory.chat_memory.messages:
                    raw_messages.append({
                        "type": type(msg).__name__,
                        "content": getattr(msg, 'content', str(msg)),
                        "length": len(getattr(msg, 'content', str(msg)))
                    })
            
            return {
                "memory_info": memory_info,
                "raw_messages": raw_messages,
                "export_timestamp": str(pd.Timestamp.now()) if 'pd' in globals() else "unavailable"
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def simulate_conversation(self, test_scenario: str = "docker_basics") -> bool:
        """Simulate a test conversation for debugging"""
        
        scenarios = {
            "docker_basics": [
                ("Hi! I want to learn about Docker", "networkchuck"),
                ("How do I install Docker on Ubuntu?", "networkchuck"), 
                ("What's the difference between Docker and VMs?", "networkchuck"),
                ("Can you remind me what we discussed about installation?", "networkchuck")
            ],
            "excel_tutorial": [
                ("I need help with Excel spreadsheets", "bloomy"),
                ("How do I create a VLOOKUP formula?", "bloomy"),
                ("What about pivot tables?", "bloomy"),
                ("Earlier you mentioned VLOOKUP, can you expand on that?", "bloomy")
            ],
            "max_documents_test": [
                ("What is machine learning?", "datascientist"),  # Test with different max_documents
                ("Explain neural networks", "datascientist"),
                ("How does deep learning work?", "datascientist")
            ]
        }
        
        if test_scenario not in scenarios:
            print(f"❌ Unknown scenario: {test_scenario}")
            return False
        
        print(f"🎬 Simulating conversation: {test_scenario}")
        
        # Clear memory before test
        self.clear_conversation_memory()
        
        history = []
        for i, (question, personality) in enumerate(scenarios[test_scenario]):
            print(f"\n--- Turn {i+1} ---")
            print(f"👤 User ({personality}): {question}")
            
            # Test with different max_documents values
            if test_scenario == "max_documents_test":
                max_docs = [3, 8, 12][i]  # Different values for each turn
                content_settings = {'max_documents': max_docs, 'enable_videos': True, 'enable_docs': True, 'enable_analogies': True}
                response = self.chat_response_with_filters(question, history, personality, content_settings, 0.3, 0.7)
                print(f"🤖 Bot (max_docs={max_docs}): {response[:150]}...")
            else:
                # Regular test
                response = self.chat_response(question, history, personality)
                print(f"🤖 Bot: {response[:150]}...")
            
            # Update history (Gradio format)
            history.append([question, response])
            
            # Show memory state
            memory_info = self.get_memory_info()
            print(f"🧠 Memory: {memory_info.get('conversation_turns', 0)} turns")
        
        print(f"\n✅ Conversation simulation completed!")
        
        # Clean up after test
        self.clear_conversation_memory()
        return True
    
    def benchmark_max_documents(self, query: str = "What is Docker?", personality: str = "networkchuck") -> Dict[int, Dict]:
        """Benchmark different max_documents values"""
        
        results = {}
        test_values = [1, 3, 5, 8, 10, 15]
        
        print(f"🏁 Benchmarking max_documents with query: '{query}'")
        
        for max_docs in test_values:
            print(f"\n📄 Testing max_documents = {max_docs}")
            
            # Clear memory for clean test
            self.clear_conversation_memory()
            
            import time
            start_time = time.time()
            
            content_settings = {
                'max_documents': max_docs,
                'enable_videos': True,
                'enable_docs': True,
                'enable_analogies': True
            }
            
            try:
                response = self.chat_response_with_filters(
                    query, [], personality, content_settings, 0.3, 0.7
                )
                
                end_time = time.time()
                
                results[max_docs] = {
                    'response_length': len(response),
                    'response_time': round(end_time - start_time, 2),
                    'success': True,
                    'response_preview': response[:100] + "..." if len(response) > 100 else response
                }
                
                print(f"   ✅ Time: {results[max_docs]['response_time']}s, Length: {results[max_docs]['response_length']} chars")
                
            except Exception as e:
                results[max_docs] = {
                    'success': False,
                    'error': str(e),
                    'response_time': None
                }
                print(f"   ❌ Error: {e}")
        
        print(f"\n📊 Benchmark Results Summary:")
        print("Max Docs | Time (s) | Length | Status")
        print("-" * 40)
        for max_docs, result in results.items():
            if result['success']:
                print(f"{max_docs:8} | {result['response_time']:7} | {result['response_length']:6} | ✅")
            else:
                print(f"{max_docs:8} | {'ERROR':7} | {'N/A':6} | ❌")
        
        # Clean up after benchmark
        self.clear_conversation_memory()
        
        return results
    
    def get_optimal_max_documents(self, target_response_time: float = 3.0) -> int:
        """Get optimal max_documents value based on performance"""
        
        benchmark_results = self.benchmark_max_documents()
        
        # Find the highest max_documents that meets the time target
        optimal = 5  # Default fallback
        
        for max_docs in sorted(benchmark_results.keys(), reverse=True):
            result = benchmark_results[max_docs]
            if result['success'] and result['response_time'] <= target_response_time:
                optimal = max_docs
                break
        
        print(f"🎯 Optimal max_documents for {target_response_time}s target: {optimal}")
        return optimal


# Test functions
def test_max_documents_feature():
    """Test the max documents feature"""
    print("🧪 Testing Max Documents Feature...")
    
    try:
        # Initialize chatbot
        chatbot = NetworkChuckChatbot(memory_window_size=5)
        
        # Test different max_documents values
        test_query = "What is machine learning?"
        test_personality = "datascientist"
        
        for max_docs in [1, 5, 10]:
            print(f"\n📄 Testing with max_documents = {max_docs}")
            
            content_settings = {
                'max_documents': max_docs,
                'enable_videos': True,
                'enable_docs': True,
                'enable_analogies': True
            }
            
            response = chatbot.chat_response_with_filters(
                test_query, [], test_personality, content_settings, 0.3, 0.7
            )
            
            print(f"Response length: {len(response)} characters")
            print(f"Preview: {response[:100]}...")
        
        print("✅ Max Documents feature test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Max Documents test failed: {e}")
        return False

def test_chatbot_integration():
    """Test complete chatbot integration"""
    print("🧪 Testing Complete Chatbot Integration...")
    
    try:
        # Initialize chatbot
        chatbot = NetworkChuckChatbot()
        
        # Test regular chat
        response1 = chatbot.chat_response("Hello!", [], "networkchuck")
        print(f"✅ Regular chat: {len(response1)} chars")
        
        # Test filtered chat
        content_settings = {
            'max_documents': 3,
            'enable_videos': False,
            'enable_docs': False,
            'enable_analogies': True
        }
        
        response2 = chatbot.chat_response_with_filters(
            "What is Docker?", [], "networkchuck", content_settings, 0.5, 0.8
        )
        print(f"✅ Filtered chat: {len(response2)} chars")
        
        # Test memory
        memory_info = chatbot.get_memory_info()
        print(f"✅ Memory info: {memory_info.get('total_messages', 0)} messages")
        
        # Test conversation simulation
        chatbot.simulate_conversation("max_documents_test")
        print("✅ Conversation simulation completed")
        
        print("✅ Complete integration test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False


if __name__ == "__main__":
    # Run tests
    # test_max_documents_feature()
    # test_chatbot_integration()
    pass  # Run tests if needed