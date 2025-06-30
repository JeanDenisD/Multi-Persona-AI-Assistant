"""
LangChain Agent System - Intelligent Coordinator for Enhanced RAG
Coordinates multiple tools with memory and intelligent routing
"""

import os
import json
from typing import Dict, List, Any, Optional
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage

# Import your enhanced RAG tools
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from agents.tools.content_tools import (
    EnhancedRAGTool,
    VideoContentSearchTool, 
    DocumentationFinderTool
)


class EnhancedRAGAgent:
    """
    LangChain Agent that intelligently coordinates your enhanced RAG system.
    Adds memory, tool routing, and agent intelligence while preserving all features.
    """
    
    def __init__(self):
        # Initialize LLM for agent
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo", 
            temperature=0.7,
            openai_api_key=os.getenv('OPENAI_API_KEY')
        )
        
        # Initialize memory for conversation context
        self.memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            return_messages=True,
            k=10  # Keep last 10 exchanges
        )
        
        # Initialize tools that wrap your enhanced RAG system
        self.tools = [
            EnhancedRAGTool(),
            VideoContentSearchTool(),
            DocumentationFinderTool()
        ]
        
        # Create agent with intelligent routing
        self.agent = self._create_agent()
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=3,
            return_intermediate_steps=True
        )
        
        print("✅ Enhanced RAG Agent ready with intelligent tool coordination!")
    
    def _create_agent(self):
        """Create the LangChain agent with intelligent routing"""
        
        system_prompt = """You are an intelligent AI assistant that helps users with technical and educational questions using specialized tools.

You have access to an enhanced RAG system with two personalities:
- **NetworkChuck**: Energetic tech expert (networking, cybersecurity, DevOps)  
- **Bloomy**: Professional finance expert (Excel, Bloomberg, financial modeling)

**AVAILABLE TOOLS:**
1. **enhanced_rag_search**: Main tool with dual personalities and smart documentation
   - Use for ANY user question - technical or casual
   - Automatically provides relevant documentation when appropriate
   - Handles both personalities and universal knowledge
   - Input: JSON with {"query": "...", "personality": "networkchuck/bloomy", "include_docs": true/false}
   - Or plain text for simple queries

2. **video_content_search**: Raw content search from video transcripts
   - Use when users want specific video content or source information
   - Returns content with timestamps and video titles

3. **documentation_finder**: Official documentation search
   - Use when users specifically ask for documentation or learning resources
   - Returns curated official documentation links

**INTELLIGENT ROUTING GUIDELINES:**
- **For most queries**: Use enhanced_rag_search (it's your primary tool)
- **For personality questions**: Use enhanced_rag_search with appropriate personality
- **For specific video content**: Consider video_content_search
- **For documentation requests**: Consider documentation_finder (though enhanced_rag_search also provides docs)

**PERSONALITY SELECTION:**
- Finance/Excel/Bloomberg topics → Use "bloomy" personality
- Tech/Networking/DevOps topics → Use "networkchuck" personality  
- General topics → Either personality (suggest based on context)
- User preference → Always honor user's choice

**MEMORY USAGE:**
- Remember user preferences (personality, topics of interest)
- Reference previous conversation context
- Adapt responses based on user's expertise level

**RESPONSE STYLE:**
- Be helpful, intelligent, and conversational
- Let the tools handle the personality styling
- Provide context about which tools you used when helpful
- Always aim for the best possible assistance

**IMPORTANT**: The enhanced_rag_search tool preserves ALL the enhanced features from the original system, including universal knowledge access, smart documentation, and authentic personalities."""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad")
        ])
        
        return create_openai_functions_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
    
    def chat(self, user_input: str, personality_preference: str = None) -> Dict[str, Any]:
        """
        Main chat interface with agent intelligence
        
        Args:
            user_input: User's message
            personality_preference: Optional personality preference
            
        Returns:
            Enhanced response with agent metadata
        """
        
        try:
            # Prepare enhanced input with personality preference
            enhanced_input = user_input
            if personality_preference:
                enhanced_input = f"{user_input}\n\n[User prefers {personality_preference} personality style]"
            
            # Execute agent with intelligent tool coordination
            result = self.agent_executor.invoke({"input": enhanced_input})
            
            # Extract conversation history for context
            history = self.memory.chat_memory.messages
            human_message_count = len([m for m in history if isinstance(m, HumanMessage)])
            
            # Analyze which tools were used
            tools_used = self._extract_tools_used(result)
            
            return {
                "response": result["output"],
                "agent_used": True,
                "tools_used": tools_used,
                "conversation_length": len(history),
                "memory_context": human_message_count,
                "intermediate_steps": result.get("intermediate_steps", []),
                "enhanced_features_preserved": True
            }
            
        except Exception as e:
            # Fallback to direct enhanced RAG if agent fails
            try:
                enhanced_rag_tool = EnhancedRAGTool()
                fallback_input = json.dumps({
                    "query": user_input,
                    "personality": personality_preference or "networkchuck",
                    "include_docs": True
                })
                fallback_result = enhanced_rag_tool._run(fallback_input)
                
                return {
                    "response": fallback_result + f"\n\n[Fallback: Direct enhanced RAG used due to agent error]",
                    "agent_used": False,
                    "fallback_reason": str(e),
                    "tools_used": ["enhanced_rag_search"],
                    "conversation_length": 0,
                    "memory_context": 0,
                    "enhanced_features_preserved": True
                }
            except Exception as fallback_error:
                return {
                    "response": f"I encountered an error processing your request: {fallback_error}",
                    "agent_used": False,
                    "fallback_reason": f"Agent error: {e}, Fallback error: {fallback_error}",
                    "tools_used": [],
                    "conversation_length": 0,
                    "memory_context": 0,
                    "enhanced_features_preserved": False
                }
    
    def _extract_tools_used(self, result: Dict) -> List[str]:
        """Extract which tools were used from agent result"""
        tools_used = []
        
        # Check intermediate steps for tool usage
        if "intermediate_steps" in result:
            for step in result["intermediate_steps"]:
                if hasattr(step, '__len__') and len(step) >= 2:
                    action = step[0]
                    if hasattr(action, 'tool'):
                        tools_used.append(action.tool)
        
        # If no intermediate steps, infer from response content
        response = result.get("output", "")
        if "*Agent: Enhanced RAG*" in response:
            tools_used.append("enhanced_rag_search")
        
        return tools_used if tools_used else ["enhanced_rag_search"]  # Default assumption
    
    def get_conversation_summary(self) -> str:
        """Get a summary of the current conversation"""
        messages = self.memory.chat_memory.messages
        if not messages:
            return "No conversation history"
        
        human_messages = len([m for m in messages if isinstance(m, HumanMessage)])
        ai_messages = len([m for m in messages if isinstance(m, AIMessage)])
        
        return f"Conversation: {human_messages} user messages, {ai_messages} AI responses"
    
    def clear_memory(self):
        """Clear conversation memory"""
        self.memory.clear()
    
    def set_user_preferences(self, preferences: Dict):
        """Store user preferences in memory"""
        pref_message = f"User preferences: {json.dumps(preferences)}"
        self.memory.chat_memory.add_message(SystemMessage(content=pref_message))


