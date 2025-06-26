#!/usr/bin/env python3
"""
Quick test script for the embedding system using LangChain
"""

import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from pinecone import Pinecone

load_dotenv()

def test_openai_connection():
    """Test OpenAI API connection using working approach"""
    try:
        # Use the working approach from your other project
        import openai
        openai.api_key = os.getenv('OPENAI_API_KEY')
        
        # Test embeddings using the older working syntax
        response = openai.Embedding.create(
            model="text-embedding-3-small",
            input=["Hello, this is a test"]
        )
        
        embedding_vector = response['data'][0]['embedding']
        
        print("✅ OpenAI connection successful!")
        print(f"   Model: text-embedding-3-small")
        print(f"   Embedding dimension: {len(embedding_vector)}")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI connection failed: {e}")
        
        # Try the new client approach as fallback
        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=["test"]
            )
            
            print("✅ OpenAI (new client) connection successful!")
            print(f"   Embedding dimension: {len(response.data[0].embedding)}")
            return True
            
        except Exception as e2:
            print(f"❌ All OpenAI methods failed: {e2}")
            return False

def test_pinecone_connection():
    """Test Pinecone connection"""
    try:
        pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
        
        # List existing indexes
        indexes = [index.name for index in pc.list_indexes()]
        print("✅ Pinecone connection successful!")
        print(f"   Existing indexes: {indexes}")
        return True
        
    except Exception as e:
        print(f"❌ Pinecone connection failed: {e}")
        return False

def test_data_files():
    """Test if data files exist"""
    files_to_check = [
        "data/processed/all_networkchuck_transcripts.csv",
        "data/processed/all_bloomy_transcripts.csv"
    ]
    
    all_exist = True
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"✅ Found: {file_path}")
        else:
            print(f"❌ Missing: {file_path}")
            all_exist = False
    
    return all_exist

def main():
    print("🧪 Testing Embedding Pipeline Setup (LangChain)")
    print("=" * 50)
    
    # Test environment variables
    print("\n🔑 Checking Environment Variables:")
    if os.getenv('OPENAI_API_KEY'):
        print("✅ OPENAI_API_KEY found")
    else:
        print("❌ OPENAI_API_KEY missing")
    
    if os.getenv('PINECONE_API_KEY'):
        print("✅ PINECONE_API_KEY found")
    else:
        print("❌ PINECONE_API_KEY missing")
    
    # Test connections
    print("\n🌐 Testing API Connections:")
    openai_ok = test_openai_connection()
    pinecone_ok = test_pinecone_connection()
    
    # Test data files
    print("\n📁 Checking Data Files:")
    files_ok = test_data_files()
    
    # Summary
    print("\n" + "=" * 50)
    if openai_ok and pinecone_ok and files_ok:
        print("🎉 ALL TESTS PASSED!")
        print("🚀 Ready to run the embedding pipeline!")
    else:
        print("⚠️ Some tests failed. Please fix issues before running pipeline.")

if __name__ == "__main__":
    main()