"""
Memory Manager Utility for NetworkChuck AI
Provides advanced memory management and debugging tools
"""

from typing import List, Dict, Any, Optional
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import HumanMessage, AIMessage
import json
from datetime import datetime


class MemoryManager:
    """
    Advanced memory management utility for the NetworkChuck AI system
    """
    
    def __init__(self, memory: ConversationBufferWindowMemory):
        self.memory = memory
    
    def gradio_to_langchain_history(self, gradio_history: List[List[str]]) -> List[Dict]:
        """
        Convert Gradio chat history to LangChain message format
        
        Args:
            gradio_history: [[user_msg, bot_msg], [user_msg, bot_msg], ...]
        
        Returns:
            List of message dictionaries
        """
        langchain_messages = []
        
        for turn in gradio_history:
            if len(turn) >= 2 and turn[0] and turn[1]:
                # Add user message
                langchain_messages.append({
                    "type": "human",
                    "content": turn[0],
                    "timestamp": datetime.now().isoformat()
                })
                
                # Add AI message
                langchain_messages.append({
                    "type": "ai", 
                    "content": turn[1],
                    "timestamp": datetime.now().isoformat()
                })
        
        return langchain_messages
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get detailed summary of conversation state"""
        try:
            messages = self.memory.chat_memory.messages
            
            summary = {
                "total_messages": len(messages),
                "conversation_turns": len(messages) // 2,
                "window_size": self.memory.k,
                "memory_full": len(messages) >= (self.memory.k * 2),
                "last_messages": []
            }
            
            # Get last few messages for preview
            for msg in messages[-4:]:  # Last 2 exchanges
                summary["last_messages"].append({
                    "type": type(msg).__name__,
                    "content": msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                })
            
            return summary
            
        except Exception as e:
            return {"error": str(e)}
    
    def export_conversation(self) -> Dict[str, Any]:
        """Export entire conversation for debugging/analysis"""
        try:
            messages = self.memory.chat_memory.messages
            
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "memory_config": {
                    "window_size": self.memory.k,
                    "return_messages": self.memory.return_messages,
                    "memory_key": self.memory.memory_key
                },
                "conversation": []
            }
            
            for i, msg in enumerate(messages):
                export_data["conversation"].append({
                    "index": i,
                    "type": type(msg).__name__,
                    "content": msg.content,
                    "length": len(msg.content)
                })
            
            return export_data
            
        except Exception as e:
            return {"error": str(e)}
    
    def import_conversation(self, conversation_data: List[Dict]) -> bool:
        """Import conversation from exported data"""
        try:
            self.memory.clear()
            
            # Process conversation data in pairs
            for i in range(0, len(conversation_data), 2):
                if i + 1 < len(conversation_data):
                    human_msg = conversation_data[i]
                    ai_msg = conversation_data[i + 1]
                    
                    if (human_msg.get("type") == "HumanMessage" and 
                        ai_msg.get("type") == "AIMessage"):
                        
                        self.memory.save_context(
                            {"input": human_msg["content"]},
                            {"output": ai_msg["content"]}
                        )
            
            return True
            
        except Exception as e:
            print(f"❌ Error importing conversation: {e}")
            return False
    
    def analyze_conversation_patterns(self) -> Dict[str, Any]:
        """Analyze conversation patterns for insights"""
        try:
            messages = self.memory.chat_memory.messages
            
            if not messages:
                return {"status": "no_conversation"}
            
            analysis = {
                "message_lengths": {
                    "human": [],
                    "ai": []
                },
                "topics_mentioned": [],
                "question_types": [],
                "personality_indicators": []
            }
            
            # Analyze message patterns
            for msg in messages:
                msg_type = "human" if isinstance(msg, HumanMessage) else "ai"
                analysis["message_lengths"][msg_type].append(len(msg.content))
                
                # Look for technical topics
                content_lower = msg.content.lower()
                tech_topics = ["docker", "excel", "python", "network", "security", "linux"]
                for topic in tech_topics:
                    if topic in content_lower and topic not in analysis["topics_mentioned"]:
                        analysis["topics_mentioned"].append(topic)
                
                # Detect question types
                if isinstance(msg, HumanMessage):
                    if "how" in content_lower:
                        analysis["question_types"].append("how-to")
                    elif "what" in content_lower:
                        analysis["question_types"].append("definition")
                    elif "?" in msg.content:
                        analysis["question_types"].append("general_question")
                
                # Look for personality markers
                personality_markers = {
                    "networkchuck": ["coffee", "hey guys", "what's up"],
                    "bloomy": ["professional", "financial", "analysis"]
                }
                
                for personality, markers in personality_markers.items():
                    for marker in markers:
                        if marker in content_lower:
                            analysis["personality_indicators"].append(personality)
            
            # Calculate averages
            if analysis["message_lengths"]["human"]:
                analysis["avg_human_length"] = sum(analysis["message_lengths"]["human"]) / len(analysis["message_lengths"]["human"])
            if analysis["message_lengths"]["ai"]:
                analysis["avg_ai_length"] = sum(analysis["message_lengths"]["ai"]) / len(analysis["message_lengths"]["ai"])
            
            return analysis
            
        except Exception as e:
            return {"error": str(e)}
    
    def optimize_memory_window(self, target_context_length: int = 3000) -> int:
        """
        Suggest optimal memory window size based on conversation patterns
        
        Args:
            target_context_length: Target total context length in characters
        
        Returns:
            Suggested window size
        """
        try:
            analysis = self.analyze_conversation_patterns()
            
            if "avg_human_length" not in analysis or "avg_ai_length" not in analysis:
                return 10  # Default
            
            avg_human = analysis["avg_human_length"]
            avg_ai = analysis["avg_ai_length"]
            avg_turn_length = avg_human + avg_ai
            
            # Calculate optimal window size
            optimal_window = max(3, min(20, target_context_length // avg_turn_length))
            
            return optimal_window
            
        except Exception as e:
            print(f"⚠️ Error optimizing memory window: {e}")
            return 10  # Default fallback


class ConversationDebugger:
    """
    Debug conversation flow and memory behavior
    """
    
    @staticmethod
    def simulate_conversation(chatbot, test_scenario: str = "docker_tutorial"):
        """Simulate a conversation scenario for testing"""
        
        scenarios = {
            "docker_tutorial": [
                ("Hi! I want to learn about Docker containers", "networkchuck"),
                ("How do I install Docker on Ubuntu?", "networkchuck"), 
                ("What's the difference between Docker and VMs?", "networkchuck"),
                ("Can you remind me what we discussed about installation?", "networkchuck")
            ],
            "excel_help": [
                ("I need help with Excel spreadsheets", "bloomy"),
                ("How do I create a VLOOKUP formula?", "bloomy"),
                ("What about pivot tables?", "bloomy"),
                ("Earlier you mentioned VLOOKUP, can you expand on that?", "bloomy")
            ]
        }
        
        if test_scenario not in scenarios:
            print(f"❌ Unknown scenario: {test_scenario}")
            return False
        
        print(f"🎬 Simulating conversation: {test_scenario}")
        
        history = []
        for i, (question, personality) in enumerate(scenarios[test_scenario]):
            print(f"\n--- Turn {i+1} ---")
            print(f"👤 User ({personality}): {question}")
            
            # Get response
            response = chatbot.chat_response(question, history, personality)
            print(f"🤖 Bot: {response[:150]}...")
            
            # Update history (Gradio format)
            history.append([question, response])
            
            # Show memory state
            memory_info = chatbot.get_memory_info()
            print(f"🧠 Memory: {memory_info.get('conversation_turns', 0)} turns")
        
        print(f"\n✅ Conversation simulation completed!")
        return True


# Test function
def test_memory_manager():
    """Test the memory manager functionality"""
    print("🧪 Testing Memory Manager...")
    
    try:
        # Create test memory
        from langchain.memory import ConversationBufferWindowMemory
        test_memory = ConversationBufferWindowMemory(k=5, return_messages=True)
        
        # Initialize manager
        manager = MemoryManager(test_memory)
        
        # Test Gradio conversion
        test_gradio_history = [
            ["Hello", "Hi there!"],
            ["How are you?", "I'm doing great!"]
        ]
        
        langchain_format = manager.gradio_to_langchain_history(test_gradio_history)
        print(f"✅ Converted {len(test_gradio_history)} Gradio turns to {len(langchain_format)} LangChain messages")
        
        # Test conversation analysis
        test_memory.save_context({"input": "How do I setup Docker?"}, {"output": "Docker is great for containers!"})
        analysis = manager.analyze_conversation_patterns()
        print(f"✅ Conversation analysis: {analysis.get('topics_mentioned', [])}")
        
        print("✅ Memory Manager test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Memory Manager test failed: {e}")
        return False


if __name__ == "__main__":
    test_memory_manager()