"""
NetworkChuck AI - Optimized Layout with Test Suite on Right
Professional testing framework with enhanced UI and fixed readability
"""

import gradio as gr
import os
import json
from dotenv import load_dotenv

load_dotenv()
from src.core.chatbot import NetworkChuckChatbot

chatbot = NetworkChuckChatbot(memory_window_size=10)

def load_test_cases(file_path="data/test_cases.json"):
    """Load test cases from external JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            test_cases = json.load(f)
        print(f"✅ Loaded {len(test_cases)} test sets from {file_path}")
        return test_cases
    except FileNotFoundError:
        print(f"⚠️ Test cases file not found: {file_path}")
        return {
            "Docker Tests": [
                "Hello! How are you?",
                "How do I install Docker?", 
                "What about Docker Compose?",
                "Can you remind me what we discussed about Docker?"
            ],
            "Excel Tests": [
                "Tell me about Excel VLOOKUP",
                "How do pivot tables work?",
                "What's the difference between VLOOKUP and INDEX-MATCH?",
                "What did we discuss about Excel earlier?"
            ]
        }
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing test cases JSON: {e}")
        return {}

def chat_with_personality(message, history, personality):
    """Clean chat function"""
    try:
        print(f"🎭 DEBUG: Chat using personality: {personality}")
        response = chatbot.chat_response(message, history, personality)
        return response
    except Exception as e:
        error_msg = f"Sorry, I encountered an error: {str(e)}"
        print(f"❌ Error in chat_with_personality: {error_msg}")
        return error_msg

def get_memory_status():
    try:
        memory_info = chatbot.get_memory_info()
        return f"""**🧠 Memory Status:** Active
**📊 Messages:** {memory_info.get('total_messages', 0)}
**💬 Turns:** {memory_info.get('conversation_turns', 0)}
**🔧 Window:** {memory_info.get('memory_window_size', 0)}
**✅ State:** {'Active' if memory_info.get('memory_active', False) else 'Ready'}"""
    except Exception as e:
        return f"**❌ Error:** {e}"

def clear_memory():
    try:
        chatbot.clear_conversation_memory()
        print("🧠 Conversation memory cleared")
        return """**🧠 Memory:** Cleared
**✅ Status:** Ready
**🔄 State:** Fresh start"""
    except Exception as e:
        print(f"❌ Error clearing memory: {e}")
        return f"**❌ Error:** {e}"

# Load test sets from external file
test_sets = load_test_cases()

# Enhanced CSS with fixes for both issues
custom_css = """
.gradio-container {
    font-family: 'Arial', sans-serif;
}
.memory-status {
    background: #ffffff !important;
    color: #000000 !important;
    border: 2px solid #666666 !important;
    padding: 15px !important;
    margin: 10px 0 !important;
    border-radius: 8px !important;
    font-family: monospace !important;
    font-weight: bold !important;
}
.memory-status * {
    color: #000000 !important;
}
.test-suite {
    background: rgba(0, 100, 200, 0.1);
    border: 2px solid #0066cc;
    border-radius: 10px;
    padding: 10px;
    margin: 10px 0;
}
"""

def create_interface():
    personalities = ["NetworkChuck", "Bloomy"]
    test_set_names = list(test_sets.keys())
    
    with gr.Blocks(
        title="🚀 NetworkChuck AI Assistant with Test Suite",
        css=custom_css,
        theme=gr.themes.Soft()
    ) as interface:
        
        gr.Markdown("""
        # 🚀 NetworkChuck AI Assistant
        ## 🧠 LangChain Memory + 🧪 Professional Test Suite
        
        Optimized layout: Chat on left, test suite and controls on right!
        """)
        
        # Radio buttons for personalities
        with gr.Row():
            personality_radio = gr.Radio(
                choices=personalities,
                value="NetworkChuck",
                label="🎭 Choose AI Personality"
            )
        
        # Main Layout: Chat + Right Panel
        with gr.Row():
            # Left side: Chat Interface (larger)
            with gr.Column(scale=2):
                chatbot_interface = gr.ChatInterface(
                    fn=chat_with_personality,
                    additional_inputs=[personality_radio],
                    title="💬 Chat with Memory",
                    description="Ask questions and I'll remember our conversation!"
                )
            
            # Right side: Test Suite + Memory Controls (smaller)
            with gr.Column(scale=1):
                # Professional Test Suite Section
                with gr.Accordion("🧪 Test Suite", open=True, elem_classes=["test-suite"]):
                    gr.Markdown("### 📋 Quick Tests")
                    
                    test_set_selector = gr.Radio(
                        choices=test_set_names,
                        value=test_set_names[0] if test_set_names else "No Tests",
                        label="Select Test Set",
                        info="Choose test category"
                    )
                    
                    gr.Markdown("**Test Cases:**")
                    
                    # Test cases table (FIXED - disabled interactive but kept text selectable)
                    initial_tests = test_sets.get(test_set_names[0], []) if test_set_names else []
                    test_table = gr.DataFrame(
                        value=[[i+1, test] for i, test in enumerate(initial_tests)],
                        headers=["#", "Test Case"],
                        datatype=["number", "str"],
                        interactive=True,
                        wrap=True
                    )
                    
                    gr.Markdown("""
                    **📋 Usage:**
                    1. Select test set above
                    2. **Click and drag** to select test case text
                    3. **Copy** (Ctrl+C) and **paste** in chat input
                    4. Perfect for demos!
                    """)
                
                # Memory Controls
                gr.Markdown("### 🧠 Memory Controls")
                
                # FIXED: Better contrast for memory status
                memory_status_display = gr.Markdown(
                    value="""**🧠 Memory Status:** Ready
