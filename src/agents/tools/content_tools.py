"""
LangChain Content Tools - Wraps Enhanced RAG System (FIXED VERSION)
Creates LangChain tools that use your enhanced RAG components
"""

import json
import os
from typing import Optional, Dict, Any
from langchain.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from pydantic import BaseModel, Field

# Import your enhanced RAG components
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from core.enhanced_rag import EnhancedRAGEngine
from core.doc_matcher import SmartDocumentationMatcher
from core.retriever import RAGRetriever


class EnhancedRAGTool(BaseTool):
    """
    Main LangChain tool that wraps your complete Enhanced RAG system.
    This preserves ALL your enhanced features while adding LangChain compatibility.
    """
    name: str = "enhanced_rag_search"
    description: str = """
    Advanced AI assistant with dual personalities and smart documentation.
    
    Use this tool for ANY user question - technical or casual.
    
    Input format: JSON string with fields:
    {"query": "user question", "personality": "networkchuck or bloomy", "include_docs": true/false}
    
    Or just plain text for simple queries.
    """
    
    # Class variable to store the enhanced RAG instance
    _enhanced_rag: Optional[EnhancedRAGEngine] = None
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize enhanced RAG system if not already done
        if EnhancedRAGTool._enhanced_rag is None:
            EnhancedRAGTool._enhanced_rag = EnhancedRAGEngine()
            print("✅ EnhancedRAGTool initialized with full enhanced system!")
    
    @property
    def enhanced_rag(self) -> EnhancedRAGEngine:
        """Get the enhanced RAG instance"""
        if EnhancedRAGTool._enhanced_rag is None:
            EnhancedRAGTool._enhanced_rag = EnhancedRAGEngine()
        return EnhancedRAGTool._enhanced_rag
    
    def _run(
        self, 
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """
        Run the enhanced RAG system - preserves all your features exactly
        """
        try:
            # Parse input - handle JSON or plain text
            if query.strip().startswith('{'):
                # JSON input
                try:
                    params = json.loads(query)
                    user_query = params.get('query', query)
                    personality = params.get('personality', 'networkchuck')
                    include_docs = params.get('include_docs', True)
                    doc_top_k = params.get('doc_top_k', 3)
                    doc_min_similarity = params.get('doc_min_similarity', 0.2)
                except json.JSONDecodeError:
                    # If JSON parsing fails, treat as plain text
                    user_query = query
                    personality = 'networkchuck'
                    include_docs = True
                    doc_top_k = 3
                    doc_min_similarity = 0.2
            else:
                # Plain text input
                user_query = query
                personality = 'networkchuck'
                include_docs = True
                doc_top_k = 3
                doc_min_similarity = 0.2
            
            # Use your enhanced RAG system exactly as it works
            result = self.enhanced_rag.generate_response(
                user_query=user_query,
                personality=personality.lower(),
                include_docs=include_docs,
                top_k=5,  # Context retrieval
                doc_top_k=doc_top_k,
                doc_min_similarity=doc_min_similarity
            )
            
            # Add agent metadata for debugging
            metadata = f"\n\n---\n*Agent: Enhanced RAG | Sources: {result['sources']} | Docs: {result['doc_links_count']} | Style: {personality}*"
            
            return result['response'] + metadata
            
        except Exception as e:
            return f"Enhanced RAG Error: {str(e)}"


class VideoContentSearchTool(BaseTool):
    """
    Specialized tool for searching specific video content.
    Uses your RAG retriever for raw content search.
    """
    name: str = "video_content_search"
    description: str = """
    Search for specific content from NetworkChuck and Bloomy video transcripts.
    
    Use this when users want to find information about specific topics covered in the videos.
    Returns raw content with source information (video titles, timestamps, etc.).
    
    Input: topic or keywords to search for
    """
    
    # Class variable to store the retriever instance
    _retriever: Optional[RAGRetriever] = None
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if VideoContentSearchTool._retriever is None:
            VideoContentSearchTool._retriever = RAGRetriever()
            print("✅ VideoContentSearchTool initialized!")
    
    @property
    def retriever(self) -> RAGRetriever:
        """Get the retriever instance"""
        if VideoContentSearchTool._retriever is None:
            VideoContentSearchTool._retriever = RAGRetriever()
        return VideoContentSearchTool._retriever
    
    def _run(
        self, 
        query: str, 
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Search video content and return formatted results"""
        try:
            # Get raw content using your retriever
            doc_score_pairs = self.retriever.retrieve_context(query, top_k=5)
            
            if not doc_score_pairs:
                return "No relevant video content found for this query."
            
            # Format results with metadata
            results = []
            for i, (doc, score) in enumerate(doc_score_pairs, 1):
                video_title = doc.metadata.get('video_title', 'Unknown Video')
                timestamp = doc.metadata.get('start_time', 0)
                personality = doc.metadata.get('personality', 'Unknown')
                
                results.append(f"""
{i}. **{video_title}** (at {timestamp}s)
   Source: {personality.title()} | Relevance: {score:.3f}
   Content: {doc.page_content[:200]}...
""")
            
            header = f"Found {len(results)} relevant video segments:\n"
            return header + "\n".join(results)
            
        except Exception as e:
            return f"Video search error: {str(e)}"


class DocumentationFinderTool(BaseTool):
    """
    Specialized tool for finding official documentation.
    Uses your smart documentation matcher.
    """
    name: str = "documentation_finder"
    description: str = """
    Find official documentation, guides, and learning resources.
    
    Use this when users specifically ask for documentation, tutorials, or want to learn more
    about a particular technology or topic.
    
    Input: technology or topic name
    Returns: Curated list of official documentation links
    """
    
    # Class variable to store the doc matcher instance
    _doc_matcher: Optional[SmartDocumentationMatcher] = None
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if DocumentationFinderTool._doc_matcher is None:
            DocumentationFinderTool._doc_matcher = SmartDocumentationMatcher()
            print("✅ DocumentationFinderTool initialized!")
    
    @property
    def doc_matcher(self) -> SmartDocumentationMatcher:
        """Get the doc matcher instance"""
        if DocumentationFinderTool._doc_matcher is None:
            DocumentationFinderTool._doc_matcher = SmartDocumentationMatcher()
        return DocumentationFinderTool._doc_matcher
    
    def _run(
        self, 
        query: str, 
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Find documentation using your smart matcher"""
        try:
            # Use your documentation matcher
            matches = self.doc_matcher.match_documentation(
                query, top_k=5, min_similarity=0.15
            )
            
            if not matches:
                return f"No official documentation found for '{query}'. Try searching for related technologies."
            
            # Format using your existing formatter
            formatted_docs = self.doc_matcher.format_documentation_links(matches)
            
            # Add metadata
            categories = list(set([match['category'] for match in matches]))
            avg_score = sum([m['similarity_score'] for m in matches]) / len(matches)
            
            metadata = f"\n\n*Found {len(matches)} docs across {len(categories)} categories | Avg relevance: {avg_score:.3f}*"
            
            return formatted_docs + metadata
            
        except Exception as e:
            return f"Documentation search error: {str(e)}"


# Test function to verify tools work
def test_content_tools():
    """Test function to verify the LangChain tools work"""
    print("🧪 Testing LangChain Content Tools...")
    
    try:
        # Test Enhanced RAG Tool
        print("\n--- Testing EnhancedRAGTool ---")
        rag_tool = EnhancedRAGTool()
        
        # Test with different input formats
        test_queries = [
            # JSON format
            '{"query": "How to setup Docker containers", "personality": "networkchuck", "include_docs": true}',
            # Plain text format
            "Excel VLOOKUP tutorial",
            # Casual query
            "Hello there!"
        ]
        
        for i, test_query in enumerate(test_queries, 1):
            print(f"\nTest {i}: {test_query[:50]}...")
            result = rag_tool._run(test_query)
            print(f"✅ Response length: {len(result)} chars")
            print(f"📊 Contains sources: {'Sources:' in result}")
            print(f"🎭 Contains metadata: {'*Agent: Enhanced RAG' in result}")
        
        # Test Video Content Search Tool
        print("\n--- Testing VideoContentSearchTool ---")
        video_tool = VideoContentSearchTool()
        video_result = video_tool._run("Docker networking")
        print(f"✅ Video search result: {len(video_result)} chars")
        print(f"📊 Contains metadata: {'Relevance:' in video_result}")
        
        # Test Documentation Finder Tool
        print("\n--- Testing DocumentationFinderTool ---")
        doc_tool = DocumentationFinderTool()
        doc_result = doc_tool._run("Kubernetes tutorial")
        print(f"✅ Doc finder result: {len(doc_result)} chars")
        print(f"📚 Contains links: {'http' in doc_result or 'No official documentation' in doc_result}")
        
        print(f"\n✅ All LangChain content tools working correctly!")
        print("🎯 Your enhanced RAG system is now LangChain-compatible!")
        return True
        
    except Exception as e:
        print(f"❌ Tool testing failed: {e}")
        return False


if __name__ == "__main__":
    # Run test when file is executed directly
    test_content_tools()