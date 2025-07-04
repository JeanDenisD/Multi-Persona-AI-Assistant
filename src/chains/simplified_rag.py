"""
Simplified LLM-Controlled RAG - Let GPT-4 handle everything naturally
Removed aggressive controller, enhanced memory with summarization
"""

import os
from typing import Dict, Any, List
from langchain.schema.runnable import Runnable
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.messages import trim_messages, HumanMessage, AIMessage, SystemMessage

from ..core.retriever import RAGRetriever
from ..core.doc_matcher import SmartDocumentationMatcher


class EnhancedConversationMemory:
    """Enhanced memory with 20 turns + summarization using standard LangChain"""
    
    def __init__(self, max_turns: int = 20, summary_point: int = 10):
        self.max_turns = max_turns
        self.summary_point = summary_point  # When to summarize (10 oldest turns)
        self.messages = []
        self.conversation_summary = ""
    
    def add_message(self, message):
        """Add message to memory"""
        self.messages.append(message)
        
        # Check if we need to summarize
        if len(self.messages) > self.max_turns * 2:  # 2 messages per turn
            self._summarize_old_messages()
    
    def _summarize_old_messages(self):
        """Summarize oldest messages when memory gets full"""
        try:
            # Take first 20 messages (10 turns) for summarization
            old_messages = self.messages[:self.summary_point * 2]
            recent_messages = self.messages[self.summary_point * 2:]
            
            # Create summarization prompt
            summarizer = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
            
            # Format old messages for summarization
            conversation_text = ""
            for i in range(0, len(old_messages), 2):
                if i + 1 < len(old_messages):
                    user_msg = old_messages[i].content
                    ai_msg = old_messages[i + 1].content
                    conversation_text += f"User: {user_msg}\nAssistant: {ai_msg}\n\n"
            
            summary_prompt = f"""Summarize this conversation concisely, focusing on:
- Key topics discussed
- Important information shared
- User's main interests and questions
- Any ongoing projects or contexts mentioned

Previous summary: {self.conversation_summary}

Recent conversation:
{conversation_text}

Provide a concise summary (max 200 words):"""

            summary_response = summarizer.invoke([HumanMessage(content=summary_prompt)])
            self.conversation_summary = summary_response.content
            
            # Keep only recent messages
            self.messages = recent_messages
            
            print(f"📝 Summarized {len(old_messages)} old messages. Current: {len(self.messages)} messages")
            
        except Exception as e:
            print(f"⚠️ Summarization failed: {e}")
            # Fallback: just trim to max_turns
            self.messages = self.messages[-(self.max_turns * 2):]
    
    def get_context(self) -> str:
        """Get full context including summary + recent messages"""
        context_parts = []
        
        # Add summary if available
        if self.conversation_summary:
            context_parts.append(f"CONVERSATION SUMMARY:\n{self.conversation_summary}\n")
        
        # Add recent messages
        if self.messages:
            context_parts.append("RECENT CONVERSATION:")
            for i in range(0, len(self.messages), 2):
                if i + 1 < len(self.messages):
                    user_msg = self.messages[i].content
                    ai_msg = self.messages[i + 1].content
                    context_parts.append(f"User: {user_msg}")
                    context_parts.append(f"Assistant: {ai_msg[:200]}...")
        
        return "\n".join(context_parts) if context_parts else "No previous conversation."
    
    def clear(self):
        """Clear all memory"""
        self.messages = []
        self.conversation_summary = ""


