# app.py - Production NetworkChuck AI Chatbot for Hugging Face Spaces
# Enhanced RAG system with LangChain agents for academic compliance

import os
import sys
import gradio as gr
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src directory to Python path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import the enhanced agent system
try:
    from agents.agent_system import EnhancedRAGAgent
    AGENT_AVAILABLE = True
    print("✅ LangChain agent system loaded successfully!")
except Exception as e:
    print(f"⚠️ Agent system not available: {e}")
    print("🔄 Falling back to direct enhanced RAG system...")
    from core.enhanced_rag import EnhancedRAGEngine
    AGENT_AVAILABLE = False

class NetworkChuckChatbot:
    """Production chatbot with enhanced RAG and optional LangChain agents"""
    
    def __init__(self):
        """Initialize the chatbot with the best available system"""
        self.setup_system()
        
    def setup_system(self):
        """Setup either agent system or direct enhanced RAG"""
        try:
            if AGENT_AVAILABLE:
                # Use LangChain agent system (preferred for academic compliance)
                self.agent = EnhancedRAGAgent()
                self.mode = "agent"
                print("🤖 Using LangChain Agent System with Enhanced RAG")
            else:
                # Fallback to direct enhanced RAG
                self.enhanced_rag = EnhancedRAGEngine()
                self.mode = "direct"
                print("🚀 Using Direct Enhanced RAG System")
                
        except Exception as e:
            raise Exception(f"Failed to initialize chatbot system: {e}")
    
    def chat(self, message: str, personality: str = "NetworkChuck", 
             doc_search_enabled: bool = True, doc_count: int = 3) -> tuple:
        """
        Main chat interface that handles both agent and direct modes
        
        Args:
            message: User's message
            personality: NetworkChuck or Bloomy
            doc_search_enabled: Whether to search documentation
            doc_count: Number of documentation sources to include
            
        Returns:
            tuple: (response, sources_info, personality_used)
        """
        try:
            if self.mode == "agent":
                # Use LangChain agent system
                result = self.agent.chat(
                    message=message,
                    personality=personality.lower(),
                    doc_search_enabled=doc_search_enabled,
                    doc_count=doc_count
                )
                
                # Extract information from agent result
                response = result.get('response', 'No response generated')
                sources = result.get('sources', 0)
                tools_used = result.get('tools_used', [])
                
                # Create sources info
                if tools_used:
                    sources_info = f"🤖 Agent used: {', '.join(tools_used)} | Sources: {sources}"
                else:
                    sources_info = f"📝 Direct response | Sources: {sources}"
                
                return response, sources_info, personality
                
            else:
                # Use direct enhanced RAG
                result = self.enhanced_rag.generate_response(
                    user_query=message,
                    personality=personality.lower(),
                    doc_search_enabled=doc_search_enabled,
                    doc_count=doc_count
                )
                
                # Extract information from enhanced RAG result
                response = result.get('response', 'No response generated')
                sources = result.get('sources', 0)
                
                sources_info = f"🚀 Enhanced RAG | Sources: {sources}"
                
                return response, sources_info, personality
                
        except Exception as e:
            error_msg = f"Sorry, I encountered an error: {str(e)}"
            return error_msg, "❌ Error occurred", personality

# Initialize the chatbot system
print("🚀 Initializing NetworkChuck AI Chatbot...")
try:
    chatbot = NetworkChuckChatbot()
    print("✅ Chatbot system ready!")
except Exception as e:
    print(f"❌ Failed to initialize chatbot: {e}")
    raise

def chat_interface(message, personality, doc_search, doc_count, history):
    """Gradio chat interface function"""
    if not message.strip():
        return history, "", "Please enter a message!"
    
    # Get response from chatbot
    response, sources_info, used_personality = chatbot.chat(
        message=message,
        personality=personality,
        doc_search_enabled=doc_search,
        doc_count=doc_count
    )
    
    # Add to chat history
    history.append([message, response])
    
    return history, "", sources_info

