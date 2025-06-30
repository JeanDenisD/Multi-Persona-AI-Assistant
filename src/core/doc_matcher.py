"""
Smart Documentation Matcher - Extracted from rag_development_V2.ipynb
Preserves all enhanced features: OpenAI embeddings, semantic matching, query detection
"""

import os
import json
import re
from typing import List, Dict, Any
import openai
import numpy as np


class SmartDocumentationMatcher:
    """
    Smart documentation matcher using OpenAI embeddings for semantic matching.
    Extracted from notebook and preserved exactly as working implementation.
    """
    
    def __init__(self, documentation_path: str = "data/official_docs/documentation_links.json"):
        self.documentation_path = documentation_path
        self.docs = self.load_documentation()
        self.client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        if self.docs:
            self.setup_embeddings()
            print("✅ Smart Documentation Matcher ready!")
        else:
            print("⚠️ Documentation matcher initialized without data")
    
    def load_documentation(self) -> List[Dict]:
        """Load and flatten the documentation database"""
        try:
            with open(self.documentation_path, 'r') as f:
                doc_data = json.load(f)
            
            # Flatten the nested structure
            flattened_docs = []
            for category, docs in doc_data.items():
                for doc in docs:
                    doc['category'] = category
                    flattened_docs.append(doc)
            
            print(f"✅ Loaded {len(flattened_docs)} documentation links across {len(doc_data)} categories")
            return flattened_docs
            
        except FileNotFoundError:
            print(f"⚠️ Documentation file not found: {self.documentation_path}")
            return []
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing documentation JSON: {e}")
            return []
    
    def setup_embeddings(self):
        """Setup OpenAI embeddings for semantic matching"""
        # Create searchable text for each document
        self.doc_texts = []
        for doc in self.docs:
            # Combine title, description, keywords, and topics for matching
            text_parts = [
                doc.get('title', ''),
                doc.get('description', ''),
                ' '.join(doc.get('keywords', [])),
                ' '.join(doc.get('topics', [])),
                doc.get('category', '')
            ]
            self.doc_texts.append(' '.join(text_parts).lower())
        
        # Generate embeddings for all documentation
        print(f"🔄 Generating OpenAI embeddings for {len(self.doc_texts)} documentation entries...")
        
        try:
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=self.doc_texts
            )
            
            # Store embeddings as numpy array for easier similarity calculation
            self.doc_embeddings = np.array([item.embedding for item in response.data])
            print(f"✅ Documentation embeddings generated: {self.doc_embeddings.shape}")
            
        except Exception as e:
            print(f"❌ Error generating embeddings: {e}")
            self.doc_embeddings = None
    
    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        dot_product = np.dot(vec1, vec2)
        norm_a = np.linalg.norm(vec1)
        norm_b = np.linalg.norm(vec2)
        return dot_product / (norm_a * norm_b)
    
    def extract_keywords_from_response(self, response_text: str) -> List[str]:
        """Extract relevant keywords from the AI response"""
        # Clean and normalize the response
        cleaned_text = re.sub(r'[^a-zA-Z0-9\s]', ' ', response_text.lower())
        
        # Define technology keywords to look for
        tech_keywords = {
            'docker', 'container', 'kubernetes', 'k8s', 'pod', 'kubectl',
            'excel', 'vlookup', 'pivot', 'vba', 'macro', 'power query', 'power pivot',
            'bloomberg', 'terminal', 'bdh', 'bdp', 'bds', 'bql',
            'python', 'script', 'programming', 'code',
            'aws', 'ec2', 'vpc', 's3', 'lambda', 'cloud',
            'linux', 'ubuntu', 'bash', 'command line', 'terminal',
            'network', 'dns', 'ip', 'subnet', 'router', 'firewall',
            'security', 'encryption', 'vpn', 'ssl', 'certificate',
            'ansible', 'terraform', 'infrastructure', 'automation',
            'github', 'git', 'ci/cd', 'actions', 'workflow',
            'proxmox', 'vmware', 'virtualization', 'hypervisor',
            'raspberry pi', 'pi-hole', 'iot',
            'openvpn', 'wireguard', 'pfsense',
            'powershell', 'cmdlet', 'scripting',
            'nmap', 'wireshark', 'kali', 'metasploit', 'penetration testing'
        }
        
        # Find keywords in the response
        found_keywords = []
        for keyword in tech_keywords:
            if keyword in cleaned_text:
                found_keywords.append(keyword)
        
        return found_keywords
    
    def match_documentation(self, response_text: str, top_k: int = 3, 
                          min_similarity: float = 0.1) -> List[Dict]:
        """Match documentation based on response content using OpenAI embeddings"""
        if not self.docs or self.doc_embeddings is None:
            return []
        
        # Extract keywords from response
        keywords = self.extract_keywords_from_response(response_text)
        
        # Create search query from response text and keywords
        search_text = response_text.lower() + ' ' + ' '.join(keywords)
        
        try:
            # Generate embedding for search text
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=[search_text]
            )
            
            search_embedding = np.array(response.data[0].embedding)
            
            # Calculate similarities with all documentation embeddings
            similarities = []
            for doc_embedding in self.doc_embeddings:
                similarity = self.cosine_similarity(search_embedding, doc_embedding)
                similarities.append(similarity)
            
            similarities = np.array(similarities)
            
            # Get top matches above threshold
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            matches = []
            for idx in top_indices:
                if similarities[idx] >= min_similarity:
                    doc = self.docs[idx].copy()
                    doc['similarity_score'] = similarities[idx]
                    doc['matched_keywords'] = keywords
                    matches.append(doc)
            
            return matches
            
        except Exception as e:
            print(f"❌ Error matching documentation: {e}")
            return []
    
    def format_documentation_links(self, matches: List[Dict]) -> str:
        """Format documentation matches for display"""
        if not matches:
            return ""
        
        formatted_links = ["\n📚 **Related Documentation:**"]
        
        for i, match in enumerate(matches, 1):
            formatted_links.append(
                f"{i}. **[{match['title']}]({match['url']})** ({match['difficulty']})"
            )
            formatted_links.append(f"   {match['description']}")
        
        return "\n".join(formatted_links)


# Test function to verify extraction works
def test_doc_matcher():
    """Test function to verify the documentation matcher works after extraction"""
    print("🧪 Testing SmartDocumentationMatcher extraction...")
    
    try:
        # Initialize doc matcher
        doc_matcher = SmartDocumentationMatcher()
        
        # Test query
        test_query = "How to setup Docker containers"
        matches = doc_matcher.match_documentation(test_query, top_k=3, min_similarity=0.2)
        
        print(f"✅ Test successful! Found {len(matches)} documentation matches")
        if matches:
            print("📚 Sample match:", matches[0]['title'])
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    # Run test when file is executed directly
    test_doc_matcher()