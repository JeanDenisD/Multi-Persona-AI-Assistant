"""
RAG Retriever - Extracted from rag_development_V2.ipynb
Preserves universal content retrieval (no personality filtering)
"""

import os
from typing import List, Tuple, Dict, Any
from collections import defaultdict
import numpy as np

# LangChain imports
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Pinecone as LangchainPinecone


class RAGRetriever:
    """
    RAG Retriever with universal content search (no personality filtering).
    Extracted from notebook and preserved exactly as working implementation.
    """
    
    def __init__(self, index_name: str = "networkchuck-ai-chatbot"):
        self.index_name = index_name
        self.setup_components()
        
    def setup_components(self):
        """Setup embeddings and vectorstore connection"""
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=os.getenv('OPENAI_API_KEY')
        )
        
        # Connect to vectorstore
        self.vectorstore = LangchainPinecone.from_existing_index(
            index_name=self.index_name,
            embedding=self.embeddings
        )
        print("✅ RAG Retriever ready with general search (no personality filtering)!")
    
    def retrieve_context(self, query: str, top_k: int = 5) -> List[Tuple]:
        """Retrieve context WITHOUT personality filtering - general search"""
        # NO metadata filter - search across all personalities
        docs = self.vectorstore.similarity_search_with_score(
            query=query, 
            k=top_k
            # Removed: filter=metadata_filter
        )
        return [(doc, score) for doc, score in docs]
    
    def format_context(self, doc_score_pairs: List[Tuple], max_length: int = 3000) -> str:
        """Format context with source information"""
        if not doc_score_pairs:
            return "No relevant context found."
        
        context_parts = []
        current_length = 0
        
        for doc, score in doc_score_pairs:
            video_title = doc.metadata.get('video_title', 'Unknown Video')
            timestamp = doc.metadata.get('start_time', 0)
            personality = doc.metadata.get('personality', 'Unknown')
            
            # Include personality info in context for transparency
            entry = f"[From: {video_title} at {timestamp}s] ({personality.title()} content, Score: {score:.3f})\n{doc.page_content}\n\n"
            
            if current_length + len(entry) > max_length:
                break
            context_parts.append(entry)
            current_length += len(entry)
        
        return "".join(context_parts).strip()
    
    def get_context_stats(self, doc_score_pairs: List[Tuple]) -> Dict[str, Any]:
        """Get statistics about the retrieved context"""
        if not doc_score_pairs:
            return {'total_sources': 0, 'personalities': {}, 'avg_score': 0}
        
        personalities = defaultdict(int)
        scores = []
        
        for doc, score in doc_score_pairs:
            personality = doc.metadata.get('personality', 'unknown')
            personalities[personality] += 1
            scores.append(score)
        
        return {
            'total_sources': len(doc_score_pairs),
            'personalities': dict(personalities),
            'avg_score': np.mean(scores) if scores else 0,
            'score_range': (min(scores), max(scores)) if scores else (0, 0)
        }


# Test function to verify extraction works
def test_rag_retriever():
    """Test function to verify the RAG retriever works after extraction"""
    print("🧪 Testing RAGRetriever extraction...")
    
    try:
        # Initialize RAG retriever
        retriever = RAGRetriever()
        
        # Test queries
        test_queries = [
            "How to setup Docker containers",
            "Excel VLOOKUP tutorial",
            "VPN configuration guide"
        ]
        
        for query in test_queries:
            print(f"\n🔬 Testing query: {query}")
            
            # Test retrieval
            doc_score_pairs = retriever.retrieve_context(query, top_k=5)
            print(f"📊 Found {len(doc_score_pairs)} context sources")
            
            # Test formatting
            context = retriever.format_context(doc_score_pairs)
            print(f"📝 Context length: {len(context)} characters")
            
            # Test stats
            stats = retriever.get_context_stats(doc_score_pairs)
            print(f"🎭 Personalities found: {stats['personalities']}")
            print(f"📈 Average score: {stats['avg_score']:.3f}")
        
        print(f"\n✅ RAGRetriever extraction SUCCESS!")
        print("🎯 Universal content retrieval preserved from notebook")
        return True
        
    except Exception as e:
        print(f"❌ RAGRetriever extraction FAILED: {e}")
        print("💡 Check Pinecone connection and API keys")
        return False


if __name__ == "__main__":
    # Run test when file is executed directly
    test_rag_retriever()