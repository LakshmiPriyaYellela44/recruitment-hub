"""
Vector Database - Pinecone Implementation (Optional/Paid)
Use if you prefer cloud-hosted vector DB instead of local Chroma
Requires PINECONE_API_KEY
"""

import logging
import os
from typing import List, Dict, Optional, Any
from datetime import datetime

try:
    from pinecone import Pinecone, ServerlessSpec
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False

logger = logging.getLogger(__name__)


class PineconeVectorDB:
    """
    Pinecone cloud vector database
    - Paid service (~$1-5/month for basic)
    - Hosted in cloud
    - Requires API key
    """
    
    def __init__(self):
        """Initialize Pinecone connection"""
        self.enabled = False
        self.client = None
        self.index = None
        
        if not PINECONE_AVAILABLE:
            logger.error("Pinecone SDK not installed: pip install pinecone-client")
            return
        
        api_key = os.getenv("PINECONE_API_KEY", "")
        index_name = os.getenv("PINECONE_INDEX_NAME", "recruitment-hub")
        
        if not api_key:
            logger.warning("PINECONE_API_KEY not set. Pinecone disabled.")
            return
        
        try:
            self.client = Pinecone(api_key=api_key)
            self.index_name = index_name
            self.index = self.client.Index(index_name)
            self.enabled = True
            
            logger.info(f"✅ Pinecone initialized with index: {index_name}")
        
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {e}")
            self.enabled = False
    
    def create_embedding(self, text: str) -> Optional[List[float]]:
        """Create embedding using OpenAI"""
        try:
            from openai import OpenAI
            
            api_key = os.getenv("OPENAI_API_KEY", "")
            if not api_key:
                logger.error("OPENAI_API_KEY not set")
                return None
            
            client = OpenAI(api_key=api_key)
            response = client.embeddings.create(
                input=text[:2000],
                model="text-embedding-3-small"
            )
            
            return response.data[0].embedding
        
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
        """Store candidate in Pinecone"""
        
        if not self.enabled:
            logger.warning("Pinecone not enabled")
            return False
        
        try:
            searchable_text = f"""
            {candidate_name}
            {candidate_email}
            {experience_years} years experience
            Skills: {', '.join(skills)}
            Resume: {resume_text[:500]}
            """.strip()
            
            embedding = self.create_embedding(searchable_text)
            if not embedding:
                return False
            
            self.index.upsert(
                vectors=[
                    (
                        str(candidate_id),
                        embedding,
                        {
                            "name": candidate_name,
                            "email": candidate_email,
                            "resume_score": resume_score,
                            "experience_years": experience_years,
                            "skills": ",".join(skills[:20]),
                        }
                    )
                ]
            )
            
            logger.info(f"✅ Stored {candidate_id} in Pinecone")
            return True
        
        except Exception as e:
            logger.error(f"Error storing in Pinecone: {e}")
            return False
    
    def search_candidates(
        self,
        query_text: str,
        top_k: int = 100
    ) -> List[Dict]:
        """Search similar candidates in Pine cone"""
        
        if not self.enabled:
            return []
        
        try:
            query_embedding = self.create_embedding(query_text)
            if not query_embedding:
                return []
            
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True
            )
            
            candidates = []
            for match in results.get("matches", []):
                candidates.append({
                    "candidate_id": match["id"],
                    "similarity_score": round(match["score"], 3),
                    "metadata": match.get("metadata", {})
                })
            
            logger.info(f"Found {len(candidates)} candidates in Pinecone")
            return candidates
        
        except Exception as e:
            logger.error(f"Error searching Pinecone: {e}")
            return []
    
    def delete_candidate(self, candidate_id: str) -> bool:
        """Delete from Pinecone"""
        if not self.enabled:
            return False
        
        try:
            self.index.delete(ids=[str(candidate_id)])
            return True
        except Exception as e:
            logger.error(f"Error deleting from Pinecone: {e}")
            return False
    
    def get_index_stats(self) -> Dict:
        """Get Pinecone stats"""
        if not self.enabled:
            return {"status": "disabled"}
        
        try:
            stats = self.index.describe_index_stats()
            return {
                "status": "active",
                "provider": "pinecone",
                "total_vectors": stats.get("total_vector_count", 0),
                "cost": "Paid (~$1-5/month)"
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"status": "error"}


_pinecone_db = None

def get_pinecone_db() -> PineconeVectorDB:
    """Get Pinecone instance"""
    global _pinecone_db
    if _pinecone_db is None:
        _pinecone_db = PineconeVectorDB()
    return _pinecone_db
