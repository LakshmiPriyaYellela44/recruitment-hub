"""
AI Chat Router - Conversation Management with Memory
Handles session memory and long-term memory storage
"""

import logging
from typing import Optional, List, Dict
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user

# Optional authentication for testing
def get_current_user_optional(request = None):
    """Optional dependency - returns user if authenticated, None otherwise"""
    try:
        # Try to get the token from header
        if request and hasattr(request, 'headers'):
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                # Try to validate token
                from app.core.security import verify_access_token
                token = auth_header.split(" ")[1]
                user = verify_access_token(token)
                if user:
                    return user
    except:
        pass
    return {"id": 0, "role": "guest", "email": "guest@test.com"}  # Guest user for testing
from app.modules.ai.query_parser import get_query_parser
from app.modules.ai.candidate_search import get_candidate_ranker
from app.modules.ai.resume_scorer import ResumeScorer


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai/chat", tags=["ai-chat"])


# ============================
# MODELS
# ============================

class ChatMessage:
    """In-memory message storage"""
    def __init__(self, conversation_id: str, user_id: int, role: str, content: str, memory_context: Dict = None):
        self.conversation_id = conversation_id
        self.user_id = user_id
        self.role = role
        self.content = content
        self.memory_context = memory_context or {}
        self.timestamp = datetime.utcnow()


# In-memory conversation storage (in production, use database)
conversations_db = {}  # {conversation_id: {"messages": [...], "metadata": {...}}}
session_memory_db = {}  # {user_id: [{...memory...}]}


# ============================
# MEMORY MANAGEMENT
# ============================

