"""
NetworkChuck AI - Simple Voice Fix (minimal changes to your working app)
"""

import gradio as gr
import os
import json
import tempfile
from dotenv import load_dotenv

load_dotenv()
from src.core.chatbot import NetworkChuckChatbot
from src.core.voice_manager import speech_to_text, text_to_speech_simple

chatbot = NetworkChuckChatbot(memory_window_size=10)

def load_test_cases(file_path="data/test_cases.json"):
    """Load test cases from external JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            test_cases = json.load(f)
        return test_cases
    except FileNotFoundError:
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
        return {}

def extract_text_only(response_text: str) -> str:
    """Extract only the main text content, removing videos and docs"""
    if not response_text or response_text is None:
        return ""
    
    lines = response_text.split('\n')
    text_lines = []
    
    for line in lines:
        # Skip video and documentation sections
        if any(marker in line for marker in ['🎥 **Source Videos:**', '📚 **Related Documentation:**']):
            break
        if line.startswith('**[') or line.startswith('• [') or 'http' in line:
            continue
        text_lines.append(line)
    
    return '\n'.join(text_lines).strip()

def chat_with_personality(message, history, personality):
    """Clean chat function - back to original working version"""
    try:
        # Remove emoji from personality for backend processing
        clean_personality = personality.split(' ', 1)[1] if ' ' in personality else personality
        response = chatbot.chat_response(message, history, clean_personality)
        return response
    except Exception as e:
        error_msg = f"Sorry, I encountered an error: {str(e)}"
        return error_msg

def generate_voice_response(text, personality):
    """Generate voice response separately"""
    if not text:
        return None
    
    try:
        clean_personality = personality.split(' ', 1)[1] if ' ' in personality else personality
        clean_text = extract_text_only(text)
        
        if clean_text:
            audio_bytes = text_to_speech_simple(clean_text, clean_personality)
            if audio_bytes:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                    temp_file.write(audio_bytes)
                    return temp_file.name
    except Exception as e:
        pass
    
    return None

def process_voice_input(audio_data):
    """Process voice input and return transcribed text"""
    if audio_data is None:
        return ""
    return speech_to_text(audio_data)

def get_memory_status():
    try:
        memory_info = chatbot.get_memory_info()
        total_messages = memory_info.get('total_messages', 0)
        conversation_turns = memory_info.get('conversation_turns', 0)
        
        # Show proper fresh state when no messages
        if total_messages == 0:
            return f"""**🧠 Memory Status:** Ready
**📊 Messages:** 0
**💬 Turns:** 0
**🔧 Window:** {memory_info.get('memory_window_size', 10)}
**✅ State:** Fresh"""
        else:
            return f"""**🧠 Memory Status:** Active
**📊 Messages:** {total_messages}
**💬 Turns:** {conversation_turns}
**🔧 Window:** {memory_info.get('memory_window_size', 10)}
**✅ State:** {'Active' if memory_info.get('memory_active', False) else 'Ready'}"""
    except Exception as e:
        return f"""**🧠 Memory Status:** Ready
**📊 Messages:** 0
**💬 Turns:** 0
**🔧 Window:** 10
**✅ State:** Fresh"""

def clear_memory():
    try:
        chatbot.clear_conversation_memory()
        return """**🧠 Memory:** Cleared
**✅ Status:** Ready
**🔄 State:** Fresh start"""
    except Exception as e:
        return f"**❌ Error:** {e}"

def toggle_personalities(selected_personalities):
    """Update available personalities based on user selection"""
    if not selected_personalities:
        return gr.Radio(choices=["NetworkChuck", "StartupFounder", "EthicalHacker"], 
                       value="NetworkChuck")
    else:
        return gr.Radio(choices=selected_personalities, 
                       value=selected_personalities[0])

# Load test sets from external file
test_sets = load_test_cases()

# All available personalities with icons
ALL_PERSONALITIES = [
    "🧔‍♂️ NetworkChuck", 
    "👨‍💼 Bloomy", 
    "👩‍💻 EthicalHacker", 
    "👩‍🏫 PatientTeacher", 
    "🤵 StartupFounder", 
    "👩‍🔬 DataScientist"
]

# Default showcase personalities (strong ones)
DEFAULT_PERSONALITIES = ["🧔‍♂️ NetworkChuck", "👨‍💼 Bloomy", "👩‍🔬 DataScientist"]

# Enhanced CSS
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
.personality-config {
    background: rgba(100, 0, 200, 0.1);
    border: 2px solid #6600cc;
    border-radius: 10px;
    padding: 10px;
    margin: 10px 0;
}
.voice-controls {
    background: rgba(0, 150, 100, 0.1);
    border: 2px solid #00cc66;
    border-radius: 10px;
    padding: 10px;
    margin: 10px 0;
}
"""

