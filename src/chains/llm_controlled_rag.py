"""
LLM-Controlled RAG - Complete version with Max Documents Control
LLM decides what to retrieve + modern LangChain memory + advanced filtering
"""

import os
from typing import Dict, Any, List
from urllib import response
from langchain.schema.runnable import Runnable, RunnableLambda
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.messages import trim_messages, HumanMessage, AIMessage, SystemMessage
from langchain.schema import HumanMessage as LegacyHumanMessage, AIMessage as LegacyAIMessage

from ..core.retriever import RAGRetriever
from ..core.personality import PersonalityPromptManager
from ..core.doc_matcher import SmartDocumentationMatcher
from ..prompts.llm_controller_prompts import get_controller_prompt_template


class ModernConversationMemory:
    """Modern replacement for ConversationBufferWindowMemory using trim_messages"""
    
    def __init__(self, k: int = 10, memory_key: str = "chat_history", return_messages: bool = True):
        self.k = k  # Window size
        self.memory_key = memory_key
        self.return_messages = return_messages
        self.chat_memory = type('ChatMemory', (), {'messages': []})()  # Simple message store
    
    def save_context(self, inputs: dict, outputs: dict):
        """Save context from this conversation to buffer"""
        try:
            # Add user message
            if "input" in inputs and inputs["input"]:
                self.chat_memory.messages.append(HumanMessage(content=str(inputs["input"])))
            
            # Add AI message  
            if "output" in outputs and outputs["output"]:
                self.chat_memory.messages.append(AIMessage(content=str(outputs["output"])))
            
            # Only trim if we have messages and exceed the window
            if len(self.chat_memory.messages) > self.k * 2:
                try:
                    self.chat_memory.messages = trim_messages(
                        self.chat_memory.messages,
                        token_counter=len,  # Count number of messages
                        max_tokens=self.k * 2,  # k conversations = k*2 messages (user + ai)
                        strategy="last",
                        start_on="human",
                        include_system=True,
                        allow_partial=False,
                    )
                except Exception as trim_error:
                    print(f"⚠️ Trim error, using simple slice: {trim_error}")
                    # Fallback: simple slice to keep last k*2 messages
                    self.chat_memory.messages = self.chat_memory.messages[-(self.k * 2):]
        except Exception as e:
            print(f"⚠️ Error saving context: {e}")
    
    def clear(self):
        """Clear memory contents"""
        try:
            self.chat_memory.messages = []
        except Exception as e:
            print(f"⚠️ Error clearing memory: {e}")
            self.chat_memory = type('ChatMemory', (), {'messages': []})()
    
    def load_memory_variables(self, inputs: dict) -> dict:
        """Return key-value pairs given the text input to the chain"""
        try:
            if self.return_messages:
                return {self.memory_key: self.chat_memory.messages or []}
            else:
                # Convert messages to string format if needed
                buffer = ""
                for message in self.chat_memory.messages:
                    if isinstance(message, HumanMessage):
                        buffer += f"Human: {message.content}\n"
                    elif isinstance(message, AIMessage):
                        buffer += f"AI: {message.content}\n"
                return {self.memory_key: buffer}
        except Exception as e:
            print(f"⚠️ Error loading memory variables: {e}")
            return {self.memory_key: [] if self.return_messages else ""}


