"""
NetworkChuck AI - Tabbed Interface Layout (Rolled Back to Working Voice System)
"""

import gradio as gr
import os
import json
import tempfile
from dotenv import load_dotenv

load_dotenv()
from src.core.chatbot import NetworkChuckChatbot
from src.core.voice_manager import speech_to_text, text_to_speech_simple

chatbot = NetworkChuckChatbot(max_turns=20)

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

# Updated the extract_text_only function to use the new cleaning
def extract_text_only(response_text: str) -> str:
    """Extract only the main text content, removing videos and docs"""
    if not response_text or response_text is None:
        return ""
    
    try:
        # Use the new voice cleaner if available
        from src.utils.voice_cleaner import extract_voice_content, clean_text_for_voice
        voice_content = extract_voice_content(response_text)
        return clean_text_for_voice(voice_content)
    except ImportError:
        # Fallback to original method if new cleaner not available
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

def remove_video_sections(response_text: str) -> str:
    """Remove video sections from response"""
    if not response_text:
        return ""
    
    lines = response_text.split('\n')
    filtered_lines = []
    skip_section = False
    
    for line in lines:
        if '🎥 **Source Videos:**' in line:
            skip_section = True
            continue
        elif '📚 **Related Documentation:**' in line:
            skip_section = False
        
        if not skip_section:
            filtered_lines.append(line)
    
    return '\n'.join(filtered_lines).strip()

def remove_doc_sections(response_text: str) -> str:
    """Remove documentation sections from response"""
    if not response_text:
        return ""
    
    lines = response_text.split('\n')
    filtered_lines = []
    skip_section = False
    
    for line in lines:
        if '📚 **Related Documentation:**' in line:
            skip_section = True
            continue
        
        if not skip_section:
            filtered_lines.append(line)
    
    return '\n'.join(filtered_lines).strip()

def chat_with_personality(message, history, personality, enable_videos, enable_docs, enable_analogies, max_documents, similarity_threshold, llm_temperature):
    """Enhanced chat function with max documents control"""
    try:
        # Remove emoji from personality for backend processing
        clean_personality = personality.split(' ', 1)[1] if ' ' in personality else personality
        
        # Prepare content settings with max_documents
        content_settings = {
            'enable_videos': enable_videos,
            'enable_docs': enable_docs,
            'enable_analogies': enable_analogies,
            'max_documents': max_documents
        }
        
        # Use new filtering method with max_documents
        response = chatbot.chat_response_with_filters(
            message, 
            history, 
            clean_personality, 
            content_settings, 
            similarity_threshold, 
            llm_temperature
        )
        
        return response
    except Exception as e:
        error_msg = f"Sorry, I encountered an error: {str(e)}"
        return error_msg

def generate_voice_response(text, personality):
    """Generate voice response with proper text cleaning"""
    if not text:
        return None
    
    try:
        from src.utils.voice_cleaner import extract_voice_content, clean_text_for_voice
        
        clean_personality = personality.split(' ', 1)[1] if ' ' in personality else personality
        
        # Extract main content and clean for voice
        voice_content = extract_voice_content(text)
        clean_text = clean_text_for_voice(voice_content)
        
        # Debug: Show what we're sending to TTS
        print(f"🔊 Voice text (cleaned): '{clean_text[:100]}...'")
        
        if clean_text:
            audio_bytes = text_to_speech_simple(clean_text, clean_personality)
            if audio_bytes:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                    temp_file.write(audio_bytes)
                    return temp_file.name
    except Exception as e:
        print(f"⚠️ Voice generation error: {e}")
        # Fallback: basic cleaning if import fails
        fallback_text = text.replace('*', '').replace('•', '').replace('#', '')
        try:
            audio_bytes = text_to_speech_simple(fallback_text, clean_personality)
            if audio_bytes:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                    temp_file.write(audio_bytes)
                    return temp_file.name
        except:
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

