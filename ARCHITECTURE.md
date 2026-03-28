# Architecture & Design Decisions

## 🏗️ System Architecture

### Clean Architecture Principles Applied

This recruitment platform follows **clean architecture** with **feature-based modular design**:

```
┌─────────────────────────────────────────────┐
│         Presentation Layer (React)          │
│    Components | Pages | Context | Hooks    │
└────────────┬──────────────────────────────┘
             │
┌────────────▼──────────────────────────────┐
│         API Services Layer                 │
│    authService | candidateService | etc   │
└────────────┬──────────────────────────────┘
             │
┌────────────▼──────────────────────────────┐
│         FastAPI Application                │
│  (Backend business logic + routing)        │
└────────────┬──────────────────────────────┘
             │
┌────────────▼──────────────────────────────┐
│         Feature Modules Layer              │
│  auth | candidate | recruiter | resume    │
└────────────┬──────────────────────────────┘
             │
┌────────────▼──────────────────────────────┐
│         Domain Layer (Repositories)        │
│  Database queries & business logic         │
└────────────┬──────────────────────────────┘
             │
┌────────────▼──────────────────────────────┐
│         Persistence Layer                  │
│  SQLAlchemy ORM & PostgreSQL Database      │
└─────────────────────────────────────────────┘
```

### Module Structure (Feature-Based)

Each feature module follows this pattern:

```
module/
├── __init__.py        # Package init
├── models.py          # Database models (in core/models.py for this project)
├── schemas.py         # Pydantic request/response schemas
├── repository.py      # Data access layer
├── service.py         # Business logic
└── router.py          # API endpoints & routing
```

**Advantages:**
- Easy to locate code for a feature
- Isolated, testable components
- Can be developed independently
- Clear separation of concerns
- Easy to scale and add new features

---

## 🔐 Authentication Flow

```
User Input (Web)
       ↓
[LoginPage] → authService.login()
       ↓
[JWT Token Generated] ← AuthService (backend)
       ↓
[Token Stored (localStorage)] 
       ↓
[AuthContext Updated]
       ↓
[Subsequent Requests] → Authorization: Bearer <token>
       ↓
[JWT Verified] ← AuthService (backend)
       ↓
[Protected Endpoint Accessed]
```

### Token Flow:
1. User logs in with email/password
2. Backend validates credentials
3. Backend generates JWT token
4. Frontend stores token in localStorage
5. Frontend includes token in Authorization header for all requests
6. Backend validates token and returns user

---

## 📤 Resume Processing Pipeline

```
┌─────────────────────────────────────────────┐
│  1. Frontend Upload                         │
│     User selects PDF/DOCX file              │
└────────────┬────────────────────────────────┘
             │
┌────────────▼────────────────────────────────┐
│  2. Backend Receives File                   │
│     Validates file type & size              │
└────────────┬────────────────────────────────┘
             │
┌────────────▼────────────────────────────────┐
│  3. Store in S3 (Mock)                      │
│     Generates unique key                    │
└────────────┬────────────────────────────────┘
             │
┌────────────▼────────────────────────────────┐
│  4. Publish SNS Event                       │
│     Sends to resume-upload topic            │
└────────────┬────────────────────────────────┘
             │
┌────────────▼────────────────────────────────┐
│  5. Background Worker Processes             │
│     ResumeWorker listens for event          │
└────────────┬────────────────────────────────┘
             │
┌────────────▼────────────────────────────────┐
│  6. Parse Resume                            │
│     Extract: name, email, skills, exp, edu  │
└────────────┬────────────────────────────────┘
             │
┌────────────▼────────────────────────────────┐
│  7. Update Database                         │
│     Store parsed data with status=PARSED    │
└─────────────────────────────────────────────┘
```

### Event-Driven Benefits:
- Asynchronous processing
- Scalable to multiple workers
- Decoupled components
- Can add additional processing steps

---

## 🔍 Search Architecture

### Database Query Optimization

