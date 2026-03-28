# Recruitment Platform - Quick Start Guide

## 🚀 5-Minute Quick Start

### Step 1: Prerequisites
- Python 3.11+ installed
- Node.js 18+ installed
- PostgreSQL 14+ installed and running

### Step 2: Run Setup Script

**On macOS/Linux:**
```bash
chmod +x setup.sh
./setup.sh
```

**On Windows:**
```cmd
setup.bat
```

### Step 3: Configure Database

```bash
# Login to PostgreSQL
psql -U postgres

# Create database and user
CREATE USER recruitment_user WITH PASSWORD 'recruitment_pass';
CREATE DATABASE recruitment_db OWNER recruitment_user;
GRANT ALL PRIVILEGES ON DATABASE recruitment_db TO recruitment_user;

\q
```

Update `backend/.env`:
```
DATABASE_URL=postgresql://recruitment_user:recruitment_pass@localhost:5432/recruitment_db
```

### Step 4: Run the Application

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
python -m uvicorn app.main:app --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### Step 5: Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Swagger Docs**: http://localhost:8000/docs

---

## 🧪 Test Account

Use these credentials to test:

**Candidate Account:**
- Email: `candidate@example.com`
- Password: `password123`

**Recruiter Account:**
- Email: `recruiter@example.com`
- Password: `password123`

---

## 📱 Key Features to Try

### For Candidates:
1. **Register** as a Candidate
2. **Upload Resume** (PDF or DOCX format)
3. **Add Experience** and **Education**
4. **View Profile** with parsed resume data
5. **Upgrade to PRO** for better visibility

### For Recruiters:
1. **Register** as a Recruiter
2. **Search Candidates** by skills, experience, keywords
3. **View Candidate Profiles** (requires PRO)
4. **Send Email** to candidates (requires PRO, mock logs to file)
5. **Upgrade to PRO** for full features

---

## 🔧 Using the API

### Get Authentication Token

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "candidate@example.com",
    "password": "password123"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "candidate@example.com",
    "role": "CANDIDATE",
    "subscription_type": "BASIC"
  }
}
```

### Use Token for API Calls

```bash
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <your_access_token>"
```

---

## 📂 Project Structure

```
recruitment/
├── backend/               # FastAPI backend
│   ├── app/
│   │   ├── modules/      # Feature modules
│   │   ├── core/         # Core config, db, security
│   │   ├── middleware/   # Request middleware
│   │   ├── aws_mock/     # AWS service mocks
│   │   └── workers/      # Background workers
│   ├── tests/            # Unit tests
│   ├── requirements.txt  # Dependencies
│   ├── .env.example      # Example env file
│   └── Dockerfile
│
├── frontend/              # React frontend
│   ├── src/
│   │   ├── pages/        # Page components
│   │   ├── components/   # Reusable components
│   │   ├── services/     # API services
│   │   ├── context/      # React context
│   │   └── App.jsx       # Main app component
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile
│
├── docker-compose.yml     # Docker setup
├── README.md              # Full documentation
└── setup.sh/setup.bat    # Setup script
```

---

## 🐛 Troubleshooting

### Backend won't start
```
Error: "Cannot connect to database"
Solution: Check DATABASE_URL in .env matches your PostgreSQL setup
```

### Frontend shows blank page
```
Error: API not responding
Solution: Ensure backend is running on port 8000
Check VITE_API_URL in frontend/.env
```

### Resume upload fails
```
Error: "Only PDF and DOCX files are supported"
Solution: Upload a valid PDF or DOCX file
Check storage/resumes folder exists
```

---

## 📚 Next Steps

1. **Explore API Documentation**: http://localhost:8000/docs
2. **Check Database Schema**: See `app/core/models.py`
3. **Review Feature Modules**: Each module in `app/modules/`
4. **Run Tests**: `pytest tests/ -v` in backend directory
5. **Deploy with Docker**: `docker-compose up`

---

## 🚀 Deploy with Docker

```bash
docker-compose up
```

Access via:
- Frontend: http://localhost:5173
- Backend: http://localhost:8000

---

**Happy recruiting! 🎯**