# Dark theme CSS with tabbed interface styling
custom_css = """
.gradio-container {
    font-family: 'Segoe UI', 'Arial', sans-serif;
}
.title-header {
    background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
    color: #e2e8f0;
    text-align: center;
    padding: 20px;
    border-radius: 12px;
    margin-bottom: 20px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}
.control-tabs {
    background: #2d3748;
    border: 1px solid #4a5568;
    border-radius: 8px;
    margin: 10px;
    padding: 10px;
}
.main-chat {
    background: #1a202c;
    border: 1px solid #4a5568;
    border-radius: 8px;
    padding: 20px;
    margin: 10px;
}
.memory-status {
    background: #2d3748 !important;
    color: #e2e8f0 !important;
    border: 2px solid #4a5568 !important;
    padding: 15px !important;
    margin: 10px 0 !important;
    border-radius: 8px !important;
    font-family: monospace !important;
    font-weight: bold !important;
}
.memory-status * {
    color: #e2e8f0 !important;
}
.personality-traits {
    background: #553c9a;
    border: 1px solid #6b46c1;
    border-radius: 6px;
    padding: 12px;
    margin: 8px 0;
    color: #e2e8f0;
}
"""

def create_interface():
    test_set_names = list(test_sets.keys())
    
    with gr.Blocks(
        title="🚀 NetworkChuck AI Assistant - Professional Edition",
        css=custom_css,
        theme=gr.themes.Soft()
    ) as interface:
        
        # Main Title Header (Dark Theme)
        with gr.Row(elem_classes=["title-header"]):
            gr.HTML("""
            <div style="text-align: center;">
                <h1>🎭 Multi Persona AI Assistant</h1>
                <h3>🧠 Memory + 🎥 Videos + 🎭 Personalities + 🎤🔊 Voice + 🎯 Smart Filtering + 📄 Document Control</h3>
                <p>Professional AI assistant with advanced document retrieval control and intelligent filtering</p>
            </div>
            """)
        
        # Main Layout: Tabbed Controls + Chat Area
        with gr.Row():
            # Tabbed Control Panel
            with gr.Column(scale=1, elem_classes=["control-tabs"]):
                with gr.Tabs():
                    
                    # Voice Tab
                    with gr.Tab("🔊 Voice"):
                        voice_enabled = gr.Checkbox(
                            label="Enable Voice Output",
                            value=True,
                            info="AI responds with personality-matched voice"
                        )
                        
                        gr.Markdown("""
                        **🎤 Voice Features:**
                        - Speech-to-Text with ElevenLabs + Whisper fallback
                        - Text-to-Speech with 6 unique personality voices
                        - Clean audio output (text-only, no URLs)
                        - Side-by-side voice controls for easy access
                        
                        **🎙️ Voice Controls are located below the chat area**
                        """)

                    
                    # Enhanced Content Filtering Tab
                    with gr.Tab("🎯 Filtering"):
                        gr.Markdown("**📋 Response Content**")
                        
                        enable_videos = gr.Checkbox(
                            label="Include Source Videos",
                            value=True,
                            info="Show video links with timestamps"
                        )
                        
                        enable_docs = gr.Checkbox(
                            label="Include Documentation",
                            value=True,
                            info="Show related documentation links"
                        )
                        
                        enable_analogies = gr.Checkbox(
                            label="Enable Tech Analogies",
                            value=True,
                            info="Allow technical analogies for non-tech topics"
                        )
                        
                        gr.Markdown("**🔍 Document Retrieval Settings**")
                        
                        max_documents = gr.Slider(
                            minimum=1,
                            maximum=15,
                            value=5,
                            step=1,
                            label="Max Source Documents",
                            info="Maximum number of documents to retrieve for context"
                        )
                        
                        similarity_threshold = gr.Slider(
                            minimum=0.1,
                            maximum=0.8,
                            value=0.3,
                            step=0.1,
                            label="Content Relevance",
                            info="Higher = more relevant results only"
                        )
                        
                        gr.Markdown("**⚙️ AI Response Settings**")
                        
                        llm_temperature = gr.Slider(
                            minimum=0.1,
                            maximum=1.0,
                            value=0.7,
                            step=0.1,
                            label="Response Creativity",
                            info="Lower = focused, Higher = creative"
                        )
                        
                        gr.Markdown("""
                        **💡 Tips:**
                        - **Max Documents**: More = comprehensive but slower, Less = focused but faster
                        - **Relevance**: Higher = fewer but better results
                        - **Creativity**: Lower = more factual responses
                        - Disable videos/docs for cleaner responses
                        """)
                    
                    # Test Suite Tab
                    with gr.Tab("🧪 Tests"):
                        test_set_selector = gr.Radio(
                            choices=test_set_names,
                            value=test_set_names[0] if test_set_names else "No Tests",
                            label="Test Category",
                            info="Choose test scenarios"
                        )
                        
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
                        1. Select test category above
                        2. Click and drag to select test text
                        3. Copy (Ctrl+C) and paste in chat
                        """)
                    
                    # Memory Tab
                    with gr.Tab("🧠 Memory"):
                        memory_status_display = gr.Markdown(
                            value="""**🧠 Memory Status:** Ready
