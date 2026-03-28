# Backend Developer Guide

## 📁 Backend Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app entry point
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py              # Settings and environment variables
│   │   ├── database.py            # SQLAlchemy setup and session management
│   │   ├── security.py            # JWT and password hashing
│   │   ├── exceptions.py          # Custom exception classes
│   │   └── models.py              # All SQLAlchemy ORM models
│   │
│   ├── modules/
│   │   ├── __init__.py
│   │   ├── auth/                  # Authentication module
│   │   │   ├── __init__.py
│   │   │   ├── schemas.py         # Pydantic models
│   │   │   ├── repository.py      # Database operations
│   │   │   ├── service.py         # Business logic
│   │   │   └── router.py          # API endpoints
│   │   │
│   │   ├── candidate/             # Candidate profile module
│   │   │   ├── __init__.py
│   │   │   ├── schemas.py
│   │   │   ├── repository.py
│   │   │   ├── service.py
│   │   │   └── router.py
│   │   │
│   │   ├── resume/                # Resume management module
│   │   │   ├── __init__.py
│   │   │   ├── parser.py          # Resume parsing logic
│   │   │   ├── schemas.py
│   │   │   ├── repository.py
│   │   │   ├── service.py
│   │   │   └── router.py
│   │   │
│   │   ├── recruiter/             # Recruiter features module
│   │   │   ├── __init__.py
│   │   │   ├── schemas.py
│   │   │   ├── repository.py
│   │   │   ├── service.py
│   │   │   └── router.py
│   │   │
│   │   └── subscription/          # Subscription management module
│   │       ├── __init__.py
│   │       ├── schemas.py
│   │       ├── repository.py
│   │       ├── service.py
│   │       └── router.py
│   │
│   ├── aws_mock/                  # AWS services mocks
│   │   ├── __init__.py
│   │   ├── s3_client.py           # Mock S3 client
│   │   ├── sns_client.py          # Mock SNS/SQS clients
│   │   └── ses_client.py          # Mock SES client
│   │
│   ├── middleware/                # Custom middleware
│   │   ├── __init__.py
│   │   └── middleware.py          # Request/exception handling
│   │
│   ├── utils/                     # Utility functions
│   │   ├── __init__.py
│   │   ├── auth_utils.py          # Auth dependency injectors
│   │   ├── helpers.py             # Common helper functions
│   │   └── audit.py               # Audit logging
│   │
│   └── workers/                   # Background workers
│       ├── __init__.py
│       └── resume_worker.py       # Resume processing worker
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # Pytest fixtures and config
│   ├── test_security.py           # Security module tests
│   ├── test_auth.py               # Authentication tests
│   └── test_*.py                  # More tests
│
├── storage/                       # Local file storage (AWS S3 mock)
│   └── resumes/                   # Uploaded resume files
│
├── logs/                          # Application logs
│   ├── app.log                    # Application logs
│   └── emails.log                 # Email sending logs (mock SES)
│
├── .env                           # Environment variables
├── .env.example                   # Environment template
├── requirements.txt               # Python dependencies
├── .gitignore                     # Git ignore rules
├── pytest.ini                     # Pytest configuration
└── Dockerfile                     # Docker containerization

```

---

## 🚀 Getting Started

### 1. Setup Development Environment

```bash
# Clone or navigate to backend folder
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env with your database URL
# Example: postgresql://recruitment_user:recruitment_pass@localhost/recruitment_db
```

### 2. Initialize Database

```bash
python -c "from app.core.database import init_db; init_db()"
```

### 3. Run Development Server

```bash
# With auto-reload
uvicorn app.main:app --reload

# Server starts at http://localhost:8000
# API docs at http://localhost:8000/docs (Swagger UI)
# Alternative docs at http://localhost:8000/redoc (ReDoc)
```

---

## 📚 Module Structure Pattern

Each module follows this consistent pattern:

### schemas.py - Pydantic Data Validation

```python
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserResponse(UserBase):
    id: UUID
    role: str
    subscription_type: str
    created_at: datetime
    
    class Config:
        from_attributes = True  # For SQLAlchemy ORM
```

### repository.py - Database Access Layer

```python
from sqlalchemy.orm import Session
from app.core.models import User

class UserRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, user_id: UUID) -> User:
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_by_email(self, email: str) -> User:
        return self.db.query(User).filter(User.email == email).first()
    
    def create(self, user_data: UserCreate) -> User:
        user = User(**user_data.dict())
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
```

### service.py - Business Logic

```python
from app.modules.auth.repository import UserRepository
from app.utils.audit import log_audit

