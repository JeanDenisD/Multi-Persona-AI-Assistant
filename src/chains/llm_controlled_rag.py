"""
LLM-Controlled RAG - LLM decides what to retrieve
Complete version with fixed comprehensive memory logic
"""

import os
from typing import Dict, Any, List
from urllib import response
from langchain.schema.runnable import Runnable, RunnableLambda
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import HumanMessage, AIMessage

from ..core.retriever import RAGRetriever
from ..core.personality import PersonalityPromptManager
from ..core.doc_matcher import SmartDocumentationMatcher
from ..prompts.llm_controller_prompts import get_controller_prompt_template


class LLMControlledRAG(Runnable):
    """
    LLM-controlled RAG with conversation memory
    """
    
    def __init__(self, memory_window_size: int = 10):
        self.retriever = RAGRetriever()
        self.personality_manager = PersonalityPromptManager()
        self.doc_matcher = SmartDocumentationMatcher()
        self.controller_llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.2)
        self.generator_llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)
        
        # Initialize LangChain Memory
        self.memory = ConversationBufferWindowMemory(
            k=memory_window_size,  # Keep last N conversation turns
            return_messages=True,  # Return as message objects
            memory_key="chat_history"
        )
        
        print(f"✅ LLM-Controlled RAG with Memory (window size: {memory_window_size})")
        
    def invoke(self, input_dict: Dict[str, Any]) -> str:
        """LLM-controlled RAG process with memory integration"""
        query = input_dict["question"]
        personality = input_dict.get("personality", "networkchuck")
        gradio_history = input_dict.get("history", [])
        
        # Step 1: Update memory from Gradio history if provided
        self._sync_memory_with_gradio_history(gradio_history)
        
        # Step 2: LLM Controller decides what to retrieve (with memory context)
        retrieval_strategy = self._get_retrieval_strategy(query, personality)
        
        # Step 3: Retrieve content based on LLM's decision
        context = self._retrieve_content(query, retrieval_strategy)
        
        # Step 4: LLM Generator creates response with personality and memory
        response = self._generate_response(query, context, personality, retrieval_strategy)
        
        # Step 5: Save this interaction to memory
        self.memory.save_context(
            {"input": query},
            {"output": response}
        )
        
        return response
    
    def _sync_memory_with_gradio_history(self, gradio_history: List[List[str]]):
        """
        Sync LangChain memory with Gradio chat history
        gradio_history format: [[user_msg, bot_msg], [user_msg, bot_msg], ...]
        """
        if not gradio_history:
            return
            
        # Clear existing memory to avoid duplication
        self.memory.clear()
        
        # Convert Gradio history to LangChain memory format
        for turn in gradio_history:
            if len(turn) >= 2 and turn[0] and turn[1]:  # Both user and bot messages exist
                user_msg = turn[0]
                bot_msg = turn[1]
                
                # Add to memory
                self.memory.save_context(
                    {"input": user_msg},
                    {"output": bot_msg}
                )
        
        print(f"🧠 Memory synced with {len(gradio_history)} conversation turns")
    
    def _get_retrieval_strategy(self, query: str, personality: str) -> Dict[str, Any]:
        """LLM decides what type of content to retrieve (with memory-aware logic)"""
        
        # Get conversation history for context
        memory_context = self._get_memory_context()
        
        controller_prompt = ChatPromptTemplate.from_template(
            get_controller_prompt_template()
        )
        
        result = self.controller_llm.invoke(
            controller_prompt.format(
                query=query, 
                personality=personality,
                memory_context=memory_context
            )
        )
        
        # Parse the controller's decision with new fields
        content = result.content
        strategy = {
            "query_type": self._extract_field(content, "QUERY_TYPE"),
            "search_terms": self._extract_field(content, "SEARCH_TERMS"),
            "content_type": self._extract_field(content, "CONTENT_TYPE"),
            "avoid_bias": self._extract_field(content, "AVOID_BIAS"),
            "focus_area": self._extract_field(content, "FOCUS_AREA"),
            "reasoning": self._extract_field(content, "REASONING")
        }
        
        print(f"🧠 Controller Decision: {strategy['query_type']} - {strategy['reasoning']}")
        
        return strategy
    
    def _get_memory_context(self) -> str:
        """Format memory context for the controller LLM - COMPLETE VERSION"""
        try:
            # Get chat history from memory
            messages = self.memory.chat_memory.messages
            
            if not messages:
                return "No previous conversation."
            
            # Format ALL recent exchanges (not just selective ones)
            context_parts = []
            
            # Process in pairs (human, ai) but include MORE context
            for i in range(0, len(messages), 2):
                if i + 1 < len(messages):
                    human_msg = messages[i].content
                    ai_msg = messages[i + 1].content
                    
                    # Don't truncate - include full context for better recall
                    context_parts.append(f"User: {human_msg}")
                    context_parts.append(f"Assistant: {ai_msg[:300]}...")  # Increased from 200 to 300
            
            # Include MORE conversation history (not just last 3 exchanges)
            # Take last 8 messages (4 full exchanges) instead of 6
            recent_context = "\n".join(context_parts[-8:])
            
            return recent_context
            
        except Exception as e:
            print(f"⚠️ Error getting memory context: {e}")
            return "Memory context unavailable."
    
    def _generate_comprehensive_memory_summary(self, query: str) -> str:
        """
        Generate a comprehensive summary of conversation for memory queries
        This method provides better topic coverage for "what did we discuss" questions
        """
        try:
            messages = self.memory.chat_memory.messages
            
            if not messages:
                return "No previous conversation to summarize."
            
            # Identify distinct topics discussed
            topics_covered = []
            conversation_flow = []
            
            # Analyze all exchanges for topics
            for i in range(0, len(messages), 2):
                if i + 1 < len(messages):
                    user_msg = messages[i].content.lower()
                    ai_response = messages[i + 1].content
                    
                    # Extract topic keywords from user questions
                    if "docker" in user_msg:
                        if "docker" not in [t["topic"] for t in topics_covered]:
                            topics_covered.append({
                                "topic": "docker", 
                                "details": "Docker containers and containerization",
                                "response_snippet": ai_response[:150] + "..."
                            })
                    
                    if "compose" in user_msg:
                        if "docker compose" not in [t["topic"] for t in topics_covered]:
                            topics_covered.append({
                                "topic": "docker compose",
                                "details": "Docker Compose for multi-container applications", 
                                "response_snippet": ai_response[:150] + "..."
                            })
                    
                    if "excel" in user_msg or "vlookup" in user_msg:
                        if "excel" not in [t["topic"] for t in topics_covered]:
                            topics_covered.append({
                                "topic": "excel",
                                "details": "Excel VLOOKUP functions and data analysis",
                                "response_snippet": ai_response[:150] + "..."
                            })
                    
                    if "python" in user_msg:
                        if "python" not in [t["topic"] for t in topics_covered]:
                            topics_covered.append({
                                "topic": "python",
                                "details": "Python programming and scripting",
                                "response_snippet": ai_response[:150] + "..."
                            })
                    
                    if "network" in user_msg or "vpn" in user_msg:
                        if "networking" not in [t["topic"] for t in topics_covered]:
                            topics_covered.append({
                                "topic": "networking",
                                "details": "Networking, VPNs, and network security",
                                "response_snippet": ai_response[:150] + "..."
                            })
                    
                    if "linux" in user_msg or "ubuntu" in user_msg:
                        if "linux" not in [t["topic"] for t in topics_covered]:
                            topics_covered.append({
                                "topic": "linux",
                                "details": "Linux systems and administration",
                                "response_snippet": ai_response[:150] + "..."
                            })
                    
                    # Add more topic detection as needed
            
            # Format comprehensive summary
            if topics_covered:
                summary_parts = ["In our conversation, we've covered:"]
                for i, topic_info in enumerate(topics_covered, 1):
                    summary_parts.append(f"{i}. **{topic_info['topic'].title()}**: {topic_info['details']}")
                    summary_parts.append(f"   Summary: {topic_info['response_snippet']}")
                
                return "\n".join(summary_parts)
            else:
                # Fallback to recent conversation if no topics detected
                return self._get_memory_context()
            
        except Exception as e:
            print(f"⚠️ Error generating comprehensive summary: {e}")
            return self._get_memory_context()
    
    def _extract_field(self, content: str, field: str) -> str:
        """Extract field from controller response"""
        for line in content.split('\n'):
            if field in line:
                return line.split(':', 1)[1].strip() if ':' in line else ""
        return ""
    
    def _retrieve_content(self, query: str, strategy: Dict[str, Any]) -> str:
        """Retrieve content based on LLM controller's strategy (with memory logic)"""
        
        query_type = strategy.get("query_type", "NORMAL_SEARCH")
        
        # Handle memory-priority queries
        if query_type == "MEMORY_PRIORITY":
            print("🧠 MEMORY_PRIORITY detected - using memory as primary source")
            return "MEMORY_FOCUS"  # Special flag for generator
        
        # For context/normal search, proceed with retrieval
        search_terms = strategy.get("search_terms", query)
        if search_terms == "use_memory" or not search_terms:
            search_terms = query  # Fallback to original query
        
        print(f"🔍 DEBUG: Search query: {search_terms}")
        print(f"🔍 DEBUG: Strategy: {strategy}")
        
        # Get documents
        doc_score_pairs = self.retriever.retrieve_context(search_terms, top_k=5)
        
        print(f"🔍 DEBUG: Found {len(doc_score_pairs)} documents before filtering")
        
        # Filter out personality-biased content if controller requested
        if strategy.get("avoid_bias", "").lower() == "yes":
            filtered_docs = []
            for doc, score in doc_score_pairs:
                content = doc.page_content.lower()
                # Check what personality markers are found
                nc_markers = ["hey guys", "chuck here", "what's up", "coffee time", "alright my friend"]
                found_markers = [marker for marker in nc_markers if marker in content]
                
                if not found_markers:
                    filtered_docs.append((doc, score))
                    print(f"✅ DEBUG: Kept neutral content (score: {score:.3f})")
                else:
                    print(f"❌ DEBUG: Filtered out biased content with markers: {found_markers}")
            
            doc_score_pairs = filtered_docs[:3]
            print(f"🔍 DEBUG: {len(doc_score_pairs)} documents after filtering")
        
        # For context search, limit retrieval slightly
        if query_type == "CONTEXT_SEARCH":
            doc_score_pairs = doc_score_pairs[:3]  # Fewer docs for context queries
            print("🧠 Limited retrieval for context-aware query")
        
        # Format context
        context = self.retriever.format_context(doc_score_pairs)
        print(f"🔍 DEBUG: Final context length: {len(context)} chars")
        
        return context
    
    def _generate_response(self, query: str, context: str, personality: str, strategy: Dict[str, Any]) -> str:
        """Generate response with IMPROVED memory prioritization""" 
        # Import the personality descriptions
        from ..prompts.personality_prompts import get_personality_description
        
        # Get the personality description from external file
        personality_description = get_personality_description(personality)
        
        # Check if this is a memory-focused query
        query_type = strategy.get("query_type", "NORMAL_SEARCH")
        is_memory_focus = (context == "MEMORY_FOCUS" or query_type == "MEMORY_PRIORITY")
        
        if is_memory_focus:
            print("🧠 Generating COMPREHENSIVE MEMORY-FOCUSED response")
            
            # Use comprehensive memory summary for better topic coverage
            comprehensive_summary = self._generate_comprehensive_memory_summary(query)
            
            # Memory-priority response template with better coverage
            system_prompt = """{personality_description}
            
            The user is asking about our previous conversation. Use the comprehensive conversation summary below to provide a complete answer.
            
            COMPREHENSIVE CONVERSATION SUMMARY:
            {comprehensive_summary}
            
            User Question: {query}
            
            Respond as {personality_name} by providing a thorough recap of ALL topics we discussed. Include:
            - All major topics covered (Docker, Excel, Python, etc.)
            - Key points from each discussion
            - Any analogies or examples used
            - References to different personalities if relevant
            
            Use phrases like:
            - "In our conversation, we covered several topics..."
            - "We discussed [topic 1], then moved on to [topic 2]..."
            - "To recap everything we've talked about..."
            - "Our conversation included both [topic A] and [topic B]..."
            
            Be comprehensive - don't leave out any topics we discussed!"""
            
            response = self.generator_llm.invoke([{
                "role": "system", 
                "content": system_prompt.format(
                    personality_description=personality_description,
                    comprehensive_summary=comprehensive_summary,
                    query=query,
                    personality_name=personality.title()
                )
            }])
            
        elif query_type == "CONTEXT_SEARCH":
            print("🧠 Generating CONTEXT-AWARE response")
            
            # Get regular memory context for context-aware responses
            memory_context = self._get_memory_context()
            
            # Context-aware response (builds on previous topics)
            system_prompt = """{personality_description}
            
            CONVERSATION HISTORY:
            {memory_context}
            
            CURRENT CONTEXT: {context}
            
            User Question: {query}
            
            This question builds on our previous conversation. Respond as {personality_name} by:
            1. Briefly referencing our previous discussion if relevant
            2. Using the current context to provide new information
            3. Building progressively on what we've already covered"""
            
            response = self.generator_llm.invoke([{
                "role": "system", 
                "content": system_prompt.format(
                    personality_description=personality_description,
                    memory_context=memory_context,
                    context=context,
                    query=query,
                    personality_name=personality.title()
                )
            }])
            
        else:
            print("🧠 Generating NORMAL response with memory awareness")
            
            # Get regular memory context
            memory_context = self._get_memory_context()
            
            # Normal response with memory awareness
            system_prompt = """{personality_description}
            
            CONVERSATION HISTORY:
            {memory_context}
            
            CURRENT CONTEXT: {context}
            
            User Question: {query}
            
            Respond as {personality_name} using both our conversation history and the current context. 
            If this relates to something we discussed earlier, reference it appropriately."""
            
            response = self.generator_llm.invoke([{
                "role": "system", 
                "content": system_prompt.format(
                    personality_description=personality_description,
                    memory_context=memory_context,
                    context=context,
                    query=query,
                    personality_name=personality.title()
                )
            }])

        # Add documentation if needed (but not for memory-focused queries)
        if not is_memory_focus and self._should_add_docs(query):
            doc_matches = self.doc_matcher.match_documentation(query, top_k=3, min_similarity=0.2)
            doc_links = self.doc_matcher.format_documentation_links(doc_matches)
            if doc_links:
                return response.content + "\n\n" + doc_links
        
        return response.content
    
    def _should_add_docs(self, query: str) -> bool:
        """Check if documentation should be added"""
        casual_patterns = ['hello', 'hi', 'how are you', 'thanks', 'bye']
        return not any(pattern in query.lower() for pattern in casual_patterns)
    
    def _is_memory_query(self, query: str) -> bool:
        """Quick check if query is asking for memory recall"""
        memory_indicators = [
            "remind me", "what did we", "we discussed", "you mentioned", 
            "our conversation", "earlier", "previous", "recall"
        ]
        query_lower = query.lower()
        return any(indicator in query_lower for indicator in memory_indicators)
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """Get summary of current memory state"""
        try:
            messages = self.memory.chat_memory.messages
            return {
                "total_messages": len(messages),
                "conversation_turns": len(messages) // 2,
                "memory_window_size": self.memory.k,
                "memory_active": len(messages) > 0
            }
        except Exception as e:
            return {"error": str(e), "memory_active": False}
    
    def clear_memory(self):
        """Clear conversation memory"""
        self.memory.clear()
        print("🧠 Memory cleared")