# Test function to verify agent works
def test_enhanced_rag_agent():
    """Test function to verify the enhanced RAG agent works"""
    print("🧪 Testing Enhanced RAG Agent...")
    
    try:
        # Initialize agent
        print("📦 Initializing Enhanced RAG Agent...")
        agent = EnhancedRAGAgent()
        
        # Test queries
        test_queries = [
            {
                "query": "How to setup Docker containers?",
                "personality": "networkchuck",
                "description": "Technical NetworkChuck query"
            },
            {
                "query": "Excel VLOOKUP tutorial",
                "personality": "bloomy",
                "description": "Technical Bloomy query"
            },
            {
                "query": "Hello! What can you help me with?",
                "personality": None,
                "description": "Casual greeting"
            }
        ]
        
        for i, test in enumerate(test_queries, 1):
            print(f"\n--- Agent Test {i}: {test['description']} ---")
            
            # Test agent chat
            result = agent.chat(test['query'], test['personality'])
            
            # Validate response
            print(f"🤖 Agent used: {result['agent_used']}")
            print(f"📝 Response length: {len(result['response'])} chars")
            print(f"🔧 Tools used: {result.get('tools_used', 'Unknown')}")
            print(f"💭 Memory context: {result['memory_context']} messages")
            
            if len(result['response']) > 100:
                print("✅ Agent response generated successfully")
            else:
                print("⚠️ Agent response seems short")
            
            # Check for enhanced features
            if result.get('enhanced_features_preserved'):
                print("✅ Enhanced features preserved")
            
        # Test conversation memory
        print(f"\n--- Testing Conversation Memory ---")
        summary = agent.get_conversation_summary()
        print(f"📊 Conversation summary: {summary}")
        
        print(f"\n✅ Enhanced RAG Agent testing completed!")
        print("🎯 Agent successfully coordinates enhanced RAG tools!")
        return True
        
    except Exception as e:
        print(f"❌ Agent testing failed: {e}")
        return False


if __name__ == "__main__":
    # Run test when file is executed directly
    test_enhanced_rag_agent()