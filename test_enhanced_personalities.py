"""
Simple Clean Personality Tester - No debug noise, just results
"""

import os
import sys
from dotenv import load_dotenv

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()
from src.core.chatbot import NetworkChuckChatbot


class CleanPersonalityTester:
    """Simple personality tester with clean output"""
    
    def __init__(self):
        self.personalities = [
            "NetworkChuck", "Bloomy", "EthicalHacker", 
            "PatientTeacher", "StartupFounder", "DataScientist"
        ]
        
        # Different questions to avoid memory conflicts
        self.questions = {
            "NetworkChuck": "How do I install Docker?",
            "Bloomy": "Explain Excel VLOOKUP functions", 
            "EthicalHacker": "How do I secure my network?",
            "PatientTeacher": "I'm new to programming, where do I start?",
            "StartupFounder": "How do I validate a business idea?",
            "DataScientist": "What's correlation vs causation?"
        }
    
    def test_personality_voices(self):
        """Test each personality with clean output"""
        print("🎭 PERSONALITY VOICE TEST")
        print("=" * 50)
        
        for personality in self.personalities:
            print(f"\n🔬 Testing {personality}...")
            
            # Create fresh chatbot (suppress initialization output)
            import io
            import contextlib
            
            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                chatbot = NetworkChuckChatbot(memory_window_size=5)
            
            question = self.questions[personality]
            
            try:
                # Get response (suppress debug output)
                with contextlib.redirect_stdout(f):
                    response = chatbot.chat_response(question, [], personality)
                
                # Analyze response
                analysis = self.analyze_response(personality, response)
                
                # Clean output
                print(f"   Question: {question}")
                print(f"   Response: {len(response)} chars")
                print(f"   Style Score: {analysis['score']}/10")
                print(f"   Markers: {analysis['markers']}")
                print(f"   Has Videos: {'Yes' if '🎥' in response else 'No'}")
                print(f"   Status: {'✅ Good' if analysis['score'] >= 6 else '⚠️ Weak'}")
                
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
    
    def test_same_question(self):
        """Test same question across personalities"""
        print("\n🔄 SAME QUESTION TEST")
        print("=" * 50)
        
        test_question = "How do I improve my Excel skills?"
        print(f"Question: {test_question}\n")
        
        for personality in self.personalities:
            # Fresh chatbot with suppressed output
            import io
            import contextlib
            
            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                chatbot = NetworkChuckChatbot(memory_window_size=5)
                response = chatbot.chat_response(test_question, [], personality)
            
            # Get first sentence of response
            first_sentence = response.split('.')[0][:100] + "..."
            analysis = self.analyze_response(personality, response)
            
            print(f"{personality:15} | Score: {analysis['score']:2}/10 | {first_sentence}")
    
    def test_memory_simple(self):
        """Simple memory test"""
        print("\n🧠 MEMORY TEST")
        print("=" * 50)
        
        import io
        import contextlib
        
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            chatbot = NetworkChuckChatbot(memory_window_size=5)
        
        history = []
        
        # First question
        with contextlib.redirect_stdout(f):
            response1 = chatbot.chat_response("How do I install Docker?", history, "NetworkChuck")
        history.append(["How do I install Docker?", response1])
        print("✅ First question: Docker installation")
        
        # Memory question  
        with contextlib.redirect_stdout(f):
            response2 = chatbot.chat_response("What did we just discuss?", history, "NetworkChuck")
        
        has_recap = "docker" in response2.lower() and ("discussed" in response2.lower() or "talked" in response2.lower())
        print(f"✅ Memory question: {'Working' if has_recap else 'Failed'}")
        
        # Get memory info
        memory_info = chatbot.get_memory_info()
        print(f"✅ Memory state: {memory_info['conversation_turns']} turns stored")
    
    def analyze_response(self, personality, response):
        """Simple response analysis"""
        response_lower = response.lower()
        
        markers = {
            "NetworkChuck": ["coffee", "☕", "hey there", "alright", "brewing"],
            "Bloomy": ["professional", "1.", "2.", "structured", "best practices"],
            "EthicalHacker": ["security", "ethical", "vulnerability", "attack", "legal"],
            "PatientTeacher": ["great question", "together", "understanding", "step by step"],
            "StartupFounder": ["scalability", "business", "startup", "mvp", "market"],
            "DataScientist": ["data", "analysis", "statistical", "evidence", "correlation"]
        }
        
        personality_markers = markers.get(personality, [])
        found = [m for m in personality_markers if m in response_lower]
        score = min(10, len(found) * 2)
        
        return {"markers": found, "score": score}
    
    def run_clean_tests(self):
        """Run all tests with clean output"""
        print("🧪 CLEAN PERSONALITY TESTING")
        print("=" * 60)
        
        try:
            self.test_personality_voices()
            self.test_same_question() 
            self.test_memory_simple()
            
            print("\n🎯 SUMMARY")
            print("=" * 50)
            print("✅ Personality testing complete")
            print("💡 Look for:")
            print("   - Style scores 6+/10 for good personality consistency")
            print("   - Different response styles for same question")
            print("   - Working memory functionality")
            
            return True
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return False


def main():
    """Simple main runner"""
    tester = CleanPersonalityTester()
    success = tester.run_clean_tests()
    
    if success:
        print("\n🎉 Testing completed!")
    else:
        print("\n❌ Testing failed!")


if __name__ == "__main__":
    main()