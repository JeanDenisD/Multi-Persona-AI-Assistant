"""
LLM-Controlled RAG - LLM decides what to retrieve
Complete version with fixed comprehensive memory logic + simple video integration + content filtering
FIXED: Float handling for start_time values
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
    LLM-controlled RAG with conversation memory + simple video integration + content filtering
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
        
        print(f"✅ LLM-Controlled RAG with Memory + Videos (window size: {memory_window_size})")
        
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
    
    def invoke_with_filters(self, input_dict: Dict[str, Any]) -> str:
        """Enhanced invoke with content filtering and retrieval settings"""
        query = input_dict["question"]
        personality = input_dict.get("personality", "networkchuck")
        gradio_history = input_dict.get("history", [])
        content_settings = input_dict.get("content_settings", {})
        similarity_threshold = input_dict.get("similarity_threshold", 0.3)
        llm_temperature = input_dict.get("llm_temperature", 0.7)
        
        print(f"🎯 Processing with filters: {content_settings}")
        print(f"📊 Similarity threshold: {similarity_threshold}, Temperature: {llm_temperature}")
        
        # Update generator LLM temperature
        self.generator_llm.temperature = llm_temperature
        
        # Step 1: Update memory from Gradio history if provided
        self._sync_memory_with_gradio_history(gradio_history)
        
        # Step 2: Check if we should apply tech analogies filter
        enable_analogies = content_settings.get('enable_analogies', True)
        
        # Step 3: LLM Controller decides what to retrieve (with memory context)
        retrieval_strategy = self._get_retrieval_strategy(query, personality, enable_analogies)
        
        # Step 4: Retrieve content based on LLM's decision with similarity filtering
        context = self._retrieve_content_with_filters(query, retrieval_strategy, similarity_threshold)
        
        # Step 5: LLM Generator creates response with personality and memory
        response = self._generate_response_with_filters(query, context, personality, retrieval_strategy, content_settings)
        
        # Step 6: Save this interaction to memory
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
    
    def _get_retrieval_strategy(self, query: str, personality: str, enable_analogies: bool = True) -> Dict[str, Any]:
        """LLM decides what type of content to retrieve (with memory-aware logic and analogy control)"""
        
        # Get conversation history for context
        memory_context = self._get_memory_context()
        
        # Modify controller prompt based on analogy setting
        base_prompt = get_controller_prompt_template()
        if not enable_analogies and not self._is_tech_query(query):
            analogy_instruction = "\n\nIMPORTANT: User has disabled tech analogies for non-technical questions. Avoid suggesting technical comparisons for casual/non-tech topics."
            base_prompt += analogy_instruction
        
        controller_prompt = ChatPromptTemplate.from_template(base_prompt)
        
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
    
    def _is_tech_query(self, query: str) -> bool:
        """Check if query is technical in nature"""
        tech_keywords = [
            'docker', 'network', 'programming', 'code', 'server', 'database',
            'excel', 'vlookup', 'python', 'linux', 'security', 'vpn',
            'install', 'configure', 'setup', 'command', 'function'
        ]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in tech_keywords)
    
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
        
        # Store docs for video processing
        self._last_doc_score_pairs = doc_score_pairs
        
        # Format context
        context = self.retriever.format_context(doc_score_pairs)
        print(f"🔍 DEBUG: Final context length: {len(context)} chars")
        
        return context
    
    def _retrieve_content_with_filters(self, query: str, strategy: Dict[str, Any], similarity_threshold: float) -> str:
        """Retrieve content with similarity threshold filtering"""
        
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
        print(f"📊 DEBUG: Using similarity threshold: {similarity_threshold}")
        
        # Get documents
        doc_score_pairs = self.retriever.retrieve_context(search_terms, top_k=10)  # Get more initially
        
        # Apply similarity threshold filtering
        filtered_docs = [(doc, score) for doc, score in doc_score_pairs if score >= similarity_threshold]
        
        print(f"🔍 DEBUG: Found {len(doc_score_pairs)} documents, {len(filtered_docs)} above threshold {similarity_threshold}")
        
        # Take top 5 after filtering
        doc_score_pairs = filtered_docs[:5]
        
        # Store docs for video processing
        self._last_doc_score_pairs = doc_score_pairs
        
        # Format context
        context = self.retriever.format_context(doc_score_pairs)
        print(f"🔍 DEBUG: Final context length: {len(context)} chars")
        
        return context
    
    def extract_video_info(self, doc_score_pairs):
        """Extract video info from documents - FIXED for float handling"""
        videos = {}
        
        for doc, score in doc_score_pairs:
            video_id = doc.metadata.get('video_id', '')
            video_title = doc.metadata.get('video_title', 'Unknown Video')
            video_url = doc.metadata.get('video_url', '')
            start_time = doc.metadata.get('start_time', 0)
            
            if not video_id:
                continue
                
            # FIX: Convert start_time to int to handle floats
            try:
                start_time = int(float(start_time)) if start_time else 0
            except (ValueError, TypeError):
                start_time = 0
                
            if video_id not in videos:
                videos[video_id] = {
                    'title': video_title,
                    'url': video_url,
                    'timestamps': [],
                    'max_score': score
                }
            
            videos[video_id]['timestamps'].append({
                'time': start_time,
                'score': score
            })
            videos[video_id]['max_score'] = max(videos[video_id]['max_score'], score)
        
        # Sort by relevance
        video_list = list(videos.values())
        video_list.sort(key=lambda x: x['max_score'], reverse=True)
        
        return video_list

    def format_video_links(self, video_list):
        """Format video links for display"""
        if not video_list:
            return ""
        
        links = ["\n🎥 **Source Videos:**"]
        
        for i, video in enumerate(video_list[:3], 1):  # Max 3 videos
            title = video['title']
            url = video['url']
            
            links.append(f"{i}. **[{title}]({url})**")
            
            # Add best timestamps
            timestamps = sorted(video['timestamps'], key=lambda x: x['score'], reverse=True)
            for ts in timestamps[:2]:  # Max 2 timestamps per video
                time_str = self.format_time(ts['time'])
                timestamp_url = f"{url}&t={ts['time']}s" if '?' in url else f"{url}?t={ts['time']}s"
                links.append(f"   • [{time_str}]({timestamp_url})")
        
        return "\n".join(links)

    def format_time(self, seconds):
        """Format seconds to MM:SS - FIXED for float handling"""
        if not seconds:
            return "0:00"
        
        # FIX: Convert to int to handle floats
        try:
            seconds = int(float(seconds))
        except (ValueError, TypeError):
            return "0:00"
        
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}:{secs:02d}"
    
    def _generate_response(self, query: str, context: str, personality: str, strategy: Dict[str, Any]) -> str:
        """Generate response with IMPROVED memory prioritization + simple video links""" 
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
            
            return response.content  # No video links for memory queries
            
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

        # START OF VIDEO INTEGRATION - Add video links for non-memory queries
        final_response = response.content
        
        if not is_memory_focus and hasattr(self, '_last_doc_score_pairs'):
            try:
                video_list = self.extract_video_info(self._last_doc_score_pairs)
                video_links = self.format_video_links(video_list)
                if video_links:
                    final_response += "\n\n" + video_links
            except Exception as e:
                print(f"⚠️ Video processing error: {e}")
                # Continue without video links if there's an error
        # END OF VIDEO INTEGRATION

        # Add documentation if needed (but not for memory-focused queries)
        if not is_memory_focus and self._should_add_docs(query):
            doc_matches = self.doc_matcher.match_documentation(query, top_k=3, min_similarity=0.2)
            doc_links = self.doc_matcher.format_documentation_links(doc_matches)
            if doc_links:
                final_response += "\n\n" + doc_links
        
        return final_response
    
    def _generate_response_with_filters(self, query: str, context: str, personality: str, strategy: Dict[str, Any], content_settings: dict) -> str:
        """Generate response with content filtering applied"""
        
        # Generate the base response using existing method
        base_response = self._generate_response(query, context, personality, strategy)
        
        # Apply content filters
        filtered_response = base_response
        
        # Remove videos if disabled
        if not content_settings.get('enable_videos', True):
            filtered_response = self._remove_video_sections(filtered_response)
            print("🎥 Videos filtered out")
        
        # Remove documentation if disabled
        if not content_settings.get('enable_docs', True):
            filtered_response = self._remove_doc_sections(filtered_response)
            print("📚 Documentation filtered out")
        
        return filtered_response
    
    def _remove_video_sections(self, response_text: str) -> str:
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
    
    def _remove_doc_sections(self, response_text: str) -> str:
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