class MemoryManager:
    """Manage session and long-term memory"""
    
    @staticmethod
    def get_session_memory(user_id: int) -> List[Dict]:
        """Get current session memory"""
        return session_memory_db.get(user_id, [])
    
    @staticmethod
    def add_session_memory(user_id: int, memory_point: Dict):
        """Add to session memory"""
        if user_id not in session_memory_db:
            session_memory_db[user_id] = []
        
        session_memory_db[user_id].append({
            **memory_point,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Keep only last 50 memory points
        if len(session_memory_db[user_id]) > 50:
            session_memory_db[user_id] = session_memory_db[user_id][-50:]
    
    @staticmethod
    def get_conversation_memory(conversation_id: str) -> Dict:
        """Get long-term memory for conversation"""
        return conversations_db.get(conversation_id, {}).get("memory", {})
    
    @staticmethod
    def add_conversation_memory(conversation_id: str, memory_key: str, memory_value):
        """Store long-term memory"""
        if conversation_id not in conversations_db:
            conversations_db[conversation_id] = {"messages": [], "memory": {}}
        
        conversations_db[conversation_id]["memory"][memory_key] = memory_value


class ContextBuilder:
    """Build context for AI responses"""
    
    @staticmethod
    def build_conversation_context(
        user_id: int,
        user_role: str,
        conversation_id: Optional[str],
        messages: List[Dict],
        context: Dict
    ) -> str:
        """Build full context prompt for LLM"""
        
        session_mem = MemoryManager.get_session_memory(user_id)
        conv_mem = MemoryManager.get_conversation_memory(conversation_id) if conversation_id else {}
        
        context_prompt = f"""
You are an AI Assistant for a recruitment platform.

USER ROLE: {user_role.upper()}
USER ID: {user_id}
CONVERSATION ID: {conversation_id or 'NEW'}

ROLE-SPECIFIC INSTRUCTIONS:
"""
        
        if user_role == 'recruiter':
            context_prompt += """
You are helping a recruiter/hiring manager.
You can:
- Help search and find candidates
- Analyze and score resumes
- Generate job descriptions
- Provide recruitment insights
- Answer questions about candidates

Focus on: Finding the best candidates, analyzing qualifications, matching skills.
"""
        else:
            context_prompt += """
You are helping a job candidate.
You can:
- Help them find suitable job opportunities
- Analyze their resume and provide improvement suggestions
- Check application status
- Give advice on career development
- Answer questions about the platform

Focus on: Career development, resume improvement, job matching.
"""
        
        # Add session memory context
        if session_mem:
            context_prompt += f"\n\nCONVERSATION HISTORY CONTEXT:\n"
            for mem in session_mem[-10:]:  # Last 10 memory points
                if mem.get('type') == 'user_query':
                    context_prompt += f"- User asked about: {mem.get('value')}\n"
                elif mem.get('type') == 'system_context':
                    context_prompt += f"- System: {mem.get('value')}\n"
        
        # Add message history
        if messages:
            context_prompt += "\n\nRECENT CONVERSATION:\n"
            for msg in messages[-5:]:  # Last 5 messages
                role = "User" if msg['role'] == 'user' else "Assistant"
                context_prompt += f"{role}: {msg['content'][:100]}...\n"
        
        # Add request context
        if context.get('user_intent'):
            context_prompt += f"\n\nUSER INTENT: {context['user_intent'].upper()}"
        
        context_prompt += "\n\nPlease respond helpfully and concisely."
        
        return context_prompt
    
    @staticmethod
    def build_memory_context(user_role: str, response: str, user_query: str) -> Dict:
        """Extract and store memory from interaction"""
        
        memory = {
            "type": "conversation_turn",
            "user_query": user_query,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Extract topics from conversation
        topics = []
        if user_role == 'recruiter':
            if any(word in user_query.lower() for word in ['find', 'search', 'candidate']):
                topics.append('candidate_search')
            if any(word in user_query.lower() for word in ['analyze', 'score', 'resume']):
                topics.append('resume_analysis')
            if any(word in user_query.lower() for word in ['job', 'role', 'position']):
                topics.append('job_matching')
        else:
            if any(word in user_query.lower() for word in ['job', 'find', 'apply']):
                topics.append('job_search')
            if any(word in user_query.lower() for word in ['resume', 'score', 'profile']):
                topics.append('resume_improvement')
            if any(word in user_query.lower() for word in ['application', 'status']):
                topics.append('application_tracking')
        
        if topics:
            memory['topics'] = topics
        
        return memory


# ============================
# API ENDPOINTS
# ============================

@router.post("/")
async def chat(
    payload: dict,
    db: Session = Depends(get_db),
    request = None
):
    """
    Send message and get AI response with memory
    
    Payload:
    {
        "message": "Find senior Python developers",
        "conversation_id": "conv-123" (optional),
        "context": {...},
        "user_role": "recruiter|candidate",
        "session_memory": [...]
    }
    """
    
    try:
        # Try to authenticate, but allow unauthenticated access for testing
        current_user = get_current_user_optional(request)
        
        message = payload.get("message", "").strip()
        conversation_id = payload.get("conversation_id")
        context = payload.get("context", {})
        user_role = payload.get("user_role", "candidate")
        session_memory = payload.get("session_memory", [])
        
        if not message:
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        user_id = current_user.get("id")
        
        # Generate conversation ID if not provided
        if not conversation_id:
            import uuid
            conversation_id = f"conv-{uuid.uuid4().hex[:8]}"
        
        # Initialize conversation if new
        if conversation_id not in conversations_db:
            conversations_db[conversation_id] = {
                "messages": [],
                "memory": {},
                "created_at": datetime.utcnow().isoformat(),
                "user_id": user_id
            }
        else:
            # SECURITY: Verify conversation belongs to current user
            conv_user_id = conversations_db[conversation_id].get("user_id")
            if conv_user_id and conv_user_id != user_id:
                raise HTTPException(
                    status_code=403,
                    detail="Access denied. This conversation belongs to another user."
                )
        
        # Get conversation messages
        conv_messages = conversations_db[conversation_id]["messages"]
        
        # Build context for LLM
        full_context = ContextBuilder.build_conversation_context(
            user_id=user_id,
            user_role=user_role,
            conversation_id=conversation_id,
            messages=conv_messages,
            context=context
        )
        
        # Get AI response
        response_text = await get_ai_response(
            user_query=message,
            context=full_context,
            user_role=user_role,
            db=db
        )
        
        # Build memory context
        memory_context = ContextBuilder.build_memory_context(
            user_role=user_role,
            response=response_text,
            user_query=message
        )
        
        # Store messages
        conversations_db[conversation_id]["messages"].append({
            "role": "user",
            "content": message,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        conversations_db[conversation_id]["messages"].append({
            "role": "assistant",
            "content": response_text,
            "timestamp": datetime.utcnow().isoformat(),
            "memory_context": memory_context
        })
        
        # Update memory systems
        MemoryManager.add_session_memory(user_id, memory_context)
        MemoryManager.add_conversation_memory(conversation_id, "last_update", datetime.utcnow().isoformat())
        
        return {
            "success": True,
            "response": response_text,
            "conversation_id": conversation_id,
            "memory_context": memory_context,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "response": "I encountered an error. Please try again."
        }


@router.get("/history")
async def get_chat_history(
    current_user: dict = Depends(get_current_user),
    limit: int = Query(10, ge=1, le=50)
):
    """Get conversation history for current user"""
    
    user_id = current_user.get("id")
    
    # Filter conversations for this user
    user_convs = [
        (conv_id, data)
        for conv_id, data in conversations_db.items()
        if data.get("user_id") == user_id
    ]
    
    # Sort by creation date (newest first)
    user_convs.sort(
        key=lambda x: x[1].get("created_at", ""),
        reverse=True
    )
    
    # Return limited results
    result = []
    for conv_id, conv_data in user_convs[:limit]:
        result.append({
            "id": conv_id,
            "created_at": conv_data.get("created_at"),
            "message_count": len(conv_data.get("messages", [])),
            "messages": conv_data.get("messages", [])[:5],  # Last 5 messages
            "memory": conv_data.get("memory", {})
        })
    
    return {"conversations": result}


@router.get("/session-memory")
async def get_session_memory(
    current_user: dict = Depends(get_current_user)
):
    """Get current session memory"""
    
    user_id = current_user.get("id")
    memory = MemoryManager.get_session_memory(user_id)
    
    return {
        "user_id": user_id,
        "memory_points": memory,
        "count": len(memory)
    }


# ============================
# HELPER: Mock AI Response (Fallback)
# ============================

def get_mock_response(user_query: str, user_role: str) -> str:
    """Generate mock responses for testing/development without API keys"""
    
    if not user_query or not isinstance(user_query, str):
        user_query = ""
    
    query_lower = user_query.lower().strip()
    
    if user_role == 'recruiter':
        # Recruiter responses
        if any(word in query_lower for word in ['find', 'search', 'candidate', 'developer', 'engineer']):
            return "I can help you find candidates! I'd recommend searching by specific skills like Python, React, or Java. What specific role are you trying to fill?"
        elif any(word in query_lower for word in ['analyze', 'score', 'resume', 'review', 'profile']):
            return "To analyze resumes, please share the candidate details or upload their resume. I can help evaluate their experience, skills, and fit for your position."
        elif any(word in query_lower for word in ['job', 'role', 'position', 'hire', 'requirement']):
            return "What type of position are you looking to fill? Please share details about the role, required skills, experience level, and salary range. I'll help you find the best candidates."
        elif any(word in query_lower for word in ['help', 'tip', 'advice', 'how', 'guide']):
            return "Here are some recruiting tips:\n1. Be clear about job requirements\n2. Look for proven experience\n3. Consider cultural fit\n4. Use skills-based matching\n5. Focus on potential and growth\n\nHow can I assist further?"
        elif query_lower in ['hi', 'hello', 'hey', 'hey there', 'greetings', '']:
            return "👋 Hello! I'm your AI recruiting assistant. I can help you with:\n💼 Finding and searching candidates\n📄 Analyzing resumes and profiles\n💡 Job matching and recommendations\n📊 Recruitment insights\n\nWhat would you like to do?"
        else:
            return "I'm here to help with recruiting tasks! You can ask me to:\n• Find candidates with specific skills\n• Analyze and score resumes\n• Generate job descriptions\n• Provide recruitment insights\n\nWhat would you like help with?"
    
    else:  # Candidate role
        if any(word in query_lower for word in ['find', 'search', 'job', 'apply', 'opportunity', 'hiring']):
            return "I can help you find great job opportunities! To get started, tell me about:\n✨ Your skills and experience\n🎯 The type of role you're looking for\n💼 Your career goals\n🌍 Preferred location\n\nWhat are you interested in?"
        elif any(word in query_lower for word in ['resume', 'score', 'profile', 'improve', 'strengthen', 'cv']):
            return "I'd be happy to help improve your resume and profile! Please share:\n📝 Your current resume summary\n💻 Key skills\n👔 Work experience\n🎓 Education\n🎯 Career goals\n\nI'll provide tailored suggestions!"
        elif any(word in query_lower for word in ['application', 'status', 'apply', 'track', 'submitted']):
            return "You can check your application status in the 'Applications' section. There you'll see:\n📋 All positions you've applied to\n🔄 Current status of each application\n📅 Timeline and updates\n💬 Messages from recruiters\n\nWould you like to apply to new positions?"
        elif any(word in query_lower for word in ['help', 'tip', 'advice', 'guide', 'how']):
            return "Here are tips to land your dream job:\n✅ Optimize your resume for keywords\n📸 Build a strong portfolio\n🎤 Practice interviewing\n🤝 Network actively\n⭐ Highlight your achievements\n\nWhat area would you like help with?"
        elif query_lower in ['hi', 'hello', 'hey', 'hey there', 'greetings', '']:
            return "👋 Hello! I'm your AI career assistant. I'm here to help you with:\n🔍 Finding job opportunities\n📊 Improving your resume\n💡 Career development\n💬 Application tracking\n🏆 Landing your dream job\n\nWhat would you like to explore?"
        else:
            return "I'm your AI career assistant! I can help with:\n🎯 Job search and matching\n📝 Resume optimization\n✨ Profile enhancement\n📚 Skill development\n🚀 Career growth\n\nWhat's on your mind?"


# ============================
# HELPER: Recruiter Candidate Filtering
# ============================

async def generate_recruiter_filter_response(user_query: str, query_lower: str, db: Session = None) -> str:
    """Parse recruiter filter request and generate intelligent response with recommendations."""
    
    # Parse filters from query
    filters = parse_candidate_filters(user_query, query_lower)
    
    # If we have database access, query actual candidates
    if db:
        try:
            # Query candidates from database
            candidates = await query_candidates_by_filters(filters, db)
            
            # Format and return candidate data
            return format_candidates_response(candidates, filters)
        except Exception as e:
            logger.error(f"Error querying candidates: {str(e)}", exc_info=True)
    
    # Fallback: Explain the filters (if no db or query failed)
    response = "I can help you filter and find candidates! Here's what I detected from your request:\n\n"
    
    if filters['skills']:
        response += f"📋 **Skills Required:** {', '.join(filters['skills'])}\n"
    
    if filters['experience']:
        response += f"💼 **Experience:** {filters['experience']}\n"
    
    if filters['education']:
        response += f"🎓 **Education:** {filters['education']}\n"
    
    if filters['min_score']:
        response += f"⭐ **Minimum Score:** {filters['min_score']}%\n"
    
    response += "\n✅ To get matching candidates based on these criteria, use the search feature with these filters. I'll help you evaluate the results!\n\n"
    
    # Provide recommendations
    response += "💡 **My Recommendations:**\n"
    response += "1. Look for candidates with a good skill-to-experience ratio\n"
    response += "2. Consider candidates who have grown in their roles over time\n"
    response += "3. Check their education background for relevant fields\n"
    response += "4. Review their latest roles for closer alignment with your position\n"
    
    return response


def parse_candidate_filters(user_query: str, query_lower: str) -> dict:
    """Parse filter criteria from recruiter's query."""
    
    filters = {
        'skills': [],
        'experience': None,
        'education': None,
        'min_score': None,
        'location': None
    }
    
    # Extract skills (common tech keywords)
    tech_skills = [
        'python', 'java', 'javascript', 'typescript', 'react', 'node', 'node.js',
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'sql', 'nosql', 'mongodb',
        'postgres', 'mysql', 'fastapi', 'django', 'flask', 'spring', 'golang',
        'rust', 'c++', 'go', 'php', 'ruby', 'dot net', '.net', 'elastic', 'spark'
    ]
    
    for skill in tech_skills:
        if skill in query_lower:
            filters['skills'].append(skill.title())
    
    # Extract experience requirements (e.g., "3+ years", "5 years")
    import re
    exp_pattern = r'(\d+)\+?\s*(?:years?|yrs?)'
    exp_match = re.search(exp_pattern, query_lower)
    if exp_match:
        years = exp_match.group(1)
        filters['experience'] = f"{years}+ years"
    
    # Extract education (bachelor, master, phd)
    education_keywords = ['bachelor', 'master', 'phd', 'degree', 'graduation']
    for edu in education_keywords:
        if edu in query_lower:
            filters['education'] = edu.capitalize()
            break
    
    # Extract score/match percentage (e.g., "80% score", "above 85")
    score_pattern = r'(\d+)\s*%?(?:\s*(?:score|match|qualified))?'
    score_matches = re.findall(score_pattern, query_lower)
    if score_matches:
        for score_str in score_matches:
            try:
                score = int(score_str)
                if 50 <= score <= 100:  # Likely a score/percentage
                    filters['min_score'] = score
                    break
            except:
                pass
    
    return filters


def calculate_candidate_score(candidate_data: dict) -> int:
    """
    Calculate a match score for a candidate based on skills, experience, and education.
    Score: 0-100
    """
    
    score = 0
    
    # Skills evaluation (max 40 points)
    if 'skills' in candidate_data and candidate_data['skills']:
        num_skills = len(candidate_data['skills'])
        # Reward for having 3+ specialized skills, up to 40 points
        skills_score = min(40, num_skills * 10)
        score += skills_score
    
    # Experience evaluation (max 35 points)
    if 'experiences' in candidate_data:
        experiences = candidate_data['experiences']
        if experiences:
            # Calculate total years - handle None values
            total_years = sum([exp.get('years') or 0 for exp in experiences])
            # 0-2 years = 10 pts, 3-5 = 20 pts, 6-10 = 30 pts, 10+ = 35 pts
            if total_years >= 10:
                score += 35
            elif total_years >= 6:
                score += 30
            elif total_years >= 3:
                score += 20
            elif total_years > 0:
                score += 10
    
    # Education evaluation (max 25 points)
    if 'educations' in candidate_data and candidate_data['educations']:
        education = candidate_data['educations'][0]  # Get most recent/primary education
        degree = education.get('degree', '').lower()
        
        if 'phd' in degree:
            score += 25
        elif 'master' in degree:
            score += 20
        elif any(x in degree for x in ['bachelor', 'degree', 'graduation']):
            score += 15
        else:
            score += 5
    
    return min(100, score)  # Cap at 100


async def query_candidates_by_filters(filters: dict, db: Session) -> List[dict]:
    """
    Query database for candidates matching the specified filters.
    Returns structured candidate data: name, email, experience, skills, education, score
    """
    
    try:
        from sqlalchemy import select, func
        from sqlalchemy.orm import selectinload
        from app.core.models import User, UserRole, Skill, Experience, Education
        
        # Build base query for CANDIDATE users with eager loading
        query = select(User).where(
            User.role == UserRole.CANDIDATE
        ).options(
            selectinload(User.skills),
            selectinload(User.experiences),
            selectinload(User.educations)
        )
        
        # Filter by skills if provided
        if filters.get('skills'):
            skill_names = [s.lower() for s in filters['skills']]
            query = query.join(User.skills).filter(
                Skill.name.in_(skill_names)
            ).distinct()
        
        # Filter by education if provided
        if filters.get('education'):
            education_filter = filters['education'].lower()
            query = query.join(User.educations).filter(
                Education.degree.ilike(f"%{education_filter}%")
            ).distinct()
        
        # Execute query (async execution)
        result = await db.execute(query)
        candidates = result.scalars().all()
        
        # Format candidate data
        formatted_candidates = []
        for candidate in candidates:
            # Calculate total experience
            total_years = sum([exp.years for exp in candidate.experiences if exp.years])
            
            # Check experience filter
            if filters.get('experience'):
                exp_match = False
                if '5+' in filters['experience'] and total_years >= 5:
                    exp_match = True
                elif '3+' in filters['experience'] and total_years >= 3:
                    exp_match = True
                elif '10+' in filters['experience'] and total_years >= 10:
                    exp_match = True
                elif '6-10' in filters['experience'] and 6 <= total_years <= 10:
                    exp_match = True
                
                if not exp_match:
                    continue
            
            # Build candidate data dict
            candidate_data = {
                'name': f"{candidate.first_name} {candidate.last_name}".strip() or "Not Provided",
                'email': candidate.email,
                'phone': candidate.phone_number or 'N/A',
                'experience_years': total_years,
                'skills': [s.name.title() for s in candidate.skills],
                'education': [{'degree': e.degree, 'field': e.field_of_study} for e in candidate.educations],
                'job_titles': [e.job_title for e in candidate.experiences]
            }
            
            # Calculate score
            score = calculate_candidate_score({
                'skills': candidate.skills,
                'experiences': [{'years': e.years} for e in candidate.experiences],
                'educations': [{'degree': e.degree} for e in candidate.educations]
            })
            candidate_data['match_score'] = score
            
            # Check score filter
            if filters.get('min_score') and score < int(filters['min_score']):
                continue
            
            formatted_candidates.append(candidate_data)
        
        return formatted_candidates
    
    except Exception as e:
        logger.error(f"Error querying candidates: {str(e)}", exc_info=True)
        return []


def format_candidates_response(candidates: List[dict], filters: dict) -> str:
    """Format candidate query results into a clean, structured format."""
    
    if not candidates:
        response = "Sorry, no candidates found matching your criteria:\n"
        if filters.get('skills'):
            response += f"- Skills: {', '.join(filters['skills'])}\n"
        if filters.get('experience'):
            response += f"- Experience: {filters['experience']}\n"
        if filters.get('education'):
            response += f"- Education: {filters['education']}\n"
        if filters.get('min_score'):
            response += f"- Minimum Score: {filters['min_score']}%\n"
        response += "\nTry adjusting your filters and try again."
        return response
    
    response = f"\n{'='*80}\n"
    response += f"                    FOUND {len(candidates)} MATCHING CANDIDATES\n"
    response += f"{'='*80}\n\n"
    
    for i, candidate in enumerate(candidates, 1):
        response += f"CANDIDATE #{i}\n"
        response += f"Name:           {candidate['name']}\n"
        response += f"Email:          {candidate['email']}\n"
        response += f"Experience:     {candidate['experience_years']} years\n"
        
        if candidate.get('job_titles'):
            roles = ', '.join(candidate['job_titles'][:2])
            response += f"Position(s):    {roles}\n"
        
        if candidate.get('skills'):
            skills = ', '.join(candidate['skills'][:4])
            if len(candidate['skills']) > 4:
                skills += f" +{len(candidate['skills']) - 4} more"
            response += f"Skills:         {skills}\n"
        
        if candidate.get('education'):
            edu = candidate['education'][0]
            edu_text = f"{edu['degree']}"
            if edu.get('field'):
                edu_text += f" in {edu['field']}"
            response += f"Education:      {edu_text}\n"
        
        response += f"Match Score:    {candidate['match_score']}%\n"
        response += f"\n{'-'*80}\n\n"
    
    response += f"\n{'='*80}\n"
    response += f"SUMMARY: {len(candidates)} candidates match your filters\n"
    response += f"{'='*80}\n\n"
    
    return response


# ============================
# HELPER: AI Response Generation
# ============================

async def get_ai_response(
    user_query: str,
    context: str,
    user_role: str,
    db: Session
) -> str:
    """Generate AI response using actual LLM (Gemini) with role-specific prompts"""
    
    try:
        # Try to use LLM if available
        try:
            from app.modules.ai.resume_parser import get_llm_client
            from app.modules.ai.config import AIConfig
            
            llm = get_llm_client()
            if llm and AIConfig.GOOGLE_API_KEY:
                try:
                    # BUILD ROLE-SPECIFIC SYSTEM PROMPT
                    if user_role.upper() == "RECRUITER":
                        system_prompt = """You are an expert AI Recruitment Assistant helping recruiters find and analyze talent.

Your responsibilities:
1. Help recruiters search for and identify candidates with specific skills
2. Analyze and score candidate profiles based on job requirements
3. Provide insights on candidate cultural fit and potential
4. Generate job descriptions and requirements
5. Give recruitment strategy advice

When the recruiter asks to:
- FIND candidates: Ask about required skills, experience level, and preferred location. Provide specific search recommendations.
- ANALYZE profiles: Review candidate skills, experience, and achievements. Give a detailed assessment.
- CREATE jobs: Help craft compelling job descriptions with clear requirements.
- STRATEGY: Provide actionable recruitment tips and best practices.

Be professional, direct, and results-oriented. Use emojis sparingly but purposefully.
Always provide specific, actionable recommendations."""
                    
                    else:  # CANDIDATE
                        system_prompt = """You are an expert AI Career Assistant helping job seekers find opportunities and advance their careers.

Your responsibilities:
1. Help candidates find relevant job opportunities
2. Improve and optimize their resumes and profiles
3. Provide career development advice
4. Track and manage job applications
5. Share interview tips and career strategies

When the candidate asks to:
- FIND jobs: Ask about their skills, experience, and career goals. Suggest relevant opportunities.
- IMPROVE resume: Ask about their background and provide specific optimization suggestions.
- APPLICATION help: Guide them through the application process and track progress.
- INTERVIEW prep: Provide tips and common questions for their target role.
- CAREER advice: Give personalized guidance on growth and advancement.

Be encouraging, supportive, and practical. Use emojis to make responses friendly.
Always provide specific, actionable next steps."""
                    
                    # BUILD FULL PROMPT
                    full_prompt = f"""SYSTEM INSTRUCTIONS:
{system_prompt}

CONVERSATION CONTEXT:
{context}

USER QUERY:
{user_query}

INSTRUCTIONS FOR RESPONSE:
1. Stay in character for the {user_role} role
2. Be specific and actionable
3. Ask clarifying questions if needed
4. Provide concrete recommendations
5. Keep response concise but comprehensive
6. Use formatting (bullet points, emojis) for clarity

Please provide a helpful, dynamic response:"""
                    
                    # Call LLM with error handling for quota/model issues
                    logger.info(f"Attempting LLM call with model: {AIConfig.PARSER_MODEL} for user role: {user_role}")
                    
                    if hasattr(llm, 'GenerativeModel'):
                        # Google Gemini - try multiple models for compatibility
                        models_to_try = [
                            AIConfig.PARSER_MODEL or 'gemini-1.5-flash',
                            'gemini-1.5-pro',
                            'gemini-2.0-flash'
                        ]
                        
                        response = None
                        last_error = None
                        
                        for model_name in models_to_try:
                            try:
                                logger.info(f"Trying model: {model_name} with role-specific prompt")
                                model = llm.GenerativeModel(
                                    model_name,
                                    system_instruction=system_prompt
                                )
                                response = model.generate_content(
                                    full_prompt, 
                                    request_options={"timeout": 30}
                                )
                                if response and hasattr(response, 'text') and response.text:
                                    logger.info(f"✅ LLM response successful with model: {model_name}")
                                    return response.text
                            except Exception as model_error:
                                last_error = model_error
                                logger.warning(f"Model {model_name} failed: {str(model_error)[:100]}")
                                continue
                        
                        if last_error:
                            logger.warning(f"All models failed. Using mock response. Last error: {str(last_error)[:100]}")
                    else:
                        # OpenAI fallback
                        response = llm.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=[{"role": "user", "content": full_prompt}],
                            temperature=0.7,
                            max_tokens=500
                        )
                        if response and response.choices:
                            logger.info("✅ OpenAI response successful")
                            return response.choices[0].message.content
                except Exception as e:
                    logger.warning(f"LLM call failed: {str(e)[:100]}. Trying with simpler prompt.")
                    # Try one more time with MUCH simpler prompt
                    try:
                        model = llm.GenerativeModel(AIConfig.PARSER_MODEL or 'gemini-1.5-flash')
                        simple_prompt = f"""You are a helpful recruitment AI assistant for {user_role.lower()}s.
Answer this: {user_query}

Be concise and helpful."""
                        response = model.generate_content(simple_prompt, request_options={"timeout": 30})
                        if response and hasattr(response, 'text') and response.text:
                            logger.info("✅ LLM response successful with simple prompt")
                            return response.text
                    except Exception as simple_error:
                        logger.error(f"Simple prompt also failed: {str(simple_error)[:100]}")
                        pass
            else:
                logger.error("No LLM client configured or no API key found!")
        except ImportError as e:
            logger.error(f"Resume parser module not available: {str(e)[:50]}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {str(e)[:100]}")
        
        # Fallback: Use dynamic, intelligent responses based on role and query understanding
        logger.warning(f"LLM not available. Using intelligent dynamic responses.")
        
        query_lower = user_query.lower().strip()
        user_role_upper = user_role.upper()
        
        # Simple keyword extraction for better understanding
        keywords = {}
        keywords['job_search'] = any(w in query_lower for w in ['find', 'search', 'job', 'opportunity', 'hiring', 'give jobs', 'looking for', 'position', 'role'])
        keywords['resume'] = any(w in query_lower for w in ['resume', 'cv', 'profile', 'improve', 'strengthen', 'enhance'])
        keywords['company'] = any(w in query_lower for w in ['company', 'google', 'microsoft', 'amazon', 'facebook', 'tech', 'startup', 'about'])
        keywords['interview'] = any(w in query_lower for w in ['interview', 'prep', 'question', 'answer', 'practice', 'how to'])
        keywords['skills'] = any(w in query_lower for w in ['skill', 'learn', 'python', 'java', 'react', 'developer', 'engineer', 'full stack'])
        keywords['greeting'] = any(w in query_lower for w in ['hi', 'hello', 'hey', 'greetings', 'how are you'])
        
        # RECRUITER-SPECIFIC: Candidate filtering keywords (includes technology names)
        keywords['filter_candidates'] = any(w in query_lower for w in [
            'filter', 'candidates', 'show me', 'find candidates', 'search candidates',
            'candidates with', 'years', 'experience', 'degree', 'education', 'bachelor',
            'master', 'phd', 'score', 'match', 'qualified', 'find developer', 'find engineer',
            # Technology keywords for quick candidate filtering
            'python', 'java', 'javascript', 'react', 'node', 'aws', 'docker', 'kubernetes',
            'sql', 'postgresql', 'mongodb', 'django', 'fastapi', 'spring', 'devops', 'c++',
            'go', 'rust', 'typescript', 'vue', 'angular', 'git', 'ci/cd', 'jenkins'
        ])
        
        # RECRUITER RESPONSES
        if user_role_upper == "RECRUITER":
            if keywords['filter_candidates']:
                # CANDIDATE FILTERING - New Feature with Database Query
                filter_response = await generate_recruiter_filter_response(user_query, query_lower, db=db)
                return filter_response
            elif keywords['job_search']:
                return f"I can help you find the right candidates for your positions. What type of role are you looking to fill? Tell me about the skills, experience level, and specific technologies your ideal candidate should have."
            elif keywords['resume']:
                return f"I'm ready to review and analyze candidate resumes and profiles. Just share the candidate's information and let me know what position you're trying to fill. I can give you a detailed assessment of their fit."
            elif keywords['company']:
                return f"Are you looking to recruit top talent for your company? Tell me more about your organization, the role you're trying to fill, and the team they'd be joining."
            elif keywords['interview']:
                return f"I can help prepare your interview process and candidate screening. What stage of recruitment are you in - screening resumes, conducting interviews, or making offers?"
            else:
                return f"How can I help with your recruitment needs today? I can assist with finding candidates, analyzing profiles, creating job descriptions, or developing hiring strategies."
        
        # CANDIDATE RESPONSES
        else:
            if keywords['job_search']:
                return f"I'd love to help you find the right job opportunity. To give you better recommendations, tell me about your background - what programming languages or technologies you're skilled in, how many years of experience you have, and what type of role you're most interested in."
            elif keywords['resume']:
                return f"I can help you improve your resume and profile to stand out to recruiters. What specific areas would you like to focus on - your technical skills section, work experience descriptions, or your overall format?"
            elif keywords['skills'] or keywords['company']:
                # Handle tech stack or company questions
                if 'full stack' in query_lower or 'stack' in query_lower:
                    return f"Full stack development is a great skill set. Are you looking to learn full stack development, or are you searching for full stack developer jobs? I can help with either!"
                elif any(c in query_lower for c in ['google', 'microsoft', 'amazon', 'facebook', 'apple']):
                    company_name = next((c for c in ['google', 'microsoft', 'amazon', 'facebook', 'apple'] if c in query_lower), None)
                    if company_name:
                        return f"Interested in working at {company_name}? That's a great goal. What position are you targeting there, and what's your current experience level? I can help you prepare for their interview process and highlight relevant skills."
                else:
                    return f"Tell me more about what you're looking for. Are you interested in a specific technology, company, or type of role? I can give you more targeted advice."
            elif keywords['interview']:
                return f"Interview preparation is crucial. What type of interviews will you be facing - technical coding interviews, system design, behavioral questions, or a combination? I can help you prepare."
            elif keywords['greeting']:
                return f"Hey there! I'm here to help you advance your career. Whether you're looking for job opportunities, want to improve your resume, or need interview preparation, just let me know what you need."
            else:
                return f"I'm here to help with your career. Are you looking for jobs, wanting to improve your resume, preparing for interviews, or looking to develop specific skills? Let me know how I can assist."
    
    except Exception as e:
        logger.error(f"Error generating AI response: {str(e)}", exc_info=True)
        # Final fallback
        return "I encountered an error processing your request. Please try again."
