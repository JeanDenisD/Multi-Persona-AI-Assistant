from src.core.chatbot import NetworkChuckChatbot

def test_memory():
    print("🧪 Testing memory integration...")
    chatbot = NetworkChuckChatbot(memory_window_size=5)
    memory_info = chatbot.get_memory_info()
    print(f"Initial memory status: {memory_info}")
    
    # Test conversation memory
    print("\n🎭 Testing conversation...")
    history = []
    
    # First question
    response1 = chatbot.chat_response("How do I install Docker?", history, "networkchuck")
    print(f"Response 1 length: {len(response1)} chars")
    history.append(["How do I install Docker?", response1])
    
    # Follow-up question (should use memory)
    response2 = chatbot.chat_response("Can you remind me what we just discussed?", history, "networkchuck")
    print(f"Response 2 length: {len(response2)} chars")
    
    # Check memory after conversation
    final_memory = chatbot.get_memory_info()
    print(f"Final memory status: {final_memory}")

if __name__ == "__main__":
    test_memory()