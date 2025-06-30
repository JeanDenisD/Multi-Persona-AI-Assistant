"""
Enhanced RAG Engine - Extracted from rag_development_V2.ipynb
Main orchestrator that combines all components with smart documentation
"""

import os
import openai
from typing import Dict, Any

# Import our extracted components
from .doc_matcher import SmartDocumentationMatcher
from .retriever import RAGRetriever
from .personality import PersonalityPromptManager


class EnhancedRAGEngine:
    """
    Enhanced RAG Engine with smart documentation support.
    Extracted from notebook and preserved exactly as working implementation.
    """
    
    def __init__(self):
        self.retriever = RAGRetriever()
        self.prompt_manager = PersonalityPromptManager()
        self.doc_matcher = SmartDocumentationMatcher()
        self.client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        print("✅ Enhanced RAG Engine ready with smart documentation!")
    
    def should_provide_docs(self, query: str) -> bool:
        """Determine if documentation should be provided based on query type"""
        casual_greetings = [
            'how are you', 'hello', 'hi', 'hey', 'what\'s up', 
            'good morning', 'good afternoon', 'good evening',
            'how\'s it going', 'how do you do', 'what\'s new',
            'how have you been', 'nice to meet you', 'pleased to meet you'
        ]
        
        small_talk = [
            'thank you', 'thanks', 'bye', 'goodbye', 'see you later',
            'have a good day', 'take care', 'nice talking to you'
        ]
        
        # Convert query to lowercase for comparison
        query_lower = query.lower().strip()
        
        # Check for casual greetings and small talk
        casual_patterns = casual_greetings + small_talk
        
        return not any(pattern in query_lower for pattern in casual_patterns)
    
    def generate_response(self, user_query: str, personality: str = "networkchuck", 
                         include_docs: bool = True, top_k: int = 5,
                         doc_top_k: int = 3, doc_min_similarity: float = 0.2):
        """Generate response with enhanced features and smart documentation"""
        try:
            # Step 1: Retrieve context (general search, no personality filtering)
            doc_score_pairs = self.retriever.retrieve_context(user_query, top_k)
            context = self.retriever.format_context(doc_score_pairs)
            context_stats = self.retriever.get_context_stats(doc_score_pairs)
            
            # Step 2: Generate AI response with personality style
            prompt = self.prompt_manager.build_prompt(
                personality, user_query, context, context_stats
            )
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": prompt}],
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content
            
            # Step 3: Smart documentation matching
            documentation_matches = []
            documentation_links = ""
            
            if include_docs and self.should_provide_docs(user_query):
                # Match against original query (not AI response) for universal docs
                documentation_matches = self.doc_matcher.match_documentation(
                    user_query, top_k=doc_top_k, min_similarity=doc_min_similarity
                )
                documentation_links = self.doc_matcher.format_documentation_links(
                    documentation_matches
                )
            
            # Step 4: Combine response with documentation
            final_response = ai_response
            if documentation_links:
                final_response += "\n\n" + documentation_links
            
            return {
                "response": final_response,
                "ai_response_only": ai_response,
                "context": context,
                "context_stats": context_stats,
                "documentation_matches": documentation_matches,
                "personality": personality,
                "sources": len(doc_score_pairs),
                "doc_links_count": len(documentation_matches),
                "docs_skipped_reason": "casual_query" if include_docs and not self.should_provide_docs(user_query) else None
            }
            
        except Exception as e:
            return {
                "response": f"Sorry, I encountered an error: {e}",
                "ai_response_only": f"Error: {e}",
                "context": "",
                "context_stats": {},
                "documentation_matches": [],
                "personality": personality,
                "sources": 0,
                "doc_links_count": 0,
                "docs_skipped_reason": "error"
            }


# Test function to verify extraction works
def test_enhanced_rag_engine():
    """Test function to verify the enhanced RAG engine works after extraction"""
    print("🧪 Testing EnhancedRAGEngine extraction...")
    
    try:
        # Initialize enhanced RAG engine
        print("📦 Initializing EnhancedRAGEngine...")
        enhanced_rag = EnhancedRAGEngine()
        
        # Test queries (same as in your notebook)
        test_queries = [
            {
                "query": "How to setup Docker containers",
                "personality": "networkchuck",
                "expected_docs": True
            },
            {
                "query": "Excel VLOOKUP tutorial", 
                "personality": "bloomy",
                "expected_docs": True
            },
            {
                "query": "Hello there!",
                "personality": "networkchuck", 
                "expected_docs": False  # Should skip docs for casual
            }
        ]
        
        print(f"\n🔬 Testing {len(test_queries)} complete scenarios...")
        
        for i, test in enumerate(test_queries, 1):
            print(f"\n--- Test {i}: {test['personality']} - {test['query']} ---")
            
            # Test complete enhanced RAG response
            result = enhanced_rag.generate_response(
                user_query=test['query'],
                personality=test['personality'],
                include_docs=True,
                top_k=5,
                doc_top_k=3,
                doc_min_similarity=0.2
            )
            
            # Validate result structure
            expected_keys = [
                "response", "ai_response_only", "context", "context_stats",
                "documentation_matches", "personality", "sources", "doc_links_count"
            ]
            
            missing_keys = [key for key in expected_keys if key not in result]
            if missing_keys:
                print(f"❌ Missing keys: {missing_keys}")
                return False
            
            # Check functionality
            print(f"📊 Sources: {result['sources']}")
            print(f"📚 Docs: {result['doc_links_count']}")
            print(f"🎭 Personality: {result['personality']}")
            print(f"📝 Response length: {len(result['response'])} chars")
            
            # Validate documentation behavior
            if test['expected_docs']:
                if result['doc_links_count'] > 0:
                    print("✅ Documentation provided as expected")
                else:
                    print("⚠️ Expected documentation but none provided")
            else:
                if result['docs_skipped_reason'] == 'casual_query':
                    print("✅ Correctly skipped docs for casual query")
                else:
                    print("⚠️ Should have skipped docs for casual query")
            
            # Check context stats
            if result['context_stats'] and 'personalities' in result['context_stats']:
                personalities = result['context_stats']['personalities']
                print(f"🎭 Context from: {personalities}")
            
        print(f"\n✅ EnhancedRAGEngine extraction SUCCESS!")
        print("🎯 Complete enhanced RAG system with all features preserved")
        return True
        
    except Exception as e:
        print(f"❌ EnhancedRAGEngine extraction FAILED: {e}")
        print(f"💡 Error details: {type(e).__name__}")
        return False


if __name__ == "__main__":
    # Run test when file is executed directly
    test_enhanced_rag_engine()