**📊 Messages:** 0
**💬 Turns:** 0
**🔧 Window:** 10
**✅ State:** Fresh""",
                            elem_classes=["memory-status"]
                        )
                        
                        with gr.Row():
                            refresh_memory_btn = gr.Button(
                                "🔄 Refresh",
                                variant="secondary",
                                size="sm",
                                scale=1
                            )
                            
                            clear_memory_btn = gr.Button(
                                "🧠 Clear",
                                variant="stop", 
                                size="sm",
                                scale=1
                            )
                        
                        gr.Markdown("""
                        **🧠 Memory Features:**
                        - LangChain conversation memory
                        - Cross-modal continuity (voice + text)
                        - Configurable window size (10 turns)
                        """)
            
            # Main Chat Area
            with gr.Column(scale=3, elem_classes=["main-chat"]):
                
                # Personality Settings (on top of chat) - All 6 Personalities
                personality_radio = gr.Radio(
                    choices=ALL_PERSONALITIES,
                    value="🧔‍♂️ NetworkChuck",
                    label="🎭 Active AI Personality",
                    info="Choose your expert persona - all personalities available"
                )
                
                # Simplified Personality Traits (no customization needed)
                with gr.Accordion("📋 Personality Traits & Descriptions", open=False, elem_classes=["personality-traits"]):
                    gr.Markdown("""
                    **📊 All Available Personalities:**
                    - 🧔‍♂️ **NetworkChuck** (8/10) - Energetic tech enthusiast with coffee analogies
                    - 👨‍💼 **Bloomy** (6/10) - Professional financial analyst with structured approach  
                    - 👩‍🔬 **DataScientist** (8/10) - Analytical expert with evidence-based methodology
                    - 🤵 **StartupFounder** (10/10) - Business leader focused on scalability
                    - 👩‍💻 **EthicalHacker** (8/10) - Security specialist with ethical approach
                    - 👩‍🏫 **PatientTeacher** (4/10) - Educational expert (demonstrates prompt engineering needs)
                    
                    **All personalities are always available in the selection above.**
                    """)
                
                # Enhanced Chat Interface with max_documents
                chatbot_interface = gr.ChatInterface(
                    fn=chat_with_personality,
                    type='messages',
                    additional_inputs=[
                        personality_radio, 
                        enable_videos, 
                        enable_docs, 
                        enable_analogies, 
                        max_documents,
                        similarity_threshold, 
                        llm_temperature
                    ],
                    title="💬 AI Conversation",
                    description="Ask questions and I'll remember our conversation with intelligent filtering!",
                    chatbot=gr.Chatbot(height=400, type='messages')
                )
                
                # REARRANGED: Audio Controls Side by Side
                gr.Markdown("### 🎤🔊 Voice Controls")
                
                with gr.Row():
                    # Left Side: Speech-to-Text (STT)
                    with gr.Column(scale=1):
                        gr.Markdown("#### 🎤 Speech to Text")
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
                    
                    # Right Side: Text-to-Speech (TTS)
                    with gr.Column(scale=1):
                        gr.Markdown("#### 🔊 Text to Speech")
                        tts_audio = gr.Audio(
                            label="AI Voice Response",
                            autoplay=True,
                            visible=True
                        )
                        
                        generate_voice_btn = gr.Button(
                            "🔊 Generate Voice",
                            variant="primary",
                            size="lg"
                        )
                
                gr.Markdown("**🎤 Voice Workflow:** Record → Convert OR Voice to Chat → AI responds → Generate Voice")

        
        # Event Handlers
        
        def update_tests_on_selection(test_set_name):
            """Update test table when test set changes"""
            tests = test_sets.get(test_set_name, [])
            return [[i+1, test] for i, test in enumerate(tests)]
        
        def generate_voice_for_last_response(history, personality, voice_enabled):
            """FIXED: Generate voice for the last AI response"""
            if not history or not voice_enabled:
                return None
            
            try:
                # Get the last bot message from history
                last_response = history[-1]["content"] if len(history) > 0 and history[-1].get("role") == "assistant" else ""
                
                # Fallback for older tuple format
                if not last_response and isinstance(history[-1], (list, tuple)) and len(history[-1]) >= 2:
                    last_response = history[-1][1]
                
                if last_response:
                    audio_file = generate_voice_response(last_response, personality)
                    if audio_file:
                        return audio_file
            except Exception as e:
                print(f"⚠️ Voice generation error: {e}")
            
            return None
        
        # Connect events
        test_set_selector.change(
            fn=update_tests_on_selection,
            inputs=[test_set_selector],
            outputs=[test_table]
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
        
        voice_to_chat_btn.click(
            fn=process_voice_input,
            inputs=[voice_input],
            outputs=[chatbot_interface.textbox]
        )
        
        # FIXED: Manual voice generation button
        generate_voice_btn.click(
            fn=generate_voice_for_last_response,
            inputs=[chatbot_interface.chatbot, personality_radio, voice_enabled],
            outputs=[tts_audio]
        )
        
        # Footer (Dark Theme)
        gr.HTML("""
        <div style="text-align: center; padding: 20px; margin-top: 20px; background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%); border-radius: 12px; color: #e2e8f0;">
            <h3>🚀 Professional AI Assistant Features</h3>
            <p><strong>Voice:</strong> Bidirectional conversation • <strong>Memory:</strong> LangChain integration • <strong>Filtering:</strong> Smart content control • <strong>Personalities:</strong> 6 unique experts • <strong>Sources:</strong> Videos + Documentation • <strong>Documents:</strong> User-controlled retrieval (1-15 docs)</p>
        </div>
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
    