```python
# Optimized search with joins and indexes
search_candidates(
  skills: List[UUID],           # Uses index on skills.id
  min_years: int,               # Uses index on experiences.years
  max_years: int,
  keyword: str,                 # Uses index on users.email
  degree: str                   # Uses index on educations.degree
)
```

**Query Strategy:**
1. Start with users table (base)
2. LEFT JOIN candidate_skills for skill filtering
3. LEFT JOIN experiences for experience filtering
4. LEFT JOIN educations for education filtering
5. Apply WHERE clauses with indexed columns
6. Use DISTINCT to avoid duplicates
7. Apply LIMIT and OFFSET for pagination

**Indexes Created:**
- `users.email` - Fast email lookups
- `skills.name` - Skill searches
- `experiences.years` - Experience filtering
- `educations.degree` - Education filtering
- `candidate_skills.candidate_id` - Relationship lookups

---

## 🔐 Authorization Model

### Role-Based Access Control (RBAC)

```
User Roles:
├── CANDIDATE
│   ├── Can view own profile
│   ├── Can upload resume
│   ├── Can manage own experiences/education
│   ├── Can view recruiter messages (if PRO)
│   └── Can apply to jobs
│
└── RECRUITER
    ├── Can search candidates (BASIC)
    ├── Can view candidate profiles (PRO only)
    ├── Can send emails (PRO only)
    ├── Can view analytics (PRO)
    └── Can manage job postings
```

### Subscription-Based Features

```
BASIC Subscription:
├── View candidate directory
├── Search candidates
├── View limited profile info
└── 1 resume upload

PRO Subscription:
├── All BASIC features +
├── View detailed candidate profiles
├── Send unlimited emails
├── Email templates
├── Advanced analytics
├── Priority in recruiter search results
├── Contact information access
└── Unlimited resume uploads
```

---

## 🗄️ Database Design

### Single Users Table Strategy

**Why single users table:**
- Simpler queries
- Unified authentication
- Role column determines behavior
- Candidate-specific fields in separate tables

**Candidate-Specific Data:**
- resumes → Resume.candidate_id
- experiences → Experience.candidate_id
- educations → Education.candidate_id
- skills (M2M) → CandidateSkill.candidate_id

**Audit Columns on All Tables:**
- `created_at` - Record creation time
- `updated_at` - Last modification time
- `created_by` - User who created
- `updated_by` - User who last modified

### Relationships

```
users
├─ 1:Many → resumes
├─ 1:Many → experiences
├─ 1:Many → educations
├─ Many:Many → skills (through candidate_skills)
├─ 1:Many → emails_sent (from)
└─ 1:Many → audit_logs

skills
├─ Many:Many → users (through candidate_skills)
└─ 1:Many → candidate_skills

audit_logs
└─ Many:1 → users
```

---

## 🔄 Data Flow Examples

### Example 1: Resume Upload and Parsing

```python
# Frontend sends:
POST /api/resumes/upload {
  file: File (multipart)
}

# Backend:
1. Validate file type (PDF/DOCX)
2. Generate unique filename
3. Upload to S3 mock (storage/resumes/) ✅
4. Create Resume record in DB (status=UPLOADED)
5. Publish SNS event
6. Return response immediately (async processing)

# Background Worker:
1. Receive SNS event
2. Download file from S3
3. Parse with PyPDF2/python-docx
4. Extract: skills, experiences, educations
5. Update Resume record (status=PARSED, parsed_data={...})
6. Can now use parsed data for search indexing
```

### Example 2: Recruiter Searches and Contacts Candidate

```javascript
// Frontend:
1. Recruiter enters search criteria
2. Call recruiterService.searchCandidates()
3. Display results with skill badges
4. Click "View Profile" (requires PRO)

// Backend:
1. Search with filters (pre-built query)
2. Join with experiences, educations, skills
3. Apply WHERE conditions
4. Return paginated results with candidate data

// Recruiter sends email:
1. Click "Send Email" on candidate
2. Fill subject and body
3. Call recruiterService.sendEmail()

// Backend:
1. Verify recruiter has PRO subscription
2. Verify candidate exists
3. Call SES mock client
4. Log email to file
5. Store EmailSent record in DB
6. Return confirmation
```