def create_interface():
    """Create and configure the Gradio interface"""
    
    # Custom CSS for better styling
    custom_css = """
    .gradio-container {
        max-width: 1200px !important;
    }
    .chat-container {
        height: 600px;
    }
    """
    
    with gr.Blocks(
        title="NetworkChuck AI Chatbot", 
        theme=gr.themes.Soft(),
        css=custom_css
    ) as interface:
        
        # Header
        gr.Markdown("""
        # 🤖 NetworkChuck AI Chatbot
        ### Enhanced RAG System with LangChain Agents
        
        Ask me about **networking, cybersecurity, Linux, cloud computing** (NetworkChuck) or **Excel, finance, Bloomberg Terminal** (Bloomy)!
        """)
        
        with gr.Row():
            with gr.Column(scale=3):
                # Main chat interface
                chatbot_ui = gr.Chatbot(
                    label="Chat with NetworkChuck AI",
                    height=500,
                    show_copy_button=True,
                    type="messages"  # Use modern message format
                )
                
                # Message input
                msg_input = gr.Textbox(
                    label="Your Message",
                    placeholder="Ask me about networking, cybersecurity, Excel, or finance!",
                    lines=2,
                    max_lines=4
                )
                
                # Action buttons
                with gr.Row():
                    send_btn = gr.Button("💬 Send", variant="primary", scale=2)
                    clear_btn = gr.Button("🗑️ Clear Chat", scale=1)
                
                # Status display
                status_display = gr.Textbox(
                    label="System Status",
                    interactive=False,
                    max_lines=2
                )
            
            with gr.Column(scale=1):
                # Controls panel
                gr.Markdown("### 🎛️ **Controls**")
                
                personality_choice = gr.Radio(
                    choices=["NetworkChuck", "Bloomy"],
                    value="NetworkChuck",
                    label="🎭 Personality",
                    info="Choose your AI personality"
                )
                
                doc_search_toggle = gr.Checkbox(
                    value=True,
                    label="📚 Smart Documentation",
                    info="Include relevant documentation in responses"
                )
                
                doc_count_slider = gr.Slider(
                    minimum=1,
                    maximum=5,
                    value=3,
                    step=1,
                    label="📄 Documentation Sources",
                    info="Number of documentation sources to include"
                )
                
                # System info
                gr.Markdown(f"""
                ### 📊 **System Info**
                
                **Mode**: {"🤖 LangChain Agents" if AGENT_AVAILABLE else "🚀 Enhanced RAG"}
                
                **Features**:
                - ✅ Universal Knowledge Access
                - ✅ Smart Documentation Matching  
                - ✅ Dual Personalities (NetworkChuck + Bloomy)
                - ✅ Technical Query Detection
                - {"✅ Agent Coordination" if AGENT_AVAILABLE else "✅ Direct Enhanced RAG"}
                
                **Personalities**:
                - 🎯 **NetworkChuck**: Networking, cybersecurity, Linux, cloud
                - 💼 **Bloomy**: Excel, finance, Bloomberg Terminal, VBA
                """)
        
        # Event handlers
        def send_message(message, personality, doc_search, doc_count, history):
            return chat_interface(message, personality, doc_search, doc_count, history)
        
        # Send button click
        send_btn.click(
            fn=send_message,
            inputs=[msg_input, personality_choice, doc_search_toggle, doc_count_slider, chatbot_ui],
            outputs=[chatbot_ui, msg_input, status_display]
        )
        
        # Enter key press
        msg_input.submit(
            fn=send_message,
            inputs=[msg_input, personality_choice, doc_search_toggle, doc_count_slider, chatbot_ui],
            outputs=[chatbot_ui, msg_input, status_display]
        )
        
        # Clear chat
        clear_btn.click(
            fn=lambda: ([], "Chat cleared! Ready for new conversation."),
            outputs=[chatbot_ui, status_display]
        )
        
        # Example queries
        gr.Markdown("""
        ### 💡 **Try These Example Queries**
        
        **NetworkChuck Examples**:
        - "How do I set up a VPN server?"
        - "Explain Docker containers and networking"
        - "What's the difference between TCP and UDP?"
        
        **Bloomy Examples**:
        - "How do I use VLOOKUP in Excel?"
        - "Explain pivot tables for financial analysis"
        - "What are Bloomberg Terminal shortcuts?"
        """)
    
    return interface

# Create and launch the interface
if __name__ == "__main__":
    print("🌐 Creating Gradio interface...")
    interface = create_interface()
    
    # Auto-detect environment: Local vs Hugging Face Spaces
    is_huggingface = bool(os.getenv("SPACE_ID") or os.getenv("SPACE_AUTHOR_NAME"))
    
    if is_huggingface:
        print("🤗 Detected Hugging Face Spaces environment")
        server_name = "0.0.0.0"  # Required for HF Spaces
        server_port = 7860       # HF Spaces default port
    else:
        print("💻 Detected local development environment")
        server_name = "127.0.0.1"  # Localhost for local testing
        server_port = None         # Auto-find available port
    
    # Launch configuration
    interface.launch(
        server_name=server_name,
        server_port=server_port,
        share=False,              # Don't create public link (HF handles this)
        debug=False,              # Set to True for development debugging
        show_error=True,          # Show errors in interface
        inbrowser=not is_huggingface  # Auto-open browser locally only
    )