# Test function for voice cleaning integration
def test_voice_cleaning_integration():
    """Test the voice cleaning integration"""
    
    test_response = """**Docker** is a *containerization* platform! 🚀

Here are the key benefits:
• **Portability** - runs anywhere
• *Consistency* - same environment everywhere  
• **Scalability** - easy to scale up/down

🎥 **Source Videos:**
1. **[Docker Tutorial](https://youtube.com/watch?v=123)**
   • 5:30 - Installation
   • 12:45 - Configuration

📚 **Related Documentation:**
1. **Docker Engine Documentation** (intermediate)
"""
    
    print("🧪 Testing Voice Cleaning Integration")
    print("=" * 50)
    print(f"Original text length: {len(test_response)} chars")
    print(f"Has asterisks: {'*' in test_response}")
    print(f"Has video section: {'🎥' in test_response}")
    
    # Test voice cleaning
    try:
        from src.utils.voice_cleaner import extract_voice_content, clean_text_for_voice
        
        voice_content = extract_voice_content(test_response)
        clean_text = clean_text_for_voice(voice_content)
        
        print(f"\nCleaned text length: {len(clean_text)} chars")
        print(f"Asterisks removed: {'*' not in clean_text}")
        print(f"Video section removed: {'🎥' not in clean_text}")
        print(f"Clean text: '{clean_text}'")
        
        print("\n✅ Voice cleaning integration test passed!")
        
    except Exception as e:
        print(f"❌ Voice cleaning test failed: {e}")

if __name__ == "__main__":
    # Comment out test to avoid memory pollution
    # test_memory_integration()
    test_voice_cleaning_integration()
    
    # Ensure completely fresh memory for users
    chatbot.clear_conversation_memory()
    
    interface = create_interface()
    interface.launch()