class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo
    
    async def register_user(self, user_data: UserCreate, current_user_id: UUID):
        # Check duplicate email
        if self.repo.get_by_email(user_data.email):
            raise ConflictException("Email already registered")
        
        # Create user
        user = self.repo.create(user_data)
        
        # Log audit
        await log_audit(
            action="user_registered",
            resource="users",
            resource_id=user.id,
            user_id=current_user_id
        )
        
        return user
```

### router.py - API Endpoints

```python
from fastapi import APIRouter, Depends, status
from app.utils.auth_utils import get_current_user

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    repo = UserRepository(db)
    service = UserService(repo)
    user = await service.register_user(user_data, current_user_id=None)
    return UserResponse.from_orm(user)

@router.get("/{user_id}")
async def get_user(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    if not user:
        raise NotFoundException(f"User not found: {user_id}")
    return UserResponse.from_orm(user)
```

---

## 🔐 Authentication & Authorization

### JWT Token Flow

```python
# In core/security.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
import bcrypt

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()

def verify_password(password: str, hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), hash.encode())

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET_KEY,
        algorithm="HS256"
    )
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=["HS256"]
        )
        return payload
    except JWTError:
        return None
```

### Role-Based Access Control

```python
# In utils/auth_utils.py
from fastapi import Depends, HTTPException, status

async def require_role(*allowed_roles: str):
    async def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker

# Usage in router
@router.post("/recruiter-feature")
async def recruiter_only(
    current_user: User = Depends(require_role("RECRUITER"))
):
    pass
```

### Subscription-Based Authorization

```python
# In modules/recruiter/service.py
async def send_email_to_candidate(self, candidate_id: UUID, email_data: dict):
    # Check subscription
    if self.current_user.subscription_type != "PRO":
        raise AuthorizationException(
            "Email sending requires PRO subscription"
        )
    
    # Send email...
    await self.ses_client.send_email(...)
```

---

## 📊 Database Interactions

### Query Examples

```python
# Simple get by ID
user = db.query(User).filter(User.id == user_id).first()

# Get with relationships loaded
user = (db.query(User)
    .options(joinedload(User.resumes))
    .filter(User.id == user_id)
    .first())

# Complex query with joins and filters
candidates = (db.query(User)
    .join(CandidateSkill)
    .join(Skill)
    .filter(User.role == "CANDIDATE")
    .filter(Skill.name.in_(["Python", "React"]))
    .distinct()
    .offset(offset)
    .limit(limit)
    .all())

# Aggregate query
total_candidates = db.query(User).filter(
    User.role == "CANDIDATE"
).count()

# Update operation
db.query(User).filter(User.id == user_id).update(
    {"subscription_type": "PRO"},
    synchronize_session=False
)
db.commit()
```

### Using SQLAlchemy Relationships

```python
# In core/models.py
class User(Base):
    __tablename__ = "users"
    id = Column(UUID, primary_key=True)
    email = Column(String, unique=True)
    
    # Relationships
    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    experiences = relationship("Experience", back_populates="user", cascade="all, delete-orphan")

class Resume(Base):
    __tablename__ = "resumes"
    id = Column(UUID, primary_key=True)
    user_id = Column(UUID, ForeignKey("users.id"))
    
    # Relationships
    user = relationship("User", back_populates="resumes")

# Usage
user = db.query(User).get(user_id)
print(user.resumes)  # Automatically loaded due to relationship
```

---

## 🔄 Event-Driven Architecture

### Publishing Events

```python
# In modules/resume/service.py
from app.aws_mock.sns_client import SNSClient

