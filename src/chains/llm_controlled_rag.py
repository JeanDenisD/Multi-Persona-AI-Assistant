"""
LLM-Controlled RAG - LLM decides what to retrieve
"""

import os
from typing import Dict, Any, List
from urllib import response
from langchain.schema.runnable import Runnable, RunnableLambda
# from langchain.schema.output_parser import StrOutputParser
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from ..core.retriever import RAGRetriever
from ..core.personality import PersonalityPromptManager
from ..core.doc_matcher import SmartDocumentationMatcher
from ..prompts.llm_controller_prompts import get_controller_prompt_template


class LLMControlledRAG(Runnable):
    """
    LLM-controlled RAG where LLM decides what to retrieve
    """
    
    def __init__(self):
        self.retriever = RAGRetriever()
        self.personality_manager = PersonalityPromptManager()
        self.doc_matcher = SmartDocumentationMatcher()
        self.controller_llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.2)
        self.generator_llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)
        
    def invoke(self, input_dict: Dict[str, Any]) -> str:
        """LLM-controlled RAG process"""
        query = input_dict["question"]
        personality = input_dict.get("personality", "networkchuck")
        
        # Step 1: LLM Controller decides what to retrieve
        retrieval_strategy = self._get_retrieval_strategy(query, personality)
        
        # Step 2: Retrieve content based on LLM's decision
        context = self._retrieve_content(query, retrieval_strategy)
        
        # Step 3: LLM Generator creates response with personality
        response = self._generate_response(query, context, personality)
        
        return response
    
    def _get_retrieval_strategy(self, query: str, personality: str) -> Dict[str, Any]:
        """LLM decides what type of content to retrieve"""
        controller_prompt = ChatPromptTemplate.from_template(get_controller_prompt_template())
        
        result = self.controller_llm.invoke(
            controller_prompt.format(query=query, personality=personality)
        )
        
        # Parse the controller's decision
        content = result.content
        strategy = {
            "search_terms": self._extract_field(content, "SEARCH_TERMS"),
            "content_type": self._extract_field(content, "CONTENT_TYPE"),
            "avoid_bias": self._extract_field(content, "AVOID_PERSONALITY_BIAS"),
            "focus_area": self._extract_field(content, "FOCUS_AREA")
        }
        
        return strategy
    
    def _extract_field(self, content: str, field: str) -> str:
        """Extract field from controller response"""
        for line in content.split('\n'):
            if field in line:
                return line.split(':', 1)[1].strip() if ':' in line else ""
        return ""
    
    def _retrieve_content(self, query: str, strategy: Dict[str, Any]) -> str:
        """Retrieve content based on LLM controller's strategy"""
        
        # Use search terms if provided, otherwise use original query
        search_query = strategy.get("search_terms", query)
        if not search_query or search_query == "":
            search_query = query
        
        print(f"🔍 DEBUG: Search query: {search_query}")
        print(f"🔍 DEBUG: Strategy: {strategy}")
        
        # Get documents
        doc_score_pairs = self.retriever.retrieve_context(search_query, top_k=5)
        
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
        
        # Format context
        context = self.retriever.format_context(doc_score_pairs)
        print(f"🔍 DEBUG: Final context length: {len(context)} chars")
        
        return context
    
    def _generate_response(self, query: str, context: str, personality: str) -> str:
        """Generate response with extracted personality descriptions""" 
        # Import the personality descriptions
        from ..prompts.personality_prompts import get_personality_description
        
        # Get the personality description from external file
        personality_description = get_personality_description(personality)
        
        # Keep the LLM prompt structure hardcoded here
        system_prompt = """{personality_description}
        
        Context: {context}
        
        User Question: {query}
        
        Respond as {personality_name} with your authentic style:"""
        
        # Generate with strong personality enforcement
        response = self.generator_llm.invoke([{
            "role": "system", 
            "content": system_prompt.format(
            personality_description=personality_description,
            context=context,
            query=query,
            personality_name=personality.title()
        )
        }])

        # Add documentation if needed (restore this functionality)
        if self._should_add_docs(query):
            doc_matches = self.doc_matcher.match_documentation(query, top_k=3, min_similarity=0.2)
            doc_links = self.doc_matcher.format_documentation_links(doc_matches)
            if doc_links:
                return response.content + "\n\n" + doc_links
        
        return response.content
    
    def _should_add_docs(self, query: str) -> bool:
        """Check if documentation should be added"""
        casual_patterns = ['hello', 'hi', 'how are you', 'thanks', 'bye']
        return not any(pattern in query.lower() for pattern in casual_patterns)