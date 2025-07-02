"""
NetworkChuck AI Chatbot - Enhanced Gradio Interface (Gradio 4.44.0 Compatible)
"""

import os
import gradio as gr
from src.core.chatbot import NetworkChuckChatbot

# Global variable to track current personality
current_personality = "NetworkChuck"

def create_interface():
    """Create enhanced Gradio interface compatible with 4.44.0"""
    chatbot = NetworkChuckChatbot()
    
    def chat_with_personality(message, history):
        """Enhanced chat function with personality"""
        global current_personality
        print(f"🎭 DEBUG: Chat using personality: {current_personality}")
        
        # Use global personality state
        response = chatbot.chat_response(message, history, current_personality)
        return response
    
    def clear_conversation():
        """Clear conversation and reset"""
        return [], "🗑️ Conversation cleared"
    
    def switch_to_networkchuck():
        """Switch to NetworkChuck personality"""
        global current_personality
        current_personality = "NetworkChuck"
        print(f"🎭 DEBUG: Switched to NetworkChuck")
        return "✅ Using NetworkChuck personality"

    def switch_to_bloomy():
        """Switch to Bloomy personality"""
        global current_personality
        current_personality = "Bloomy"
        print(f"🎭 DEBUG: Switched to Bloomy")
        return "✅ Using Bloomy personality"
    
    # Custom CSS for better styling
    custom_css = """
    .gradio-container {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .status-good {
        background-color: #d4edda;
        color: #155724;
        padding: 0.75rem;
        border-radius: 8px;
        border: 1px solid #c3e6cb;
        font-weight: 500;
    }
    """
    
    with gr.Blocks(
        theme=gr.themes.Soft(),
        title="NetworkChuck AI Assistant",
        css=custom_css
    ) as app:
        
        # Header
        gr.HTML("""
        <div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 10px; margin-bottom: 2rem;">
            <h1>🚀 NetworkChuck AI Assistant</h1>
            <p>Enhanced RAG system with NetworkChuck & Bloomy personalities</p>
            <p><strong>Features:</strong> Smart Documentation • Personality Switching • Context-Aware Responses</p>
        </div>
        """)
        
        with gr.Row():
            with gr.Column(scale=4):
                # Personality controls with tab-style selector
                with gr.Group():
                    gr.HTML('<div style="margin-bottom: 0.5rem;"><strong>🎭 Choose Personality</strong></div>')
                    
                    # Tab-style personality selector
                    with gr.Row():
                        networkchuck_btn = gr.Button(
                            "NetworkChuck",
                            variant="primary",
                            size="lg"
                        )
                        bloomy_btn = gr.Button(
                            "Bloomy", 
                            variant="secondary",
                            size="lg"
                        )
                
                # Status at the same level
                with gr.Group():
                    status_display = gr.Textbox(
                        value="✅ Using NetworkChuck personality",
                        label="Current Status",
                        interactive=False,
                        elem_classes="status-good"
                    )
                    
                    clear_btn = gr.Button(
                        "🗑️ Clear Conversation",
                        variant="secondary",
                        size="sm"
                    )
            
            with gr.Column(scale=1):
                # System info
                gr.Markdown("""
                ### 📊 System Info
                **RAG Type:** LLM-Controlled  
                **Personalities:** 2 Active  
                **Documentation:** Auto-matched  
                **Context Filtering:** Enabled  
                """)
        
        # Main chat interface - simplified for Gradio 4.44.0
        with gr.Row():
            with gr.Column():
                chat_interface = gr.ChatInterface(
                    fn=chat_with_personality,
                    chatbot=gr.Chatbot(
                        height=600,
                        show_label=False,
                        container=True,
                        show_copy_button=True
                    ),
                    textbox=gr.Textbox(
                        placeholder="Ask about networking, cybersecurity, Excel, finance, or anything else...",
                        scale=7
                    )
                )
        
        # Footer with examples
        gr.Markdown("""
        ### 💡 Try These Examples:
        **NetworkChuck Style:** "How to setup Docker containers?" • "VPN configuration guide" • "Network troubleshooting tips"  
        **Bloomy Style:** "Excel VLOOKUP tutorial" • "Financial modeling best practices" • "Bloomberg Terminal shortcuts"
        """)
        
        # Event handlers
        networkchuck_btn.click(
            fn=switch_to_networkchuck,
            outputs=[status_display]
        )

        bloomy_btn.click(
            fn=switch_to_bloomy,
            outputs=[status_display]
        )

        clear_btn.click(
            fn=clear_conversation,
            outputs=[chat_interface.chatbot, status_display]
        )
    
    return app


if __name__ == "__main__":
    app = create_interface()
    app.launch()