class ResumeService:
    def __init__(self, sns_client: SNSClient = Depends(get_sns_client)):
        self.sns = sns_client
    
    async def upload_resume(self, file, user_id):
        # Store file
        file_path = await self.s3_client.upload_file(...)
        
        # Create DB record
        resume = self.repo.create_resume(...)
        
        # Publish event
        await self.sns.publish(
            topic="resume-upload",
            message={
                "resume_id": str(resume.id),
                "user_id": str(user_id),
                "file_path": file_path,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return resume
```

### Subscribing to Events

```python
# In workers/resume_worker.py
from app.aws_mock.sns_client import SNSClient
from app.modules.resume.parser import ResumeParser

class ResumeWorker:
    def __init__(self):
        self.sns = SNSClient()
        self.parser = ResumeParser()
    
    async def start(self):
        # Subscribe to events
        self.sns.subscribe(
            topic="resume-upload",
            callback=self.process_resume
        )
    
    async def process_resume(self, message):
        resume_id = message["resume_id"]
        file_path = message["file_path"]
        
        # Parse resume
        parsed_data = self.parser.parse(file_path)
        
        # Update database
        self.repo.update_resume(resume_id, parsed_data)
```

---

## 🧪 Testing Backend

### Unit Test Example

```python
# tests/test_auth.py
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.models import User

@pytest.fixture
def test_user(db):
    user = User(
        email="test@example.com",
        password_hash="hashed_password",
        first_name="Test",
        last_name="User",
        role="CANDIDATE"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def test_login_success(client, test_user):
    response = client.post(
        "/api/auth/login",
        json={
            "email": "test@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_invalid_email(client):
    response = client.post(
        "/api/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 401
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_auth.py

# Run with coverage
pytest --cov=app tests/

# Run with verbose output
pytest -v

# Run specific test
pytest tests/test_auth.py::test_login_success
```

---

## 🛠️ Common Development Tasks

### Adding a New Endpoint

1. **Define schema** (schemas.py):
```python
class NewResourceCreate(BaseModel):
    name: str
    description: str
```

2. **Create repository method** (repository.py):
```python
def create_resource(self, data: NewResourceCreate):
    resource = NewResource(**data.dict())
    self.db.add(resource)
    self.db.commit()
    return resource
```

3. **Add service method** (service.py):
```python
async def create_new_resource(self, data: NewResourceCreate, user_id: UUID):
    resource = self.repo.create_resource(data)
    await log_audit("resource_created", resource.id, user_id)
    return resource
```

4. **Add endpoint** (router.py):
```python
@router.post("/resources", status_code=201)
async def create_resource(
    data: NewResourceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    repo = NewResourceRepository(db)
    service = NewResourceService(repo)
    resource = await service.create_new_resource(data, current_user.id)
    return ResourceResponse.from_orm(resource)
```

---

### Adding a New Database Model

1. **Define model** (core/models.py):
```python
class NewResource(Base):
    __tablename__ = "new_resources"
    
    id = Column(UUID, primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

2. **Reinitialize database**:
```bash
# Development only
python -c "from app.core.database import init_db; init_db()"
```

---

## 🔍 Debugging

### Enable SQL Query Logging

```python
# At app startup or in config
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

### Debug Print Statements

```python
# Use logger instead of print
import logging
logger = logging.getLogger(__name__)

logger.debug(f"User data: {user}")
logger.info(f"Processing resume: {resume_id}")
logger.warning(f"Unusual activity: {event}")
logger.error(f"Critical error: {error}")
```

### Interactive Debugger

```python
# Use breakpoint (Python 3.7+)
async def debug_function():
    data = await fetch_data()
    breakpoint()  # Execution pauses here
    process(data)

# Run with: python -m pdb app/main.py
# Or: uvicorn app.main:app --reload
```

---

## 📖 API Documentation

FastAPI automatically generates docs:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

Add docstrings to endpoints:

```python
@router.get("/users/{user_id}")
async def get_user(user_id: UUID):
    """
    Get user by ID.
    
    - **user_id**: Unique user identifier (UUID)
    
    Returns:
    - **id**: User ID
    - **email**: User email address
    - **role**: User role (CANDIDATE or RECRUITER)
    """
    pass
```

---

## 📝 Code Style & Best Practices

### Naming Conventions
- Classes: PascalCase (`UserService`)
- Functions: snake_case (`create_user`)
- Constants: UPPER_SNAKE_CASE (`MAX_FILE_SIZE`)
- Private attributes: `_prefix` (`_internal_state`)

### Import Organization
```python
# 1. Standard library
import os
from datetime import datetime
from typing import List, Optional

# 2. Third-party packages
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

# 3. Local imports
from app.core.models import User
from app.utils.auth_utils import get_current_user
```

### Error Handling
```python
try:
    result = await risky_operation()
except SpecificException as e:
    logger.error(f"Expected error: {e}")
    raise CustomException(f"Failed to process: {e}")
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise InternalServerError("An unexpected error occurred")
```

---

## 🔗 Integration with Frontend

The frontend calls backend via HTTP:

```javascript
// Frontend makes request
const response = await fetch('http://localhost:8000/api/users/123', {
  headers: {
    'Authorization': 'Bearer token...'
  }
});

// Backend must handle CORS
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"])
```

---

**Happy coding! 🚀**