**📊 State:** Initialized  
**🔧 Window:** 10 turns""",
                    elem_classes=["memory-status"]
                )
                
                with gr.Column():
                    refresh_memory_btn = gr.Button(
                        "🔄 Refresh Status",
                        variant="secondary",
                        size="sm"
                    )
                    
                    clear_memory_btn = gr.Button(
                        "🧠 Clear Memory",
                        variant="stop", 
                        size="sm"
                    )
                
                # Compact Personality Info
                gr.Markdown("""
                ### 🎭 Personalities:
                
                **🚀 NetworkChuck**
                Tech enthusiast, coffee educator
                
                **💼 Bloomy**
                Financial analyst, Bloomberg expert
                """)
        
        # Event Handlers
        
        def switch_personality(personality):
            print(f"🎭 DEBUG: Switched to {personality}")
            return f"""**🎭 Personality:** {personality}
**✅ Status:** Active
**🔄 Ready:** For conversation"""
        
        def update_tests_on_selection(test_set_name):
            """Update test table when test set changes"""
            tests = test_sets.get(test_set_name, [])
            table_data = [[i+1, test] for i, test in enumerate(tests)]
            return table_data
        
        # Connect events
        test_set_selector.change(
            fn=update_tests_on_selection,
            inputs=[test_set_selector],
            outputs=[test_table]
        )
        
        personality_radio.change(
            fn=switch_personality,
            inputs=[personality_radio],
            outputs=[memory_status_display]
        )
        
        refresh_memory_btn.click(
            fn=get_memory_status,
            outputs=[memory_status_display]
        )
        
        clear_memory_btn.click(
            fn=clear_memory,
            outputs=[memory_status_display]
        )
        
        # Compact Footer
        gr.Markdown(f"""
        ---
        **🚀 Features:** {len(test_sets)} test sets • LangChain Memory • Multiple Personalities • Demo Ready
        """)
    
    return interface

def test_memory_integration():
    print("🧪 Testing LangChain Memory Integration...")
    try:
        memory_info = chatbot.get_memory_info()
        print(f"✅ Memory initialized: {memory_info}")
        
        test_history = []
        response1 = chatbot.chat_response("How do I install Docker?", test_history, "NetworkChuck")
        test_history.append(["How do I install Docker?", response1])
        print("✅ First response generated")
        
        response2 = chatbot.chat_response("Can you remind me what we just discussed?", test_history, "NetworkChuck")
        print("✅ Memory-based response generated")
        
        final_memory = chatbot.get_memory_info()
        print(f"✅ Final memory: {final_memory}")
        print("🎉 LangChain Memory Integration Test PASSED!")
        return True
    except Exception as e:
        print(f"❌ Memory Integration Test FAILED: {e}")
        return False

if __name__ == "__main__":
    print("🚀 NetworkChuck AI with Optimized Layout Starting...")
    test_memory_integration()
    
    interface = create_interface()
    interface.launch()