---

## 🔧 AWS Mocks - Switch to Real Services

### S3 (File Storage)

**Mock → Real Migration:**

```python
# Mock (Current)
from app.aws_mock.s3_client import S3Client
# Stores files in ./storage/resumes

# Real AWS
import boto3
s3_client = boto3.client('s3', region_name='us-east-1')
# Stores files in AWS S3 bucket
```

### SNS (Pub/Sub)

**Mock → Real Migration:**

```python
# Mock (Current)
sns = SNSClient()
await sns.publish(topic='resume-upload', message={...})
# In-memory subscriptions

# Real AWS
sns = boto3.client('sns', region_name='us-east-1')
response = sns.publish(
    TopicArn='arn:aws:sns:region:account:topic',
    Message=json.dumps({...})
)
```

### SES (Email)

**Mock → Real Migration:**

```python
# Mock (Current)
ses = SESClient()
await ses.send_email(to_addresses=[...], subject='...', body='...')
# Logs to file

# Real AWS
client = boto3.client('ses', region_name='us-east-1')
response = client.send_email(
    Source='noreply@company.com',
    Destination={'ToAddresses': [...]},
    Message={...}
)
```

**Configuration needed for real AWS:**
1. AWS credentials (IAM user or role)
2. Verified email addresses in SES
3. Associated S3 bucket
4. SNS topics created
5. Update `AWS_MOCK_ENABLED = False` in `.env`

---

## 🧪 Testing Strategy

### Unit Tests
- Service layer business logic
- Repository queries
- Security functions (password hashing, tokens)

### Integration Tests
- API endpoints
- Database interactions
- Authentication flow

### E2E Tests (Future)
- User workflows
- Multi-step processes
- Frontend interaction

### Test Coverage Targets
- Services: 80%+
- Repositories: 70%+
- Utils: 90%+

---

## 📊 Performance Optimizations

### Database Level
- Indexes on frequently searched columns
- Batch queries where possible
- Select only needed columns

### Application Level
- JWT tokens reduce DB queries
- Pagination on list endpoints
- Caching of skill lists (future)
- Redis for session management (future)

### Frontend Level
- React Query for data fetching
- Component memoization
- Lazy loading of pages
- Image optimization

---

## 🔐 Security Measures

### Authentication
- JWT tokens with expiration
- Role-based access control
- Subscription-based authorization

### Data Protection
- Password hashing with bcrypt
- CORS configuration
- Input validation (Pydantic)
- SQL injection prevention (SQLAlchemy ORM)

### Audit Trail
- All important actions logged
- Audit columns on tables
- Tracking user modifications

---

## 🚀 Scalability Considerations

### Horizontal Scaling
- Stateless backend (can run multiple instances)
- Load balancer distribution
- Database read replicas (future)

### Vertical Scaling
- Database indexes for faster queries
- Connection pooling
- Caching layer (Redis)

### Asynchronous Processing
- Event-driven architecture ready
- Background workers for resume parsing
- Can extend with more workers

---

## 📈 Growth Path

### Phase 1 (Current)
- MVP with core features
- Local testing with mocks
- Basic search and filtering

### Phase 2
- Real AWS integration
- Database read replicas
- Redis caching
- Email notifications

### Phase 3
- Mobile app
- Advanced NLP for resume parsing
- ML-based candidate matching
- Notification system

### Phase 4
- AI-powered recommendations
- Video interviewing
- Applicant tracking system
- Employer branding tools

---

## 🔗 External References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8949)
- [AWS Lambda for Resume Processing](https://docs.aws.amazon.com/lambda/)

---

**Built with production-grade architecture and best practices.** ✨