def create_interface():
    test_set_names = list(test_sets.keys())
    
    with gr.Blocks(
        title="🚀 NetworkChuck AI Assistant - Voice-Enabled",
        css=custom_css,
        theme=gr.themes.Soft()
    ) as interface:
        
        gr.Markdown("""
        # 🚀 NetworkChuck AI Assistant
        ## 🧠 Memory + 🎥 Videos + 🎭 Customizable AI Personalities + 🎤🔊 Voice
        
        Complete voice conversation - talk with AI personalities that respond in their unique voices!
        """)
        
        # Active Personality Selector (Full width like chatbox)
        personality_radio = gr.Radio(
            choices=DEFAULT_PERSONALITIES,
            value="🧔‍♂️ NetworkChuck",
            label="🎭 Active AI Personality",
            info="Select your current expert persona"
        )
        
        # Voice settings
        with gr.Accordion("🔊 Voice Settings", open=False, elem_classes=["voice-controls"]):
            voice_enabled = gr.Checkbox(
                label="Enable Voice Output",
                value=True,
                info="AI will respond with voice"
            )
        
        # Main Layout: Chat + Right Panel
        with gr.Row():
            # Left side: Chat Interface (larger)
            with gr.Column(scale=2):
                # Use your original working ChatInterface
                chatbot_interface = gr.ChatInterface(
                    fn=chat_with_personality,
                    additional_inputs=[personality_radio],
                    title="💬 Chat with Memory + Videos + Voice",
                    description="Ask questions and I'll remember our conversation!",
                    chatbot=gr.Chatbot(height=600)
                )
                
                # Separate voice output area
                with gr.Row():
                    tts_audio = gr.Audio(
                        label="🔊 AI Voice Response",
                        autoplay=True,
                        visible=True
                    )
                    generate_voice_btn = gr.Button(
                        "🔊 Generate Voice",
                        variant="secondary",
                        size="sm"
                    )
                
                # Voice input section - added below chat
                with gr.Accordion("🎤 Voice Input", open=False, elem_classes=["voice-controls"]):
                    gr.Markdown("### 🎤 Voice to Text")
                    voice_input = gr.Audio(
                        sources=["microphone"],
                        type="numpy",
                        label="Record your question"
                    )
                    with gr.Row():
                        voice_btn = gr.Button("🎤→📝 Convert Only", variant="secondary", scale=1)
                        voice_to_chat_btn = gr.Button("🎤→💬 Voice to Chat", variant="primary", scale=1)
                    voice_output = gr.Textbox(
                        label="Transcribed Text",
                        placeholder="Voice will be converted to text here...",
                        lines=2
                    )
                    gr.Markdown("**Usage:** Record → **Voice to Chat** (auto-fills chat input) OR Convert Only → Copy → Paste")
            
            # Right side: Personality Settings + Test Suite + Memory Controls
            with gr.Column(scale=1):
                # Personality Configuration Section (Collapsible)
                with gr.Accordion("⚙️ Personality Settings", open=False, elem_classes=["personality-config"]):
                    gr.Markdown("""
                    ### 🎭 Customize Available Personalities
                    Select which AI personalities you want to use.
                    """)
                    
                    personality_selector_right = gr.CheckboxGroup(
                        choices=ALL_PERSONALITIES,
                        value=DEFAULT_PERSONALITIES,
                        label="Available Personalities",
                        info="Select personalities to show"
                    )
                    
                    gr.Markdown("""
                    **📊 Strength Scores:**
                    - 🧔‍♂️ **NetworkChuck** (8/10)
                    - 👨‍💼 **Bloomy** (6/10) 
                    - 👩‍🔬 **DataScientist** (8/10)
                    - 🤵 **StartupFounder** (10/10)
                    - 👩‍💻 **EthicalHacker** (8/10)
                    - 👩‍🏫 **PatientTeacher** (4/10)
                    """)
                
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
                
                # Memory Controls (Collapsible)
                with gr.Accordion("🧠 Memory Controls", open=False):
                    memory_status_display = gr.Markdown(
                        value="""**🧠 Memory Status:** Ready
**📊 Messages:** 0
**💬 Turns:** 0
**🔧 Window:** 10
**✅ State:** Fresh""",
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
        
        # Event Handlers
        
        def update_personality_radio(selected_personalities):
            """Update the personality radio options based on selection"""
            if not selected_personalities:
                choices = DEFAULT_PERSONALITIES
                value = "🧔‍♂️ NetworkChuck"
            else:
                choices = selected_personalities
                value = selected_personalities[0]
            
            return gr.Radio(choices=choices, value=value)
        
        def switch_personality(personality):
            return f"""**🎭 Personality:** {personality}
**✅ Status:** Active
**🔄 Ready:** For conversation"""
        
        def update_tests_on_selection(test_set_name):
            """Update test table when test set changes"""
            tests = test_sets.get(test_set_name, [])
            table_data = [[i+1, test] for i, test in enumerate(tests)]
            return table_data
        
        def generate_voice_for_last_response(history, personality, voice_enabled):
            """Generate voice for the last AI response"""
            if not history or not voice_enabled:
                return gr.Audio(visible=False)
            
            try:
                last_response = history[-1][1] if len(history) > 0 else ""
                if last_response:
                    audio_file = generate_voice_response(last_response, personality)
                    if audio_file:
                        return gr.Audio(value=audio_file, visible=True)
            except:
                pass
            
            return gr.Audio(visible=False)
        
        # Connect events
        personality_selector_right.change(
            fn=update_personality_radio,
            inputs=[personality_selector_right],
            outputs=[personality_radio]
        )
        
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
        
        # Voice input events
        voice_btn.click(
            fn=process_voice_input,
            inputs=[voice_input],
            outputs=[voice_output]
        )
        
        # Voice input that auto-fills chat input
        voice_to_chat_btn.click(
            fn=process_voice_input,
            inputs=[voice_input],
            outputs=[chatbot_interface.textbox]
        )
        
        # Manual voice generation button
        generate_voice_btn.click(
            fn=generate_voice_for_last_response,
            inputs=[chatbot_interface.chatbot, personality_radio, voice_enabled],
            outputs=[tts_audio]
        )
        
        # Updated Footer
        gr.Markdown(f"""
        ---
        **🚀 Features:** Voice Input/Output • Customizable Personalities • Memory • Videos • Documentation • {len(test_sets)} Test Sets
        """)
    
    return interface

def test_memory_integration():
    try:
        # Clear any existing memory first
        chatbot.clear_conversation_memory()
        
        memory_info = chatbot.get_memory_info()
        
        test_history = []
        response1 = chatbot.chat_response("How do I install Docker?", test_history, "NetworkChuck")
        test_history.append(["How do I install Docker?", response1])
        
        response2 = chatbot.chat_response("Can you remind me what we just discussed?", test_history, "NetworkChuck")
        
        final_memory = chatbot.get_memory_info()
        
        # Clean up test data from memory - make sure it's completely clean
        chatbot.clear_conversation_memory()
        
        return True
    except Exception as e:
        # Always clean memory even if test fails
        chatbot.clear_conversation_memory()
        return False

if __name__ == "__main__":
    # Comment out test to avoid memory pollution
    # test_memory_integration()

    print("🧪 Debug: Checking initial memory state...")
    memory_info = chatbot.get_memory_info()
    print(f"Memory before anything: {memory_info}")
    
    # Ensure completely fresh memory for users
    chatbot.clear_conversation_memory()
    
    interface = create_interface()
    interface.launch()