class LLMControlledRAG(Runnable):
    """
    LLM-controlled RAG with MODERN conversation memory + max documents control + advanced filtering
    """
    
    def __init__(self, memory_window_size: int = 10):
        self.retriever = RAGRetriever()
        self.personality_manager = PersonalityPromptManager()
        self.doc_matcher = SmartDocumentationMatcher()
        self.controller_llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.2)
        self.generator_llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)
        
        # Initialize MODERN LangChain Memory (replaces deprecated ConversationBufferWindowMemory)
        self.memory = ModernConversationMemory(
            k=memory_window_size,  # Keep last N conversation turns
            return_messages=True,  # Return as message objects
            memory_key="chat_history"
        )
        
        print(f"✅ LLM-Controlled RAG with MODERN Memory + Videos + Max Documents (window size: {memory_window_size})")
        
    def invoke(self, input_dict: Dict[str, Any]) -> str:
        """LLM-controlled RAG process with memory integration and max documents"""
        query = input_dict["question"]
        personality = input_dict.get("personality", "networkchuck")
        gradio_history = input_dict.get("history", [])
        max_documents = input_dict.get("max_documents", 5)
        
        # Step 1: Update memory from Gradio history if provided
        self._sync_memory_with_gradio_history(gradio_history)
        
        # Step 2: LLM Controller decides what to retrieve (with memory context)
        retrieval_strategy = self._get_retrieval_strategy(query, personality)
        
        # Step 3: Retrieve content based on LLM's decision with max documents
        context = self._retrieve_content(query, retrieval_strategy, max_documents)
        
        # Step 4: LLM Generator creates response with personality and memory
        response = self._generate_response(query, context, personality, retrieval_strategy)
        
        # Step 5: Save this interaction to memory
        self.memory.save_context(
            {"input": query},
            {"output": response}
        )
        
        return response
    
    def invoke_with_filters(self, input_dict: Dict[str, Any]) -> str:
        """Enhanced invoke with content filtering and max documents setting"""
        query = input_dict["question"]
        personality = input_dict.get("personality", "networkchuck")
        gradio_history = input_dict.get("history", [])
        content_settings = input_dict.get("content_settings", {})
        similarity_threshold = input_dict.get("similarity_threshold", 0.3)
        llm_temperature = input_dict.get("llm_temperature", 0.7)
        
        print(f"🎯 Processing with filters: {content_settings}")
        print(f"📊 Similarity threshold: {similarity_threshold}, Temperature: {llm_temperature}")
        
        # Extract max_documents from content_settings
        max_documents = content_settings.get('max_documents', 5)
        print(f"📄 Max documents: {max_documents}")
        
        # Update generator LLM temperature
        self.generator_llm.temperature = llm_temperature
        
        # Step 1: Update memory from Gradio history if provided
        self._sync_memory_with_gradio_history(gradio_history)
        
        # Step 2: Check if we should apply tech analogies filter
        enable_analogies = content_settings.get('enable_analogies', True)
        
        # Step 3: LLM Controller decides what to retrieve (with memory context)
        retrieval_strategy = self._get_retrieval_strategy(query, personality, enable_analogies)
        
        # Step 4: Retrieve content based on LLM's decision with similarity filtering and max docs
        context = self._retrieve_content_with_filters(query, retrieval_strategy, similarity_threshold, max_documents)
        
        # Step 5: LLM Generator creates response with personality and memory
        response = self._generate_response_with_filters(query, context, personality, retrieval_strategy, content_settings)
        
        # Step 6: Save this interaction to memory
        self.memory.save_context(
            {"input": query},
            {"output": response}
        )
        
        return response
    
    def _sync_memory_with_gradio_history(self, gradio_history: List):
        """
        Sync Modern LangChain memory with Gradio chat history
        Handles both old tuple format and new messages format
        """
        try:
            if not gradio_history:
                print("🧠 DEBUG: No Gradio history to sync")
                return
            
            print(f"🧠 DEBUG: Syncing memory with {len(gradio_history)} history entries")
            print(f"🧠 DEBUG: Raw Gradio history type: {type(gradio_history)}")
            
            # Clear existing memory to avoid duplication
            self.memory.clear()
            
            # Detect format and convert
            if len(gradio_history) > 0:
                first_item = gradio_history[0]
                print(f"🧠 DEBUG: First item type: {type(first_item)} - {first_item}")
                
                # NEW FORMAT: OpenAI-style messages with type='messages'
                if isinstance(first_item, dict) and 'role' in first_item:
                    print("🧠 DEBUG: Detected NEW Gradio messages format")
                    self._sync_messages_format(gradio_history)
                
                # OLD FORMAT: List/tuple pairs
                elif isinstance(first_item, (list, tuple)):
                    print("🧠 DEBUG: Detected OLD Gradio tuple format")
                    self._sync_tuple_format(gradio_history)
                
                else:
                    print(f"⚠️ DEBUG: Unknown Gradio format: {type(first_item)}")
            
            # Verify memory state after sync
            final_messages = getattr(self.memory.chat_memory, 'messages', [])
            print(f"🧠 DEBUG: Memory synced - {len(final_messages)} messages stored")
            
            # Show what's actually in memory
            for j, msg in enumerate(final_messages[:4]):
                msg_type = type(msg).__name__
                content = getattr(msg, 'content', 'NO_CONTENT')[:50]
                print(f"   Memory[{j}]: {msg_type} - '{content}...'")
            
        except Exception as e:
            print(f"⚠️ Error syncing memory with Gradio history: {type(e).__name__}: {e}")
            print(f"   Gradio history: {gradio_history}")
            # Ensure memory is in a clean state even if sync fails
            try:
                self.memory.clear()
            except:
                self.memory = ModernConversationMemory(
                    k=10, return_messages=True, memory_key="chat_history"
                )
    
    def _sync_messages_format(self, gradio_history: List[Dict]):
        """Handle NEW Gradio messages format: [{'role': 'user', 'content': '...'}, ...]"""
        user_msg = None
        
        for i, message in enumerate(gradio_history):
            try:
                role = message.get('role', '')
                content = message.get('content', '')
                
                if role == 'user':
                    user_msg = content
                    print(f"🧠 DEBUG: Stored user message: '{content[:50]}...'")
                
                elif role == 'assistant' and user_msg:
                    # We have a complete user-assistant pair
                    print(f"🧠 DEBUG: Adding conversation pair:")
                    print(f"   User: '{user_msg[:50]}...'")
                    print(f"   Assistant: '{content[:50]}...'")
                    
                    self.memory.save_context(
                        {"input": str(user_msg)},
                        {"output": str(content)}
                    )
                    user_msg = None  # Reset for next pair
                
            except Exception as msg_error:
                print(f"⚠️ Error processing message {i}: {msg_error}")
                continue
    
    def _sync_tuple_format(self, gradio_history: List[List]):
        """Handle OLD Gradio tuple format: [['user_msg', 'bot_msg'], ...]"""
        for i, turn in enumerate(gradio_history):
            try:
                if isinstance(turn, (list, tuple)) and len(turn) >= 2:
                    user_msg = turn[0]
                    bot_msg = turn[1]
                    
                    # Convert to string and validate
                    if user_msg is not None and bot_msg is not None:
                        user_str = str(user_msg).strip()
                        bot_str = str(bot_msg).strip()
                        
                        if user_str and bot_str and user_str != "None" and bot_str != "None":
                            print(f"🧠 DEBUG: Adding valid turn {i+1}")
                            print(f"   User: '{user_str[:50]}...'")
                            print(f"   Bot: '{bot_str[:50]}...'")
                            
                            self.memory.save_context(
                                {"input": user_str},
                                {"output": bot_str}
                            )
                        else:
                            print(f"⚠️ DEBUG: Skipping turn {i+1} - empty content")
                    else:
                        print(f"⚠️ DEBUG: Skipping turn {i+1} - None values")
                else:
                    print(f"⚠️ DEBUG: Skipping turn {i+1} - invalid format")
                    
            except Exception as turn_error:
                print(f"⚠️ Error processing turn {i+1}: {turn_error}")
                continue
    
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
        """Format memory context for the controller LLM - MODERN VERSION with error handling"""
        try:
            # Get chat history from MODERN memory
            messages = getattr(self.memory.chat_memory, 'messages', [])
            
            if not messages or len(messages) == 0:
                return "No previous conversation."
            
            # Format ALL recent exchanges (not just selective ones)
            context_parts = []
            
            # Process in pairs (human, ai) but include MORE context
            for i in range(0, len(messages), 2):
                try:
                    if i + 1 < len(messages):
                        human_msg = getattr(messages[i], 'content', str(messages[i]))
                        ai_msg = getattr(messages[i + 1], 'content', str(messages[i + 1]))
                        
                        # Don't truncate - include full context for better recall
                        context_parts.append(f"User: {human_msg}")
                        # Safely handle AI message truncation
                        ai_content = str(ai_msg)[:300] + "..." if len(str(ai_msg)) > 300 else str(ai_msg)
                        context_parts.append(f"Assistant: {ai_content}")
                except Exception as msg_error:
                    print(f"⚠️ Error processing message {i}: {msg_error}")
                    continue
            
            # Include MORE conversation history (not just last 3 exchanges)
            # Take last 8 messages (4 full exchanges) instead of 6
            recent_context = "\n".join(context_parts[-8:]) if context_parts else "No valid conversation context."
            
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
            messages = getattr(self.memory.chat_memory, 'messages', [])
            
            if not messages or len(messages) == 0:
                return "No previous conversation to summarize."
            
            # Identify distinct topics discussed
            topics_covered = []
            conversation_flow = []
            
            # Analyze all exchanges for topics
            for i in range(0, len(messages), 2):
                try:
                    if i + 1 < len(messages):
                        user_msg = getattr(messages[i], 'content', str(messages[i])).lower()
                        ai_response = getattr(messages[i + 1], 'content', str(messages[i + 1]))
                        
                        # Extract topic keywords from user questions
                        if "docker" in user_msg:
                            if "docker" not in [t["topic"] for t in topics_covered]:
                                topics_covered.append({
                                    "topic": "docker", 
                                    "details": "Docker containers and containerization",
                                    "response_snippet": str(ai_response)[:150] + "..."
                                })
                        
                        if "compose" in user_msg:
                            if "docker compose" not in [t["topic"] for t in topics_covered]:
                                topics_covered.append({
                                    "topic": "docker compose",
                                    "details": "Docker Compose for multi-container applications", 
                                    "response_snippet": str(ai_response)[:150] + "..."
                                })
                        
                        if "excel" in user_msg or "vlookup" in user_msg:
                            if "excel" not in [t["topic"] for t in topics_covered]:
                                topics_covered.append({
                                    "topic": "excel",
                                    "details": "Excel VLOOKUP functions and data analysis",
                                    "response_snippet": str(ai_response)[:150] + "..."
                                })
                        
                        if "python" in user_msg:
                            if "python" not in [t["topic"] for t in topics_covered]:
                                topics_covered.append({
                                    "topic": "python",
                                    "details": "Python programming and scripting",
                                    "response_snippet": str(ai_response)[:150] + "..."
                                })
                        
                        if "network" in user_msg or "vpn" in user_msg:
                            if "networking" not in [t["topic"] for t in topics_covered]:
                                topics_covered.append({
                                    "topic": "networking",
                                    "details": "Networking, VPNs, and network security",
                                    "response_snippet": str(ai_response)[:150] + "..."
                                })
                        
                        if "linux" in user_msg or "ubuntu" in user_msg:
                            if "linux" not in [t["topic"] for t in topics_covered]:
                                topics_covered.append({
                                    "topic": "linux",
                                    "details": "Linux systems and administration",
                                    "response_snippet": str(ai_response)[:150] + "..."
                                })
                        
                        # Add more topic detection as needed
                except Exception as topic_error:
                    print(f"⚠️ Error processing topic analysis for message {i}: {topic_error}")
                    continue
            
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
    
    def _retrieve_content(self, query: str, strategy: Dict[str, Any], max_documents: int = 5) -> str:
        """Retrieve content based on LLM controller's strategy with max documents limit"""
        
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
        print(f"📄 DEBUG: Max documents limit: {max_documents}")
        
        # Get documents with max_documents limit
        doc_score_pairs = self.retriever.retrieve_context(search_terms, top_k=max_documents)
        
        print(f"🔍 DEBUG: Found {len(doc_score_pairs)} documents")
        
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
            
            doc_score_pairs = filtered_docs[:max_documents]  # Respect max_documents after filtering
            print(f"🔍 DEBUG: {len(doc_score_pairs)} documents after bias filtering")
        
        # For context search, might limit further
        if query_type == "CONTEXT_SEARCH":
            context_limit = min(3, max_documents)  # Context searches use fewer docs, but respect user's max
            doc_score_pairs = doc_score_pairs[:context_limit]
            print(f"🧠 Limited to {context_limit} docs for context-aware query")
        
        # Store docs for video processing
        self._last_doc_score_pairs = doc_score_pairs
        
        # Format context
        context = self.retriever.format_context(doc_score_pairs)
        print(f"🔍 DEBUG: Final context length: {len(context)} chars")
        
        return context
    
    def _retrieve_content_with_filters(self, query: str, strategy: Dict[str, Any], similarity_threshold: float, max_documents: int = 5) -> str:
        """Retrieve content with similarity threshold filtering and max documents limit"""
        
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
        print(f"📄 DEBUG: Max documents limit: {max_documents}")
        
        # Get documents - retrieve more initially to have options for filtering
        initial_retrieve_count = max(10, max_documents * 2)  # Get at least 2x what we need
        doc_score_pairs = self.retriever.retrieve_context(search_terms, top_k=initial_retrieve_count)
        
        # Apply similarity threshold filtering
        filtered_docs = [(doc, score) for doc, score in doc_score_pairs if score >= similarity_threshold]
        
        print(f"🔍 DEBUG: Found {len(doc_score_pairs)} documents, {len(filtered_docs)} above threshold {similarity_threshold}")
        
        # Apply max_documents limit - take the top N after filtering
        final_docs = filtered_docs[:max_documents]
        
        print(f"📄 DEBUG: Using {len(final_docs)} documents (max: {max_documents})")
        
        # Log the selected documents for debugging
        for i, (doc, score) in enumerate(final_docs):
            content_preview = doc.page_content[:100].replace('\n', ' ')
            print(f"   Doc {i+1}: Score {score:.3f} - '{content_preview}...'")
        
        # Store docs for video processing
        self._last_doc_score_pairs = final_docs
        
        # Format context
        context = self.retriever.format_context(final_docs)
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
        """Get summary of current memory state - MODERN VERSION with debugging"""
        try:
            messages = getattr(self.memory.chat_memory, 'messages', [])
            message_count = len(messages) if messages else 0
            
            # Add debugging info
            print(f"🧠 DEBUG: Memory summary - {message_count} messages")
            for i, msg in enumerate(messages[:4]):  # Show first 4 messages for debugging
                msg_type = type(msg).__name__
                content_preview = getattr(msg, 'content', str(msg))[:50]
                print(f"🧠 DEBUG: Message {i}: {msg_type} - '{content_preview}...'")
            
            return {
                "total_messages": message_count,
                "conversation_turns": message_count // 2,
                "memory_window_size": getattr(self.memory, 'k', 10),
                "memory_active": message_count > 0
            }
        except Exception as e:
            print(f"⚠️ Error getting memory summary: {e}")
            return {
                "total_messages": 0,
                "conversation_turns": 0, 
                "memory_window_size": 10,
                "memory_active": False,
                "error": str(e)
            }
    
    def clear_memory(self):
        """Clear conversation memory - MODERN VERSION with safety checks"""
        try:
            print("🧠 DEBUG: Clearing memory...")
            self.memory.clear()
            
            # Verify memory is actually cleared
            messages = getattr(self.memory.chat_memory, 'messages', [])
            if len(messages) == 0:
                print("🧠 Memory cleared successfully")
            else:
                print(f"⚠️ Memory not fully cleared, {len(messages)} messages remain")
                # Force reinitialize if clear didn't work
                self.memory = ModernConversationMemory(
                    k=10, return_messages=True, memory_key="chat_history"
                )
                print("🧠 Memory reinitialized")
                
        except Exception as e:
            print(f"⚠️ Error clearing memory: {e}")
            # Force reinitialize on error
            self.memory = ModernConversationMemory(
                k=10, return_messages=True, memory_key="chat_history"
            )
            print("🧠 Memory reinitialized due to error")


# Test functions for max documents feature
def test_max_documents_retrieval():
    """Test the max documents retrieval functionality"""
    print("🧪 Testing Max Documents Retrieval...")
    
    try:
        # Initialize RAG system
        rag = LLMControlledRAG(memory_window_size=5)
        
        # Test different max_documents values
        test_query = "What is Docker?"
        test_strategy = {
            "query_type": "NORMAL_SEARCH",
            "search_terms": "Docker containers",
            "reasoning": "Test query"
        }
        
        for max_docs in [1, 3, 5, 8, 10]:
            print(f"\n📄 Testing with max_documents = {max_docs}")
            
            context = rag._retrieve_content(test_query, test_strategy, max_docs)
            context_length = len(context)
            
            print(f"   Context length: {context_length} characters")
            
            # Test with filters
            filtered_context = rag._retrieve_content_with_filters(
                test_query, test_strategy, 0.3, max_docs
            )
            filtered_length = len(filtered_context)
            
            print(f"   Filtered context length: {filtered_length} characters")
        
        print("✅ Max Documents retrieval test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Max Documents test failed: {e}")
        return False

if __name__ == "__main__":
    # test_max_documents_retrieval()
    pass  # Run tests if needed