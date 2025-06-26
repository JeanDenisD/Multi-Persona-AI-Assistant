#!/usr/bin/env python3
"""
NetworkChuck AI Chatbot - Fixed Embedding Pipeline
Handles vector embeddings for dual personality RAG system

Key Fixes:
1. Removed emoji characters from log messages (fixes Windows encoding issue)
2. Dynamic column detection for CSV files
3. Better error handling
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd

# Third-party imports
try:
    from langchain.schema import Document
    from langchain.embeddings import OpenAIEmbeddings
    from langchain.vectorstores import Pinecone as LangchainPinecone
    from pinecone import Pinecone, ServerlessSpec
    from dotenv import load_dotenv
except ImportError as e:
    print(f"ERROR: Missing required packages: {e}")
    print("Please install: pip install langchain openai pinecone-client python-dotenv")
    sys.exit(1)

# Load environment variables
load_dotenv()

# Project structure
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
LOGS_DIR = PROJECT_ROOT / "logs"

class EmbeddingPipeline:
    """Enhanced embedding pipeline with better error handling"""
    
    def __init__(self):
        """Initialize the embedding pipeline"""
        self.setup_logging()
        self.setup_components()
        
    def setup_logging(self):
        """Set up logging with Windows-compatible format (no emojis)"""
        # Ensure logs directory exists
        LOGS_DIR.mkdir(exist_ok=True)
        log_file = LOGS_DIR / "embedding_pipeline.log"
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Logging to: {log_file}")
        
    def setup_components(self):
        """Set up pipeline components"""
        self.logger.info("Setting up pipeline components...")
        self.logger.info(f"Working from project root: {PROJECT_ROOT}")
        
        # Validate environment variables
        required_vars = ['OPENAI_API_KEY', 'PINECONE_API_KEY']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            raise ValueError(f"Missing environment variables: {missing_vars}")
            
        # Initialize components
        try:
            # OpenAI Embeddings
            self.embeddings = OpenAIEmbeddings(
                model="text-embedding-3-small",
                openai_api_key=os.getenv('OPENAI_API_KEY')
            )
            
            # Pinecone
            self.pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
            self.index_name = "networkchuck-ai-chatbot"
            
            # Create index if it doesn't exist
            self._setup_pinecone_index()
            
        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}")
            raise
            
        self.logger.info("Components setup complete!")
        
    def _setup_pinecone_index(self):
        """Set up Pinecone index"""
        try:
            # Check if index exists
            existing_indexes = [index.name for index in self.pc.list_indexes()]
            
            if self.index_name not in existing_indexes:
                self.logger.info(f"Creating new Pinecone index: {self.index_name}")
                self.pc.create_index(
                    name=self.index_name,
                    dimension=1536,  # text-embedding-3-small dimension
                    metric='cosine',
                    spec=ServerlessSpec(
                        cloud='aws',
                        region='us-east-1'
                    )
                )
            else:
                self.logger.info(f"Using existing Pinecone index: {self.index_name}")
                
            self.index = self.pc.Index(self.index_name)
            
        except Exception as e:
            self.logger.error(f"Failed to setup Pinecone index: {e}")
            raise
    

    def load_transcript_data(self) -> List[Document]:
        """Load transcript data from CSV files"""
        self.logger.info("Loading transcript data...")
        documents = []
        
        # File paths
        nc_path = PROCESSED_DIR / "all_networkchuck_transcripts.csv"
        bloomy_path = PROCESSED_DIR / "all_bloomy_transcripts.csv"
        
        # Load NetworkChuck data
        try:
            self.logger.info(f"Loading from: {nc_path}")
            nc_df = pd.read_csv(nc_path)
            self.logger.info(f"Loaded {len(nc_df)} NetworkChuck transcripts")
            
            # Create documents using the correct column names
            for _, row in nc_df.iterrows():
                if pd.notna(row['text']) and str(row['text']).strip():
                    doc = Document(
                        page_content=str(row['text']),
                        metadata={
                            'segment_id': row.get('segment_id', 'unknown'),
                            'personality': 'networkchuck',
                            'video_id': row.get('video_id', 'unknown'),
                            'video_title': row.get('video_title', 'unknown'),
                            'video_url': row.get('video_url', 'unknown'),
                            'start_time': float(row.get('start_time', 0)),
                            'end_time': float(row.get('end_time', 0)),
                            'duration': float(row.get('duration', 0)),
                            'domain': row.get('domain', 'technology'),
                            'uploader': row.get('uploader', 'networkchuck'),
                            'upload_date': row.get('upload_date', 'unknown'),
                            'language': row.get('language', 'en'),
                            'video_duration': row.get('video_duration', 'unknown'),
                            'expertise_areas': row.get('expertise_areas', 'networking'),
                            'source_type': 'video_transcript'
                        }
                    )
                    documents.append(doc)
                    
        except Exception as e:
            self.logger.error(f"Error loading NetworkChuck data from {nc_path}: {e}")
            
        # Load Bloomy data
        try:
            self.logger.info(f"Loading from: {bloomy_path}")
            bloomy_df = pd.read_csv(bloomy_path)
            self.logger.info(f"Loaded {len(bloomy_df)} Bloomy transcripts")
            
            # Create documents using the correct column names
            for _, row in bloomy_df.iterrows():
                if pd.notna(row['text']) and str(row['text']).strip():
                    doc = Document(
                        page_content=str(row['text']),
                        metadata={
                            'segment_id': row.get('segment_id', 'unknown'),
                            'personality': 'bloomy',
                            'video_id': row.get('video_id', 'unknown'),
                            'video_title': row.get('video_title', 'unknown'),
                            'video_url': row.get('video_url', 'unknown'),
                            'start_time': float(row.get('start_time', 0)),
                            'end_time': float(row.get('end_time', 0)),
                            'duration': float(row.get('duration', 0)),
                            'domain': row.get('domain', 'finance'),
                            'uploader': row.get('uploader', 'bloomy'),
                            'upload_date': row.get('upload_date', 'unknown'),
                            'language': row.get('language', 'en'),
                            'video_duration': row.get('video_duration', 'unknown'),
                            'expertise_areas': row.get('expertise_areas', 'excel'),
                            'source_type': 'video_transcript'
                        }
                    )
                    documents.append(doc)
                    
        except Exception as e:
            self.logger.error(f"Error loading Bloomy data from {bloomy_path}: {e}")
            
        self.logger.info(f"Total documents loaded: {len(documents)}")
        return documents
    
    def create_vectorstore(self, documents: List[Document]) -> LangchainPinecone:
        """Create vector store from documents"""
        self.logger.info(f"Creating vectorstore with {len(documents)} documents...")
        
        try:
            # Create vectorstore
            vectorstore = LangchainPinecone.from_documents(
                documents=documents,
                embedding=self.embeddings,
                index_name=self.index_name
            )
            
            self.logger.info("Vectorstore created successfully!")
            return vectorstore
            
        except Exception as e:
            self.logger.error(f"Failed to create vectorstore: {e}")
            raise
    
    def save_metadata(self):
        """Save pipeline metadata"""
        self.logger.info("Saving pipeline metadata...")
        
        # Ensure embeddings directory exists
        embeddings_dir = PROCESSED_DIR / "embeddings"
        embeddings_dir.mkdir(exist_ok=True)
        
        metadata = {
            'pipeline_version': '1.0.0',
            'created_at': datetime.now().isoformat(),
            'embedding_model': 'text-embedding-3-small',
            'vectorstore': 'pinecone',
            'index_name': self.index_name,
            'personalities': ['networkchuck', 'bloomy']
        }
        
        metadata_path = embeddings_dir / "embedding_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
            
        self.logger.info(f"Metadata saved to: {metadata_path}")
    
    def run_pipeline(self) -> Optional[LangchainPinecone]:
        """Run the complete embedding pipeline"""
        try:
            self.logger.info("Starting embedding pipeline...")
            
            # Load documents
            documents = self.load_transcript_data()
            
            if not documents:
                raise ValueError("No documents loaded!")
            
            # Create vectorstore
            vectorstore = self.create_vectorstore(documents)
            
            # Save metadata
            self.save_metadata()
            
            self.logger.info("Pipeline completed successfully!")
            return vectorstore
            
        except Exception as e:
            self.logger.error(f"Pipeline failed: {e}")
            self.save_metadata()  # Save metadata even on failure
            raise

def main():
    """Main execution function"""
    print("NetworkChuck AI Chatbot - Embedding Pipeline")
    print("=" * 50)
    
    try:
        pipeline = EmbeddingPipeline()
        vectorstore = pipeline.run_pipeline()
        
        if vectorstore:
            print("\nSUCCESS: Embedding pipeline completed!")
            print("Your vectorstore is ready for the RAG system.")
        else:
            print("\nERROR: Pipeline failed to create vectorstore")
            
    except Exception as e:
        print(f"\nERROR: {e}")
        print("Check the logs in 'logs/embedding_pipeline.log' for details.")

if __name__ == "__main__":
    main()