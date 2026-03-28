# Troubleshooting Guide

## 🐛 Common Issues and Solutions

---

## Database Issues

### Issue: "Connection refused" or "Could not connect to server"

**Symptoms:**
- FastAPI won't start
- Error: `ERROR: Could not connect to database`

**Solutions:**

1. **Check PostgreSQL is running:**
```bash
# Windows (check Services)
Get-Service PostgreSQL* | Select-Object Status

# macOS
brew services list | grep postgres

# Linux
sudo systemctl status postgresql
```

2. **Verify connection string:**
```bash
# Should match this format:
# postgresql://username:password@host:port/database
echo $DATABASE_URL
```

3. **Test connection:**
```bash
# Install psql client if needed
psql "postgresql://user:password@localhost:5432/recruitment_db"

# If successful, you'll see the psql prompt
recruitment_db=#
```

4. **Create database if missing:**
```bash
psql -U postgres
CREATE USER recruitment_user WITH PASSWORD 'recruitment_pass';
CREATE DATABASE recruitment_db OWNER recruitment_user;
GRANT ALL PRIVILEGES ON DATABASE recruitment_db TO recruitment_user;
\q
```

---

### Issue: "Table does not exist" or "relation does not exist"

**Symptoms:**
- Error: `ERROR: relation "users" does not exist`
- First API call fails with 500 error

**Solutions:**

1. **Initialize database:**
```bash
cd backend
python -c "from app.core.database import init_db; init_db()"
```

2. **Check migration/initialization ran:**
```bash
psql -U recruitment_db recruitment_db -c "\dt"

# Should show tables like:
# public | users
# public | resumes
# public | skills
```

3. **Full reset (development only):**
```bash
# Drop and recreate database
psql -U postgres
DROP DATABASE recruitment_db;
CREATE DATABASE recruitment_db OWNER recruitment_user;
\q

# Reinitialize
cd backend
python -c "from app.core.database import init_db; init_db()"
```

---

### Issue: "Too many connections" error

**Symptoms:**
- Error after running app for a while
- Error: `FATAL: too many connections`

**Solutions:**

1. **Increase connection limit:**
```bash
# Edit PostgreSQL config
# Windows: C:\Program Files\PostgreSQL\xx\data\postgresql.conf
# macOS: /opt/homebrew/var/postgres/postgresql.conf
# Linux: /etc/postgresql/xx/main/postgresql.conf

# Change max_connections
max_connections = 200

# Restart PostgreSQL
```

2. **Use connection pooling:**

In `backend/app/core/database.py`:
```python
from sqlalchemy.pool import NullPool

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=NullPool,  # Disable connection pooling (for testing)
)

# OR for production, use pgBouncer:
# Install: apt-get install pgbouncer
# Configure /etc/pgbouncer/pgbouncer.ini
```

---

## Backend Issues

### Issue: "ModuleNotFoundError: No module named 'app'"

**Symptoms:**
- Error when running FastAPI
- Error: `ModuleNotFoundError: No module named 'app'`

**Solutions:**

1. **Check working directory:**
```bash
cd backend  # Must be in backend directory
python -m uvicorn app.main:app --reload
```

2. **Verify Python path:**
```bash
# Add backend to Python path
export PYTHONPATH="${PYTHONPATH}:/path/to/backend"

# Or run from parent directory
python -m uvicorn backend.app.main:app --reload
```

3. **Check virtual environment:**
```bash
# Activate virtual environment
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

### Issue: "ImportError: cannot import name 'SQLAlchemy'"

**Symptoms:**
- Error: `ImportError: cannot import name 'SQLAlchemy'`

**Solutions:**

```bash
# Reinstall dependencies
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall

# Check installed packages
pip list | grep -i sqlalchemy

# Should show: SQLAlchemy>=2.0.0
```

---

### Issue: Port 8000 already in use

**Symptoms:**
- Error: `Address already in use`
- Can't start FastAPI server

**Solutions:**

```bash
# Windows - Find and kill process
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux - Find and kill process
lsof -i :8000
kill -9 <PID>

# Or use different port
uvicorn app.main:app --reload --port 8001
```

---

### Issue: "JWT token expired" or "Invalid token"

**Symptoms:**
- 401 responses with "Invalid authentication credentials"
- Token was valid, now suddenly invalid

**Solutions:**

1. **Check JWT_SECRET_KEY:**
```bash
# Must be set in .env
echo $JWT_SECRET_KEY

# If empty or changed, tokens become invalid
# Update .env and use environment variable
```

2. **Verify token format:**
```bash
# Token should be: Bearer <token>
# Check Authorization header
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/auth/me

# Invalid: "Bearer$TOKEN" (missing space)
# Invalid: "$TOKEN" (missing "Bearer ")
```

3. **Check token expiration:**
```python
# In security.py, check TOKEN_EXPIRE_MINUTES
TOKEN_EXPIRE_MINUTES = 24 * 60  # 24 hours