class SimplifiedRAG(Runnable):
    """
    Simplified RAG - Let GPT-4 handle everything naturally
    No aggressive controllers, just smart prompting
    """
    
    def __init__(self, max_turns: int = 20):
        self.retriever = RAGRetriever()
        self.doc_matcher = SmartDocumentationMatcher()
        
        # Upgrade to GPT-4 for better reasoning
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
        
        # Enhanced memory with summarization
        self.memory = EnhancedConversationMemory(max_turns=max_turns)
        
        print(f"✅ Simplified RAG with GPT-4o-mini + Enhanced Memory ({max_turns} turns)")
    
    def invoke(self, input_dict: Dict[str, Any]) -> str:
        """Simplified invoke - let GPT-4 decide everything"""
        query = input_dict["question"]
        personality = input_dict.get("personality", "networkchuck")
        history = input_dict.get("history", [])
        max_documents = input_dict.get("max_documents", 5)
        
        # Sync memory with Gradio history
        self._sync_memory(history)
        
        # Get relevant documents
        doc_score_pairs = self.retriever.retrieve_context(query, top_k=max_documents)
        
        # Format context
        retrieval_context = self.retriever.format_context(doc_score_pairs)
        
        # Get conversation context
        conversation_context = self.memory.get_context()
        
        # Get documentation matches
        doc_matches = self.doc_matcher.match_documentation(query, top_k=3, min_similarity=0.2)
        doc_links = self.doc_matcher.format_documentation_links(doc_matches)
        
        # Get video information for research capability
        video_info = self._extract_video_info(doc_score_pairs)
        
        # Generate response
        response = self._generate_response(
            query, personality, conversation_context, 
            retrieval_context, doc_links, video_info
        )
        
        # Save to memory
        self.memory.add_message(HumanMessage(content=query))
        self.memory.add_message(AIMessage(content=response))
        
        return response
    
    def invoke_with_filters(self, input_dict: Dict[str, Any]) -> str:
        """Enhanced invoke with content filtering"""
        # Get base response
        response = self.invoke(input_dict)
        
        # Apply content filters
        content_settings = input_dict.get("content_settings", {})
        
        if not content_settings.get('enable_videos', True):
            response = self._remove_video_sections(response)
        
        if not content_settings.get('enable_docs', True):
            response = self._remove_doc_sections(response)
        
        return response
    
    def _sync_memory(self, gradio_history: List):
        """Sync memory with Gradio history"""
        if not gradio_history:
            return
        
        # Clear current memory
        self.memory.clear()
        
        # Add Gradio history to memory
        for entry in gradio_history:
            try:
                if isinstance(entry, dict) and 'role' in entry:
                    # New message format
                    if entry['role'] == 'user':
                        self.memory.add_message(HumanMessage(content=entry['content']))
                    elif entry['role'] == 'assistant':
                        self.memory.add_message(AIMessage(content=entry['content']))
                elif isinstance(entry, (list, tuple)) and len(entry) >= 2:
                    # Old tuple format
                    self.memory.add_message(HumanMessage(content=str(entry[0])))
                    self.memory.add_message(AIMessage(content=str(entry[1])))
            except Exception as e:
                print(f"⚠️ Error syncing message: {e}")
                continue
    
    def _extract_video_info(self, doc_score_pairs):
        """Extract video information for research"""
        videos = {}
        
        for doc, score in doc_score_pairs:
            video_id = doc.metadata.get('video_id', '')
            video_title = doc.metadata.get('video_title', 'Unknown Video')
            video_url = doc.metadata.get('video_url', '')
            
            if video_id and video_id not in videos:
                videos[video_id] = {
                    'title': video_title,
                    'url': video_url,
                    'score': score
                }
        
        return list(videos.values())
    
    def _generate_response(self, query: str, personality: str, conversation_context: str, 
                          retrieval_context: str, doc_links: str, video_info: List) -> str:
        """Generate response with enhanced prompt for natural reasoning"""
        
        # Import personality description
        from ..prompts.personality_prompts import get_personality_description
        personality_description = get_personality_description(personality)
        
        # Create enhanced prompt
        system_prompt = f"""{personality_description}

IMPORTANT RESPONSE GUIDELINES:
- Keep responses between 50-150 words
- Use bullet points for explanations when helpful
- Be concise and scannable
- Only include video/documentation references if truly relevant and not already mentioned recently

CONVERSATION CONTEXT:
{conversation_context}

CURRENT RETRIEVAL CONTEXT:
{retrieval_context}

AVAILABLE VIDEOS FOR RESEARCH:
{self._format_video_list(video_info)}

AVAILABLE DOCUMENTATION:
{doc_links}

USER QUESTION: {query}

Instructions:
1. Use conversation context to avoid repeating information or references already shared
2. If user asks about a specific video by name, search the available videos and provide detailed information
3. Provide helpful, concise responses with bullet points when appropriate
4. Only include video/doc references if they add new value and weren't shared recently
5. Respond naturally as {personality} personality"""

        response = self.llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=query)
        ])
        
        return response.content
    
    def _format_video_list(self, video_info: List) -> str:
        """Format video list for research"""
        if not video_info:
            return "No videos available."
        
        video_list = []
        for video in video_info[:5]:  # Top 5 most relevant
            video_list.append(f"- {video['title']} (Score: {video['score']:.2f})")
        
        return "\n".join(video_list)
    
    def _remove_video_sections(self, response_text: str) -> str:
        """Remove video sections from response"""
        if not response_text:
            return ""
        
        lines = response_text.split('\n')
        filtered_lines = []
        skip_section = False
        
        for line in lines:
            if '🎥' in line or 'Source Videos:' in line:
                skip_section = True
                continue
            elif '📚' in line or 'Documentation:' in line:
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
            if '📚' in line or 'Documentation:' in line:
                skip_section = True
                continue
            
            if not skip_section:
                filtered_lines.append(line)
        
        return '\n'.join(filtered_lines).strip()
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """Get memory status"""
        return {
            "total_messages": len(self.memory.messages),
            "conversation_turns": len(self.memory.messages) // 2,
            "has_summary": bool(self.memory.conversation_summary),
            "memory_active": len(self.memory.messages) > 0
        }
    
    def clear_memory(self):
        """Clear memory"""
        self.memory.clear()
        print("🧠 Enhanced memory cleared")