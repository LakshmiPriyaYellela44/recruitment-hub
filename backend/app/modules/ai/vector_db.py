"""
Vector Database - Smart Wrapper (Chroma FREE or Pinecone)
Automatically uses Chroma by default (FREE), can switch to Pinecone
"""

import logging
from typing import List, Dict, Optional
from app.modules.ai.config import AIConfig

logger = logging.getLogger(__name__)


class VectorDB:
    """
    Smart vector database wrapper
    - Uses Chroma by default (free, local)
    - Falls back to Pinecone if configured
    - Zero API key needed for Chroma
    """
    
    def __init__(self):
        """Initialize based on config"""
        self.provider = AIConfig.VECTOR_DB_PROVIDER
        self.db = None
        
        if self.provider == "chroma" or AIConfig.USE_CHROMA:
            self._init_chroma()
        elif self.provider == "pinecone" or AIConfig.PINECONE_API_KEY:
            self._init_pinecone()
        else:
            logger.warning("No vector DB provider configured - using Chroma")
            self._init_chroma()
    
    def _init_chroma(self):
        """Initialize Chroma (FREE, local)"""
        try:
            from app.modules.ai.vector_db_chroma import get_chroma_db
            self.db = get_chroma_db()
            self.provider = "chroma"
            logger.info("✅ Using Chroma vector DB (FREE, no API key needed)")
        except Exception as e:
            logger.error(f"Failed to initialize Chroma: {e}")
            self.db = None
    
    def _init_pinecone(self):
        """Initialize Pinecone (paid)"""
        try:
            from app.modules.ai.vector_db_pinecone import get_pinecone_db
            self.db = get_pinecone_db()
            self.provider = "pinecone"
            logger.info("✅ Using Pinecone vector DB")
        except Exception as e:
            logger.warning(f"Failed to initialize Pinecone: {e}")
            logger.info("Falling back to Chroma...")
            self._init_chroma()
    
    def create_embedding(self, text: str) -> Optional[List[float]]:
        """Create embedding using current provider"""
        if not self.db:
            logger.error("Vector DB not initialized")
            return None
        return self.db.create_embedding(text)
    
    def store_candidate(self, candidate_id: str, candidate_data: Dict = None, **kwargs) -> bool:
        """Store candidate - supports both old and new API"""
        if not self.db:
            return False
        
        # Support both APIs
        if candidate_data:
            return self.db.store_candidate(candidate_id, candidate_data.get("name", ""), 
                                         candidate_data.get("email", ""), 
                                         candidate_data.get("resume_score", 0),
                                         candidate_data.get("experience_years", 0),
                                         candidate_data.get("skills", []),
                                         candidate_data.get("summary", ""))
        return self.db.store_candidate(candidate_id, kwargs.get("candidate_name", ""),
                                     kwargs.get("candidate_email", ""),
                                     kwargs.get("resume_score", 0),
                                     kwargs.get("experience_years", 0),
                                     kwargs.get("skills", []),
                                     kwargs.get("resume_text", ""))
    
    def search_candidates(self, query_text: str, top_k: int = 100, **kwargs) -> List[Dict]:
        """Search candidates"""
        if not self.db:
            return []
        return self.db.search_candidates(query_text, top_k)
    
    def delete_candidate(self, candidate_id: str) -> bool:
        """Delete candidate"""
        if not self.db:
            return False
        return self.db.delete_candidate(candidate_id)
    
    def get_index_stats(self) -> Dict:
        """Get stats"""
        if not self.db:
            return {"status": "unavailable"}
        return self.db.get_index_stats()


# Singleton
_vector_db_instance = None

def get_vector_db() -> VectorDB:
    global _vector_db_instance
    if _vector_db_instance is None:
        _vector_db_instance = VectorDB()
    return _vector_db_instance
