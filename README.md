# 🎯 Recruitment Platform - Production-Grade Full Stack Application

A complete, production-ready recruitment platform built with modern technologies.

## 📋 Features

### Core Features
- ✅ User Authentication (JWT)
- ✅ Candidate Profiles with Resume Upload
- ✅ Resume Parsing (PDF/DOCX)
- ✅ Candidate Search with Advanced Filters
- ✅ Professional Profile Management
- ✅ Subscription System (BASIC/PRO)
- ✅ Email Notifications
- ✅ Audit Logging
- ✅ Event-Driven Architecture

### Subscription Features
- **BASIC**: View candidate profiles, search candidates
- **PRO**: Send emails, detailed analytics, priority visibility

---

## 🏗️ Architecture

### Feature-Based Modular Architecture

```
app/
├── modules/          # Feature modules
│   ├── auth/        # Authentication
│   ├── candidate/   # Candidate profiles
│   ├── recruiter/   # Recruiter operations
│   ├── resume/      # Resume management
│   └── subscription/# Subscription management
├── core/            # Core config, DB, security
├── middleware/      # Request/response middleware
├── aws_mock/        # AWS service mocks
├── workers/         # Background workers
└── utils/           # Common utilities
```

---

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Relational database
- **SQLAlchemy** - ORM
- **JWT** - Token-based authentication
- **PyPDF2 & python-docx** - Resume parsing

### Frontend
- **React 18** - UI framework
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **React Query** - Data fetching
- **React Router** - Routing
- **Axios** - HTTP client

---

## 📦 Installation & Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file and configure
cp .env.example .env

# Edit .env with your database connection string:
nano .env
```

**Important**: Update the `DATABASE_URL` in `.env`:
```
DATABASE_URL=postgresql://your_user:your_password@localhost:5432/recruitment_db
```

### 2. Database Setup

```bash
# Login to PostgreSQL
psql -U postgres

# Create database and user
CREATE USER recruitment_user WITH PASSWORD 'recruitment_pass';
CREATE DATABASE recruitment_db OWNER recruitment_user;
GRANT ALL PRIVILEGES ON DATABASE recruitment_db TO recruitment_user;

\q  # Exit psql
```

### 3. Initialize Database

```bash
# From backend directory
python -c "from app.core.database import init_db; init_db()"
```

### 4. Start Backend Server

```bash
# From backend directory
python -m uvicorn app.main:app --reload --port 8000
```

Backend will run at `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 5. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will run at `http://localhost:5173`

---

## 🔍 API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get token
- `GET /auth/me` - Get current user
- `POST /auth/change-password` - Change password

### Candidate
- `GET /candidates/me` - Get candidate profile
- `POST /candidates/experience` - Add experience
- `PUT /candidates/experience/{id}` - Update experience
- `DELETE /candidates/experience/{id}` - Delete experience
- `POST /candidates/education` - Add education
- `PUT /candidates/education/{id}` - Update education
- `DELETE /candidates/education/{id}` - Delete education

### Resume
- `POST /resumes/upload` - Upload resume (requires file upload)
- `GET /resumes/list` - List all resumes
- `GET /resumes/{id}` - Get resume details
- `DELETE /resumes/{id}` - Delete resume

### Recruiter (PRO only for detailed features)
- `GET /recruiters/search` - Search candidates
  - Query params: `skills`, `keyword`, `min_experience`, `max_experience`
- `GET /recruiters/candidate/{id}` - Get candidate profile (PRO only)
- `POST /recruiters/send-email` - Send email to candidate (PRO only)

### Subscription
- `POST /subscription/upgrade` - Upgrade to PRO

---

## 🔐 Authentication

### Using API with JWT Token

1. **Register/Login to get token**:
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
```

2. **Use token in Authorization header**:
```bash
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <your_access_token>"
```

---

## 📨 Email System

The platform uses a mock SES client for development. Emails are logged to `./logs/emails.log`.

To switch to real AWS SES:

1. Update `app/core/config.py`:
```python
AWS_MOCK_ENABLED = False  # Set to False
```

2. Configure AWS credentials (AWS CLI or environment variables)

3. Update `app/modules/resume/service.py` and `app/modules/recruiter/service.py` to use real SES

---

## ☁️ AWS Service Mocks

All AWS services are mocked for local development:

### S3 (File Storage)
- Mock: Stores files in `./storage/resumes`
- Real: Replace with boto3 S3 client

### SNS (Pub/Sub)
- Mock: In-memory topic subscriptions
- Real: Use boto3 SNS client

### SQS (Message Queue)
- Mock: In-memory queue with deque
- Real: Use boto3 SQS client

### SES (Email)
- Mock: Logs to `./logs/emails.log`
- Real: Use boto3 SES client

To switch to real AWS services:
1. Set `AWS_MOCK_ENABLED = False` in `.env`
2. Configure AWS credentials
3. Update AWS client classes in `app/aws_mock/`

---

## 🧪 Testing

### Run Backend Tests

```bash
cd backend

# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/ -v

# Run specific test
pytest tests/test_auth.py::test_login -v
```

### Test Coverage
- `test_security.py` - Password hashing, JWT tokens
- `test_auth.py` - Registration, login, endpoints

---

## 📤 Deployment

### Using Docker

1. **Backend Dockerfile**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

2. **Frontend Dockerfile**:
```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package.json .
RUN npm install

COPY . .

RUN npm run build

EXPOSE 3000

CMD ["npm", "run", "preview"]
```

3. **Docker Compose**:
```yaml
version: '3.8'
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: recruitment_user
      POSTGRES_PASSWORD: recruitment_pass
      POSTGRES_DB: recruitment_db
    ports:
      - "5432:5432"

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://recruitment_user:recruitment_pass@db:5432/recruitment_db
    depends_on:
      - db

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    depends_on:
      - backend
```

Run with:
```bash
docker-compose up
```

---

## 📊 Database Schema

### Key Tables
- `users` - All users (candidates & recruiters)
- `resumes` - Uploaded resumes
- `skills` - Skill master data
- `candidate_skills` - Candidate-skill relationships
- `experiences` - Work experiences
- `educations` - Education records
- `emails_sent` - Email logs
- `audit_logs` - Audit trail

All tables include audit columns: `created_at`, `updated_at`, `created_by`, `updated_by`

---

## 🔧 Configuration

### Environment Variables

Create `.env` in backend directory:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/recruitment_db

# App
APP_NAME=Recruitment Platform
DEBUG=False

# Security
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AWS
AWS_MOCK_ENABLED=True
AWS_MOCK_STORAGE_PATH=./storage/resumes

# Email
EMAIL_MOCK_ENABLED=True
EMAIL_LOG_PATH=./logs/emails.log

# CORS
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
```

---

## 📈 Performance Considerations

### Database Indexes
- `users.email` - Fast email lookups
- `users.role` - Role-based filtering
- `skills.name` - Skill searches
- `experiences.years` - Experience filtering
- `educations.degree` - Education filtering

### Caching Opportunities
- Cache frequent skill searches
- Cache candidate search results (Redis)
- Cache user profiles

### Query Optimization
- Use `select()` for specific columns
- Batch queries where possible
- Add pagination to list endpoints

---

## 🛡️ Security Features

- ✅ Password hashing with bcrypt
- ✅ JWT token-based authentication
- ✅ Role-based authorization
- ✅ Subscription-based access control
- ✅ CORS middleware
- ✅ Request logging
- ✅ Audit logging
- ✅ Exception handling

---

## 📝 API Documentation

Automated API docs available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## 🐛 Troubleshooting

### Database Connection Error
```
Check DATABASE_URL in .env
Ensure PostgreSQL is running
Verify username/password and database name
```

### Import Errors
```
Reinstall dependencies: pip install -r requirements.txt
Activate virtual environment
```

### Frontend Build Error
```
Clear node_modules: rm -rf node_modules package-lock.json
Reinstall: npm install
```

### Resume Parsing Issues
```
Ensure PyPDF2 and python-docx are installed
Check file format (PDF/DOCX only)
```

---

## 🚀 Next Steps

1. **Add Real AWS Integration**
   - Configure AWS credentials
   - Replace mock clients with real AWS services

2. **Add Caching**
   - Implement Redis for frequently accessed data
   - Cache search results

3. **Add More Tests**
   - E2E tests with Cypress
   - Load testing with Locust

4. **Production Deployment**
   - Deploy to AWS (EC2, RDS, S3)
   - Set up CI/CD pipeline
   - Configure monitoring and logging

---

## 📄 License

MIT License - feel free to use this as a starting point for your recruitment platform.

---

**Built with ❤️ | Production-Ready Recruitment Platform**
