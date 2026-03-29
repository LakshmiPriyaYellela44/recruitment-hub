"""
Vector Database - Chroma Implementation (FREE/Local)
No API keys needed, runs locally on your server
Can store unlimited vectors, completely free
"""

import logging
import os
from typing import List, Dict, Optional, Any
import numpy as np

logger = logging.getLogger(__name__)

try:
    import chromadb
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    logger.warning("Chroma not installed. Install with: pip install chromadb")

from app.modules.ai.config import AIConfig


class ChromaVectorDB:
    """
    Local vector database using Chroma (completely FREE)
    - No API keys needed
    - Runs on your server
    - Unlimited storage
    - Instant search
    """
    
    def __init__(self):
        """Initialize Chroma"""
        if not CHROMA_AVAILABLE:
            logger.error("Chroma not installed")
            self.client = None
            self.collection = None
            return
        
        try:
            # Create persistent client
            db_path = AIConfig.CHROMA_DB_PATH
            os.makedirs(db_path, exist_ok=True)
            
            self.client = chromadb.PersistentClient(path=db_path)
            self.collection = self.client.get_or_create_collection(
                name=AIConfig.CHROMA_COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"}  # Cosine similarity
            )
            
            logger.info(f"✅ Chroma initialized at {db_path}")
            logger.info(f"Collection: {AIConfig.CHROMA_COLLECTION_NAME}")
        
        except Exception as e:
            logger.error(f"Failed to initialize Chroma: {e}")
            self.client = None
            self.collection = None
    
    def create_embedding(self, text: str) -> Optional[List[float]]:
        """
        Create embedding for text using Google Gemini
        Returns 768-dim vector
        """
        try:
            if not text or len(text.strip()) < 2:
                logger.warning("Text too short for embedding")
                return None
            
            # Import here to avoid circular dependencies
            from app.modules.ai.resume_parser import get_llm_client
            
            llm = get_llm_client()
            if not llm:
                logger.error("LLM client not available")
                return None
            
            # Use LLM to create embedding
            if hasattr(llm, 'embed_content'):
                # Google Gemini API
                response = llm.embed_content(
                    model='models/embedding-001',
                    content=text[:2000]  # Max 2000 chars
                )
                embedding = response['embedding']
            else:
                # Fallback: OpenAI embedding
                response = llm.embeddings.create(
                    input=text[:2000],
                    model=AIConfig.EMBEDDING_MODEL
                )
                embedding = response.data[0].embedding
            
            logger.debug(f"✅ Created embedding: {len(embedding)} dimensions")
            return embedding
        
        except Exception as e:
            logger.error(f"Error creating embedding: {e}")
            return None
    
    def store_candidate(
        self,
        candidate_id: str,
        candidate_name: str,
        candidate_email: str,
        resume_score: int,
        experience_years: float,
        skills: List[str],
        resume_text: str
    ) -> bool:
        """
        Store candidate in Chroma for semantic search
        
        Args:
            candidate_id: Unique candidate ID
            candidate_name: Full name
            candidate_email: Email address
            resume_score: 0-100 quality score
            experience_years: Years of experience
            skills: List of skills
            resume_text: Full resume text for embedding
        
        Returns:
            True if stored successfully
        """
        
        if not self.collection:
            logger.error("Chroma collection not available")
            return False
        
        try:
            # Create searchable text
            searchable_text = f"""
            Candidate: {candidate_name}
            Email: {candidate_email}
            Experience: {experience_years} years
            Skills: {', '.join(skills)}
            Resume: {resume_text[:1000]}
            """.strip()
            
            # Create embedding
            embedding = self.create_embedding(searchable_text)
            if not embedding:
                logger.error(f"Failed to create embedding for {candidate_id}")
                return False
            
            # Store in Chroma
            self.collection.upsert(
                ids=[candidate_id],
                embeddings=[embedding],
                documents=[searchable_text],
                metadatas=[{
                    "name": candidate_name,
                    "email": candidate_email,
                    "resume_score": resume_score,
                    "experience_years": experience_years,
                    "skills": ",".join(skills[:20]),  # Top 20 skills
                }]
            )
            
            logger.info(f"✅ Stored candidate {candidate_id} in Chroma")
            return True
        
        except Exception as e:
            logger.error(f"Error storing candidate: {e}")
            return False
    
    def search_candidates(
        self,
        query_text: str,
        top_k: int = 100
    ) -> List[Dict]:
        """
        Search similar candidates using semantic search
        
        Args:
            query_text: Search query
            top_k: Return top K results
        
        Returns:
            List of candidates with similarity scores
        """
        
        if not self.collection:
            logger.error("Chroma collection not available")
            return []
        
        try:
            # Create embedding for query
            query_embedding = self.create_embedding(query_text)
            if not query_embedding:
                logger.error("Failed to create query embedding")
                return []
            
            # Search in Chroma
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            candidates = []
            if results and results['ids'] and len(results['ids']) > 0:
                for i, candidate_id in enumerate(results['ids'][0]):
                    # Chroma returns distances, convert to similarity (0-1)
                    distance = results['distances'][0][i] if results['distances'] else 0
                    similarity = 1 - (distance / 2)  # Normalize cosine distance
                    
                    metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                    
                    candidates.append({
                        "candidate_id": candidate_id,
                        "similarity_score": max(0, min(1, similarity)),  # Clamp 0-1
                        "document": results['documents'][0][i] if results['documents'] else "",
                        "metadata": metadata
                    })
            
            logger.info(f"✅ Found {len(candidates)} candidates for query")
            return candidates
        
        except Exception as e:
            logger.error(f"Error searching candidates: {e}")
            return []
    
    def delete_candidate(self, candidate_id: str) -> bool:
        """Delete candidate from vector DB"""
        
        if not self.collection:
            return False
        
        try:
            self.collection.delete(ids=[candidate_id])
            logger.info(f"✅ Deleted candidate {candidate_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting candidate: {e}")
            return False
    
    def get_index_stats(self) -> Dict:
        """Get statistics about the vector DB"""
        
        if not self.collection:
            return {"status": "unavailable", "error": "Chroma not initialized"}
        
        try:
            count = self.collection.count()
            return {
                "status": "active",
                "provider": "chroma",
                "total_candidates": count,
                "collection_name": AIConfig.CHROMA_COLLECTION_NAME,
                "db_path": AIConfig.CHROMA_DB_PATH,
                "cost": "FREE"
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"status": "error", "error": str(e)}
    
    def clear_all(self) -> bool:
        """Clear all candidates (for testing)"""
        
        if not self.collection:
            return False
        
        try:
            # Get all IDs and delete them
            all_data = self.collection.get()
            if all_data['ids']:
                self.collection.delete(ids=all_data['ids'])
                logger.info(f"✅ Cleared {len(all_data['ids'])} candidates from Chroma")
            return True
        except Exception as e:
            logger.error(f"Error clearing Chroma: {e}")
            return False


# Singleton instance
_chroma_db = None

def get_chroma_db() -> ChromaVectorDB:
    """Get Chroma instance"""
    global _chroma_db
    if _chroma_db is None:
        _chroma_db = ChromaVectorDB()
    return _chroma_db
