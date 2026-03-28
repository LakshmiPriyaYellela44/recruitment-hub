from fastapi import Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import verify_token
from app.core.exceptions import AuthenticationException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.models import User

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user.
    Validates JWT token and returns the user object.
    """
    token = credentials.credentials
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    result = await db.execute(
        select(User)
        .filter(User.id == user_id)
        .options(
            selectinload(User.resumes),
            selectinload(User.experiences),
            selectinload(User.educations),
            selectinload(User.skills)
        )
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user


def require_role(role: str):
    """Dependency to require specific user role."""
    async def check_role(current_user: User = Depends(get_current_user)):
        if current_user.role.value != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires {role} role"
            )
        return current_user
    return check_role


async def require_admin(current_user: User = Depends(get_current_user)):
    """Dependency to require admin role."""
    if current_user.role.value != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action requires ADMIN role"
        )
    return current_user


def require_subscription(min_subscription: str = "PRO"):
    """Dependency to require minimum subscription level."""
    async def check_subscription(current_user: User = Depends(get_current_user)):
        if min_subscription == "PRO" and current_user.subscription_type.value != "PRO":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This feature requires PRO subscription"
            )
        return current_user
    return check_subscription


async def get_current_user_with_query_token(
    token: str = Query(None),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current user from query parameter token.
    Used for endpoints like resume viewing that are opened in a new tab.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    result = await db.execute(
        select(User)
        .filter(User.id == user_id)
        .options(
            selectinload(User.resumes),
            selectinload(User.experiences),
            selectinload(User.educations),
            selectinload(User.skills)
        )
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user


async def get_current_user_ws(websocket) -> User:
    """
    Get current user from WebSocket connection.
    Extracts token from query parameters or headers.
    """
    from app.core.database import get_db
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Try to get token from query parameters
    token = None
    if "token" in websocket.query_params:
        token = websocket.query_params.get("token")
        logger.info(f"[WebSocket Auth] Token found in query params")
    elif "authorization" in websocket.headers:
        auth_header = websocket.headers.get("authorization")
        if auth_header and auth_header.lower().startswith("bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix
            logger.info(f"[WebSocket Auth] Token found in headers")
    
    if not token:
        logger.error("[WebSocket Auth] No token found in query params or headers")
        logger.error(f"[WebSocket Auth] Query params: {dict(websocket.query_params)}")
        logger.error(f"[WebSocket Auth] Headers available: {list(websocket.headers.keys())}")
        raise Exception("No authentication token provided")
    
    logger.info(f"[WebSocket Auth] Token length: {len(token)} chars")
    
    payload = verify_token(token)
    if not payload:
        logger.error("[WebSocket Auth] Token verification failed")
        raise Exception("Invalid authentication token")
    
    user_id = payload.get("sub")
    if not user_id:
        logger.error("[WebSocket Auth] No user_id in token payload")
        raise Exception("Invalid token payload")
    
    logger.info(f"[WebSocket Auth] User ID from token: {user_id}")
    
    # Get database session
    async for db in get_db():
        result = await db.execute(
            select(User)
            .filter(User.id == user_id)
            .options(
                selectinload(User.resumes),
                selectinload(User.experiences),
                selectinload(User.educations),
                selectinload(User.skills)
            )
        )
        user = result.scalars().first()
        if not user:
            logger.error(f"[WebSocket Auth] User not found for ID: {user_id}")
            raise Exception("User not found")
        
        logger.info(f"[WebSocket Auth] User authenticated: {user.email} (role: {user.role.value})")
        return user
