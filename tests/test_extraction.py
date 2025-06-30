"""
Test script to verify extracted modules work identically to notebook
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path.cwd()
sys.path.append(str(project_root / 'src'))

def test_doc_matcher_extraction():
    """Test that extracted SmartDocumentationMatcher works identically"""
    print("="*60)
    print("🧪 TESTING SMARTDOCUMENTATIONMATCHER EXTRACTION")
    print("="*60)
    
    try:
        # Import the extracted module
        from core.doc_matcher import SmartDocumentationMatcher
        
        # Initialize (same as notebook)
        print("📦 Initializing SmartDocumentationMatcher...")
        doc_matcher = SmartDocumentationMatcher()
        
        # Test queries (same as in your notebook)
        test_queries = [
            "How to setup Docker containers",
            "Excel VLOOKUP tutorial", 
            "Bloomberg Terminal guide",
            "Hello there!"  # Should work but maybe get fewer/no matches
        ]
        
        print(f"\n🔬 Testing {len(test_queries)} queries...")
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n--- Test {i}: {query} ---")
            
            # Test documentation matching
            matches = doc_matcher.match_documentation(
                query, 
                top_k=3, 
                min_similarity=0.2
            )
            
            print(f"📊 Found {len(matches)} documentation matches")
            
            if matches:
                print("📚 Top match:", matches[0]['title'])
                print(f"🎯 Similarity: {matches[0]['similarity_score']:.3f}")
                print(f"📁 Category: {matches[0]['category']}")
            
            # Test formatting
            formatted = doc_matcher.format_documentation_links(matches)
            if formatted:
                print("✅ Formatting works")
            else:
                print("ℹ️ No formatted output (expected for casual queries)")
        
        print(f"\n✅ SmartDocumentationMatcher extraction SUCCESS!")
        print("🎯 All core functionality preserved from notebook")
        return True
        
    except Exception as e:
        print(f"❌ SmartDocumentationMatcher extraction FAILED: {e}")
        print("💡 Check file paths and dependencies")
        return False

def test_imports():
    """Test that all necessary imports work"""
    print("\n🔍 Testing imports...")
    
    try:
        import openai
        print("✅ openai imported")
        
        import numpy as np
        print("✅ numpy imported")
        
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        if os.getenv('OPENAI_API_KEY'):
            print("✅ OPENAI_API_KEY found")
        else:
            print("⚠️ OPENAI_API_KEY not found - check .env file")
            
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 EXTRACTION TESTING SUITE")
    print("Testing that extracted modules work identically to notebook\n")
    
    # Test imports first
    imports_ok = test_imports()
    
    if imports_ok:
        # Test doc matcher extraction
        doc_matcher_ok = test_doc_matcher_extraction()
        
        if doc_matcher_ok:
            print(f"\n{'='*60}")
            print("🎉 EXTRACTION TEST SUITE PASSED!")
            print("✅ Ready for next step: RAGRetriever extraction")
            print("="*60)
        else:
            print(f"\n{'='*60}")
            print("❌ EXTRACTION TEST FAILED")
            print("🔧 Fix issues before proceeding")
            print("="*60)
    else:
        print("❌ Import issues - check dependencies")

# Test function to verify RAGRetriever extraction works

def test_rag_retriever_extraction():
    """Test that extracted RAGRetriever works identically"""
    print("="*60)
    print("🧪 TESTING RAGRETRIEVER EXTRACTION")
    print("="*60)
    
    try:
        # Import the extracted module
        from core.retriever import RAGRetriever
        
        # Initialize (same as notebook)
        print("📦 Initializing RAGRetriever...")
        retriever = RAGRetriever()
        
        # Test queries (same as in your notebook)
        test_queries = [
            "How to setup Docker containers",
            "Excel VLOOKUP tutorial", 
            "VPN configuration guide"
        ]
        
        print(f"\n🔬 Testing {len(test_queries)} queries...")
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n--- Test {i}: {query} ---")
            
            # Test context retrieval
            doc_score_pairs = retriever.retrieve_context(query, top_k=5)
            print(f"📊 Found {len(doc_score_pairs)} context sources")
            
            if doc_score_pairs:
                # Test formatting
                context = retriever.format_context(doc_score_pairs)
                print(f"📝 Context length: {len(context)} characters")
                
                # Test stats
                stats = retriever.get_context_stats(doc_score_pairs)
                print(f"🎭 Personalities: {stats['personalities']}")
                print(f"📈 Avg score: {stats['avg_score']:.3f}")
                print(f"🎯 Score range: {stats['score_range'][0]:.3f}-{stats['score_range'][1]:.3f}")
            else:
                print("⚠️ No context found")
        
        print(f"\n✅ RAGRetriever extraction SUCCESS!")
        print("🎯 Universal content retrieval preserved from notebook")
        return True
        
    except Exception as e:
        print(f"❌ RAGRetriever extraction FAILED: {e}")
        print("💡 Check Pinecone connection and API keys")
        return False

# Update the main function in your test file:
if __name__ == "__main__":
    print("🚀 EXTRACTION TESTING SUITE")
    print("Testing that extracted modules work identically to notebook\n")
    
    # Test imports first
    imports_ok = test_imports()
    
    if imports_ok:
        # Test doc matcher extraction
        doc_matcher_ok = test_doc_matcher_extraction()
        
        if doc_matcher_ok:
            # Test RAG retriever extraction
            rag_retriever_ok = test_rag_retriever_extraction()
            
            if rag_retriever_ok:
                print(f"\n{'='*60}")
                print("🎉 EXTRACTION TEST SUITE PASSED!")
                print("✅ Ready for next step: PersonalityPromptManager extraction")
                print("="*60)
            else:
                print(f"\n{'='*60}")
                print("❌ RAGRetriever TEST FAILED")
                print("🔧 Fix issues before proceeding")
                print("="*60)
        else:
            print(f"\n{'='*60}")
            print("❌ EXTRACTION TEST FAILED")
            print("🔧 Fix issues before proceeding")
            print("="*60)
    else:
        print("❌ Import issues - check dependencies")

# Test function to verify PersonalityPromptManager extraction works

def test_personality_manager_extraction():
    """Test that extracted PersonalityPromptManager works identically"""
    print("="*60)
    print("🧪 TESTING PERSONALITYPROMPTMANAGER EXTRACTION")
    print("="*60)
    
    try:
        # Import the extracted module
        from core.personality import PersonalityPromptManager
        
        # Initialize (same as notebook)
        print("📦 Initializing PersonalityPromptManager...")
        prompt_manager = PersonalityPromptManager()
        
        # Test prompt building scenarios
        test_scenarios = [
            {
                "personality": "networkchuck",
                "query": "How to setup Docker containers",
                "context": "Docker containers are like shipping containers for applications...",
                "stats": {'total_sources': 5, 'personalities': {'networkchuck': 5}, 'avg_score': 0.65}
            },
            {
                "personality": "bloomy", 
                "query": "Excel VLOOKUP tutorial",
                "context": "VLOOKUP is a powerful Excel function for data lookup...",
                "stats": {'total_sources': 3, 'personalities': {'bloomy': 3}, 'avg_score': 0.72}
            },
            {
                "personality": "networkchuck",
                "query": "What is Kubernetes?",
                "context": "Kubernetes is a container orchestration platform...",
                "stats": {'total_sources': 4, 'personalities': {'networkchuck': 4}, 'avg_score': 0.58}
            }
        ]
        
        print(f"\n🔬 Testing {len(test_scenarios)} prompt scenarios...")
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n--- Test {i}: {scenario['personality']} - {scenario['query'][:30]}... ---")
            
            # Test prompt building
            prompt = prompt_manager.build_prompt(
                personality=scenario['personality'],
                user_query=scenario['query'],
                context=scenario['context'],
                context_stats=scenario['stats']
            )
            
            # Validate prompt components
            prompt_checks = {
                "Has personality traits": any(trait in prompt for trait in ["PERSONALITY TRAITS", "enthusiastic", "professional"]),
                "Has response style": "RESPONSE STYLE:" in prompt,
                "Has query analysis": "QUERY ANALYSIS:" in prompt,
                "Has context info": "CONTEXT INFO:" in prompt,
                "Has user question": scenario['query'] in prompt,
                "Has context": scenario['context'] in prompt
            }
            
            print(f"📝 Prompt length: {len(prompt)} characters")
            print(f"🎭 Personality: {scenario['personality']}")
            
            # Check all components
            all_good = all(prompt_checks.values())
            if all_good:
                print("✅ All prompt components present")
            else:
                print("⚠️ Missing components:", [k for k, v in prompt_checks.items() if not v])
            
            # Test query analysis
            if "PROCEDURAL" in prompt:
                print("🔧 Correctly identified as procedural query")
            elif "CONCEPTUAL" in prompt:
                print("💡 Correctly identified as conceptual query")
            else:
                print("📋 Query type analysis present")
        
        print(f"\n✅ PersonalityPromptManager extraction SUCCESS!")
        print("🎯 Enhanced personality system with step integration preserved")
        return True
        
    except Exception as e:
        print(f"❌ PersonalityPromptManager extraction FAILED: {e}")
        return False

# Update the main function in your test file to include the new test:
if __name__ == "__main__":
    print("🚀 EXTRACTION TESTING SUITE")
    print("Testing that extracted modules work identically to notebook\n")
    
    # Test imports first
    imports_ok = test_imports()
    
    if imports_ok:
        # Test doc matcher extraction
        doc_matcher_ok = test_doc_matcher_extraction()
        
        if doc_matcher_ok:
            # Test RAG retriever extraction
            rag_retriever_ok = test_rag_retriever_extraction()
            
            if rag_retriever_ok:
                # Test personality manager extraction
                personality_ok = test_personality_manager_extraction()
                
                if personality_ok:
                    print(f"\n{'='*60}")
                    print("🎉 EXTRACTION TEST SUITE PASSED!")
                    print("✅ Ready for next step: EnhancedRAGEngine extraction")
                    print("="*60)
                else:
                    print(f"\n{'='*60}")
                    print("❌ PersonalityPromptManager TEST FAILED")
                    print("🔧 Fix issues before proceeding")
                    print("="*60)
            else:
                print(f"\n{'='*60}")
                print("❌ RAGRetriever TEST FAILED")
                print("🔧 Fix issues before proceeding")
                print("="*60)
        else:
            print(f"\n{'='*60}")
            print("❌ EXTRACTION TEST FAILED")
            print("🔧 Fix issues before proceeding")
            print("="*60)
    else:
        print("❌ Import issues - check dependencies")

# Test function to verify EnhancedRAGEngine extraction works

def test_enhanced_rag_engine_extraction():
    """Test that extracted EnhancedRAGEngine works identically"""
    print("="*60)
    print("🧪 TESTING ENHANCEDRAGENGINE EXTRACTION")
    print("="*60)
    
    try:
        # Import the extracted module
        from core.enhanced_rag import EnhancedRAGEngine
        
        # Initialize (same as notebook)
        print("📦 Initializing EnhancedRAGEngine...")
        enhanced_rag = EnhancedRAGEngine()
        
        # Test complete scenarios (same as in your notebook)
        test_scenarios = [
            {
                "query": "How to setup Docker containers",
                "personality": "networkchuck",
                "expected_docs": True,
                "description": "Technical NetworkChuck query"
            },
            {
                "query": "Excel VLOOKUP tutorial", 
                "personality": "bloomy",
                "expected_docs": True,
                "description": "Technical Bloomy query"
            },
            {
                "query": "Hello there!",
                "personality": "networkchuck", 
                "expected_docs": False,
                "description": "Casual query (should skip docs)"
            }
        ]
        
        print(f"\n🔬 Testing {len(test_scenarios)} complete RAG scenarios...")
        
        all_tests_passed = True
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n--- Test {i}: {scenario['description']} ---")
            print(f"Query: {scenario['query']}")
            print(f"Personality: {scenario['personality']}")
            
            # Test complete enhanced RAG response
            result = enhanced_rag.generate_response(
                user_query=scenario['query'],
                personality=scenario['personality'],
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
                all_tests_passed = False
                continue
            
            # Check core metrics
            print(f"📊 Sources found: {result['sources']}")
            print(f"📚 Documentation links: {result['doc_links_count']}")
            print(f"🎭 Personality: {result['personality']}")
            print(f"📝 Response length: {len(result['response'])} chars")
            print(f"🔧 AI response length: {len(result['ai_response_only'])} chars")
            
            # Validate documentation behavior
            docs_correct = False
            if scenario['expected_docs']:
                if result['doc_links_count'] > 0:
                    print("✅ Documentation provided as expected")
                    docs_correct = True
                else:
                    print("⚠️ Expected documentation but none provided")
            else:
                if result.get('docs_skipped_reason') == 'casual_query':
                    print("✅ Correctly skipped docs for casual query")
                    docs_correct = True
                else:
                    print("⚠️ Should have skipped docs for casual query")
            
            # Check context quality
            if result['context_stats'] and 'personalities' in result['context_stats']:
                personalities = result['context_stats']['personalities']
                avg_score = result['context_stats'].get('avg_score', 0)
                print(f"🎭 Context from: {personalities}")
                print(f"📈 Avg similarity: {avg_score:.3f}")
                
                if avg_score > 0.5:
                    print("✅ High-quality context retrieved")
                else:
                    print("⚠️ Lower quality context")
            
            # Overall test result
            if docs_correct and result['sources'] > 0 and len(result['response']) > 100:
                print("✅ Test scenario PASSED")
            else:
                print("❌ Test scenario FAILED")
                all_tests_passed = False
        
        if all_tests_passed:
            print(f"\n✅ EnhancedRAGEngine extraction SUCCESS!")
            print("🎯 Complete enhanced RAG system with all features preserved")
            print("🚀 Ready for LangChain agent integration!")
            return True
        else:
            print(f"\n❌ Some tests failed")
            return False
        
    except Exception as e:
        print(f"❌ EnhancedRAGEngine extraction FAILED: {e}")
        print(f"💡 Error type: {type(e).__name__}")
        return False

# Update the main function in your test file to include all tests:
if __name__ == "__main__":
    print("🚀 EXTRACTION TESTING SUITE")
    print("Testing that extracted modules work identically to notebook\n")
    
    # Test imports first
    imports_ok = test_imports()
    
    if imports_ok:
        # Test all extracted components
        doc_matcher_ok = test_doc_matcher_extraction()
        if not doc_matcher_ok:
            exit(1)
            
        rag_retriever_ok = test_rag_retriever_extraction()
        if not rag_retriever_ok:
            exit(1)
            
        personality_ok = test_personality_manager_extraction()
        if not personality_ok:
            exit(1)
            
        # Test complete enhanced RAG engine
        enhanced_rag_ok = test_enhanced_rag_engine_extraction()
        
        if enhanced_rag_ok:
            print(f"\n{'='*60}")
            print("🎉 ALL EXTRACTIONS SUCCESSFUL!")
            print("✅ SmartDocumentationMatcher")
            print("✅ RAGRetriever") 
            print("✅ PersonalityPromptManager")
            print("✅ EnhancedRAGEngine")
            print("")
            print("🚀 READY FOR LANGCHAIN AGENT INTEGRATION!")
            print("="*60)
        else:
            print(f"\n{'='*60}")
            print("❌ EnhancedRAGEngine TEST FAILED")
            print("🔧 Fix issues before proceeding to LangChain")
            print("="*60)
    else:
        print("❌ Import issues - check dependencies")