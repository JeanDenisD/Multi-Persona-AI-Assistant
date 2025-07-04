"""
Test personality isolation
"""

from src.chains.llm_controlled_rag_old import LLMControlledRAG

def test_personalities():
    rag = LLMControlledRAG()
    
    # Test with same query, different personalities
    query = "Hello, how are you?"
    
    print("=" * 50)
    print("TESTING NETWORKCHUCK:")
    nc_response = rag.invoke({"question": query, "personality": "networkchuck"})
    print(nc_response)
    
    print("\n" + "=" * 50)
    print("TESTING BLOOMY:")
    bloomy_response = rag.invoke({"question": query, "personality": "bloomy"})
    print(bloomy_response)
    
    print("\n" + "=" * 50)
    print("RESPONSES ARE DIFFERENT:", nc_response != bloomy_response)

if __name__ == "__main__":
    test_personalities()