# Increase if needed:
TOKEN_EXPIRE_MINUTES = 7 * 24 * 60  # 7 days
```

---

### Issue: "CORS policy: No 'Access-Control-Allow-Origin' header"

**Symptoms:**
- Frontend can't reach backend
- Error: `Access to XMLHttpRequest blocked by CORS policy`

**Solutions:**

1. **Verify CORS configuration:**

In `backend/app/main.py`:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

2. **Add frontend URL to allowed origins:**
```python
allow_origins=[
    "http://localhost:3000",      # Vite default
    "http://localhost:5173",      # Vite with port
    "http://127.0.0.1:5173",
    "http://localhost:3001",      # If using different port
    # Add production URLs here
]
```

3. **Test CORS with curl:**
```bash
curl -i -X OPTIONS http://localhost:8000/api/auth/login \
  -H "Origin: http://localhost:5173" \
  -H "Access-Control-Request-Method: POST"

# Should see CORS headers in response
```

---

### Issue: Resume upload fails

**Symptoms:**
- Upload button doesn't work
- Error: 422 or 500 on /resumes/upload

**Solutions:**

1. **Check file type:**
```python
# Only PDF and DOCX allowed
# File should be one of:
# - .pdf (application/pdf)
# - .docx (application/vnd.openxmlformats-officedocument.wordprocessingml.document)
# - .doc (application/msword)
```

2. **Check file size:**
```python
# In service.py, check max file size
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# Increase if needed
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
```

3. **Check storage directory:**
```bash
# Verify storage directory exists
mkdir -p storage/resumes

# Check permissions
ls -la storage/

# Should be writable by application user
chmod 755 storage
chmod 755 storage/resumes
```

4. **Check PyPDF2 and python-docx installed:**
```bash
pip install -r requirements.txt

# Should include:
# PyPDF2==3.x.x
# python-docx==0.8.x
```

---

## Frontend Issues

### Issue: "Cannot find module" or "Module not found"

**Symptoms:**
- npm start fails
- Error: `Module not found: Can't resolve '@/services/api'`

**Solutions:**

1. **Install dependencies:**
```bash
cd frontend
npm install
```

2. **Check node_modules:**
```bash
# If corrupted, reinstall
rm -rf node_modules package-lock.json
npm install
```

3. **Check import paths:**
```javascript
// Correct:
import { api } from '../services/api';

// Incorrect:
import { api } from '@services/api';  // Alias not configured
```

---

### Issue: Port 5173 or 3000 already in use

**Symptoms:**
- `Error: Port already in use`
- Can't start frontend dev server

**Solutions:**

```bash
# Kill existing process
# Windows
netstat -ano | findstr :5173
taskkill /PID <PID> /F

# macOS/Linux
lsof -i :5173
kill -9 <PID>

# Or use different port
npm run dev -- --port 3001
```

---

### Issue: "Cannot read property 'access_token' of undefined"

**Symptoms:**
- Error after login
- Frontend can't find token in response

**Solutions:**

1. **Check login response format:**

Should return:
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": {...}
}
```

2. **Verify API response structure:**

In `frontend/src/services/authService.js`:
```javascript
export default {
  login: async (credentials) => {
    const response = await api.post('/auth/login', credentials);
    return response.data;  // Should have access_token
  }
};
```

3. **Check backend login endpoint:**

In `backend/app/modules/auth/router.py`:
```python
@router.post("/login")
async def login(credentials: LoginRequest):
    # Must return: {"access_token": "...", "token_type": "bearer", "user": {...}}
```

---

### Issue: "Unexpected token '<'" in console

**Symptoms:**
- White screen after login
- Console error: `Unexpected token '<' JSON.parse`

**Solutions:**

1. **Check if HTML is being returned instead of JSON:**
   - Usually means 404 or backend error returning HTML error page
   
2. **Verify API URL:**
```javascript
// In .env file
VITE_API_URL=http://localhost:8000/api

// Check in browser console
console.log(import.meta.env.VITE_API_URL)
```

3. **Check backend is running:**
```bash
curl http://localhost:8000/api/health
# Should return JSON, not HTML
```

---

### Issue: Styles not loading (Tailwind not working)

**Symptoms:**
- Page loads but has no styling
- No error in console

**Solutions:**

1. **Check Tailwind CSS installed:**
```bash
npm list tailwindcss

# If missing:
npm install -D tailwindcss postcss autoprefixer
```

2. **Verify tailwind.config.js:**
```javascript
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",  // Include .jsx files!
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

3. **Check index.css:**
```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

4. **Restart dev server:**
```bash
# Vite dev server doesn't always pick up config changes
npm run dev
```

---

### Issue: "Cannot find module react-router-dom"

**Symptoms:**
- Pages not loading
- Error: `Module not found: react-router-dom`

**Solutions:**

```bash
# Install or reinstall react-router-dom
npm install react-router-dom

# If issue persists:
npm install --save react-router-dom@latest
```

---

## API Integration Issues

### Issue: Requests return 401 Unauthorized

**Symptoms:**
- Authenticated requests fail with 401
- Token exists but still not authorized

**Solutions:**

1. **Check token in localStorage:**

In browser console:
```javascript
localStorage.getItem('auth_token')
// Should return token, not null
```

2. **Verify token format in header:**

In `frontend/src/services/api.js`:
```javascript
// Should add: "Authorization": "Bearer <token>"
api.interceptors.request.use(config => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

3. **Check token hasn't expired:**

Tokens expire after 24 hours (configurable). Log in again.

---

### Issue: "Invalid email or password" on login

**Symptoms:**
- Login always fails
- Even correct credentials return 401

**Solutions:**

1. **Verify user registration:**
```bash
# Check if user exists in database
psql -U recruitment_db recruitment_db
SELECT * FROM users WHERE email = 'test@example.com';
```

2. **Create test user:**
```bash
cd backend
python

from app.core.security import get_password_hash
from app.core.database import SessionLocal, init_db
from app.core.models import User

init_db()
db = SessionLocal()

user = User(
    email="test@example.com",
    password_hash=get_password_hash("password123"),
    first_name="Test",
    last_name="User",
    role="CANDIDATE"
)
db.add(user)
db.commit()
```

3. **Test authentication directly:**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
```

---

## Email Issues

### Issue: Emails not sending (or not viewable)

**Symptoms:**
- Send email button works but no email received
- No error message

**Solutions:**

1. **Check if using mock email service:**

In development, emails are logged to `backend/logs/emails.log`

```bash
cat logs/emails.log

# Should show:
# [2024-01-15 10:30:00] Email sent to: candidate@example.com
# Subject: Test email
# Body: ...
```

2. **Enable real AWS SES for production:**

In `backend/.env`:
```
AWS_MOCK_ENABLED=false
AWS_SES_REGION=us-east-1
AWS_ACCESS_KEY_ID=<your-key>
AWS_SECRET_ACCESS_KEY=<your-secret>
```

3. **Verify SES configuration if real AWS:**

```bash
# Check verified email addresses in SES
aws ses list-verified-email-addresses

# If not verified:
aws ses verify-email-identity --email-address sender@example.com
```

---

## Performance Issues

### Issue: Slow page loads or API responses

**Symptoms:**
- Pages take long time to load
- API responses slow (>5 seconds)

**Solutions:**

1. **Check database query performance:**

Add query logging to `backend/app/main.py`:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
sqlalchemy_logger = logging.getLogger('sqlalchemy.engine')
sqlalchemy_logger.setLevel(logging.INFO)
```

2. **Check database indexes:**

```sql
-- List indexes
\d <table_name>

-- Create missing indexes
CREATE INDEX idx_users_email ON users(email);
```

3. **Monitor backend metrics:**

```bash
# View real-time CPU and memory
top -p <backend-process-id>

# Check active database connections
ps aux | grep postgres
```

4. **Frontend optimization:**

- Check Network tab in DevTools for slow API calls
- Look for large responses that could be paginated
- Enable React DevTools Profiler

---

## Docker Issues

### Issue: "Cannot connect to Docker daemon"

**Symptoms:**
- Error: `Cannot connect to Docker daemon at unix:///var/run/docker.sock`

**Solutions:**

```bash
# Make sure Docker is running
docker --version

# On Windows: Start Docker Desktop
# On macOS: brew services start docker
# On Linux: sudo systemctl start docker

# Check docker status
docker ps

# Common permissions issue (Linux):
sudo usermod -aG docker $USER
```

---

### Issue: "Container exits immediately"

**Symptoms:**
- `docker-compose up` shows container stopped
- No error message visible

**Solutions:**

```bash
# View container logs
docker-compose logs backend
docker-compose logs frontend

# Run container in foreground for debugging
docker-compose up backend  # without -d flag

# Check Dockerfile for issues
# Common: wrong working directory, missing dependencies
```

---

## Getting Help

### When stuck, check in this order:

1. **Read the error message carefully** - often explains exact issue
2. **Check relevant logs:**
   - Backend: `logs/app.log` or docker logs
   - Frontend: Browser console (F12)
   - Database: PostgreSQL logs
3. **Review this guide** - check similar issue
4. **Search online** - error message + technology name
5. **Review code** - check configuration files

### Useful debug commands:

```bash
# Backend health check
curl http://localhost:8000/api/health

# Frontend is running
curl http://localhost:5173

# Database is responsive
psql -U recruitment_user -d recruitment_db -c "SELECT 1"

# Check network connectivity
ping localhost
telnet localhost 8000
```

---

**Still stuck? Check the logs! 🔍**
