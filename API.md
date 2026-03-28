# API Reference

## Base URL
```
http://localhost:8000/api
```

## Authentication
All endpoints (except `/auth/register` and `/auth/login`) require JWT authentication:

```
Authorization: Bearer <access_token>
```

---

## Auth Endpoints

### Register New User
```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123",
  "first_name": "John",
  "last_name": "Doe",
  "role": "CANDIDATE"  // or "RECRUITER"
}
```

**Response (201):**
```json
{
  "message": "User registered successfully",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "CANDIDATE",
    "subscription_type": "BASIC",
    "is_active": true,
    "created_at": "2024-01-15T10:30:00"
  }
}
```

---

### Login
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "role": "CANDIDATE",
    "subscription_type": "BASIC",
    "is_active": true,
    "created_at": "2024-01-15T10:30:00"
  }
}
```

---

### Get Current User
```http
GET /auth/me
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "role": "CANDIDATE",
  "subscription_type": "BASIC",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00"
}
```

---

### Change Password
```http
POST /auth/change-password
Authorization: Bearer <token>
Content-Type: application/json

{
  "old_password": "currentpassword",
  "new_password": "newpassword123"
}
```

**Response (200):**
```json
{
  "message": "Password changed successfully",
  "user": {...}
}
```

---

## Candidate Endpoints

### Get Candidate Profile
```http
GET /candidates/me
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "id": "uuid",
  "email": "candidate@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "role": "CANDIDATE",
  "subscription_type": "BASIC",
  "created_at": "2024-01-15T10:30:00",
  "resumes": [...],
  "skills": [...],
  "experiences": [...],
  "educations": [...]
}
```

---

### Add Experience
```http
POST /candidates/experience
Authorization: Bearer <token>
Content-Type: application/json

{
  "job_title": "Senior Software Engineer",
  "company_name": "Tech Company",
  "location": "San Francisco, CA",
  "description": "Led backend development team",
  "start_date": "2020-01-01T00:00:00",
  "end_date": "2023-12-31T00:00:00",
  "is_current": false
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "job_title": "Senior Software Engineer",
  "company_name": "Tech Company",
  "location": "San Francisco, CA",
  "description": "Led backend development team",
  "start_date": "2020-01-01T00:00:00",
  "end_date": "2023-12-31T00:00:00",
  "is_current": false,
  "years": 4,
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00"
}
```

---

### Update Experience
```http
PUT /candidates/experience/{experience_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "job_title": "Tech Lead",
  "company_name": "Tech Company"
}
```

---

### Delete Experience
```http
DELETE /candidates/experience/{experience_id}
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "message": "Experience deleted successfully"
}
```

---

### Add Education
```http
POST /candidates/education
Authorization: Bearer <token>
Content-Type: application/json

{
  "institution": "Stanford University",
  "degree": "Bachelor of Science",
  "field_of_study": "Computer Science",
  "start_date": "2016-09-01T00:00:00",
  "end_date": "2020-05-31T00:00:00",
  "description": "Graduated with honors"
}
```

---

### Update Education
```http
PUT /candidates/education/{education_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "degree": "Master of Science"
}
```

---

### Delete Education
```http
DELETE /candidates/education/{education_id}
Authorization: Bearer <token>
```

---

## Resume Endpoints

### Upload Resume
```http
POST /resumes/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <PDF or DOCX file>
```

**Response (201):**
```json
{
  "id": "uuid",
  "file_name": "resume.pdf",
  "file_type": "pdf",
  "status": "UPLOADED",
  "message": "Resume uploaded successfully. Processing started."
}
```

---

### List Resumes
```http
GET /resumes/list
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "resumes": [
    {
      "id": "uuid",
      "file_name": "resume.pdf",
      "file_type": "pdf",
      "status": "PARSED",
      "created_at": "2024-01-15T10:30:00",
      "parsed_data": {
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "+1234567890",
        "skills": ["Python", "React", "PostgreSQL"],
        "experiences": [...],
        "educations": [...]
      }
    }
  ]
}
```

---

### Get Resume Details
```http
GET /resumes/{resume_id}
Authorization: Bearer <token>
```

---

### Delete Resume
```http
DELETE /resumes/{resume_id}
Authorization: Bearer <token>
```

---

## Recruiter Endpoints

### Search Candidates
```http
GET /recruiters/search?skills=Python,React&keyword=engineer&min_experience=2&max_experience=5&limit=20&offset=0
Authorization: Bearer <token>
```

**Query Parameters:**
- `skills` (optional): Comma-separated skill names
- `keyword` (optional): Search in name, email, education
- `min_experience` (optional): Minimum years of experience
- `max_experience` (optional): Maximum years of experience
- `limit` (optional): Max results per page (default: 20, max: 100)
- `offset` (optional): Pagination offset (default: 0)

**Response (200):**
```json
{
  "candidates": [
    {
      "id": "uuid",
      "email": "candidate@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "skills": [
        {"id": "uuid", "name": "Python"},
        {"id": "uuid", "name": "React"}
      ],
      "created_at": "2024-01-15T10:30:00"
    }
  ],
  "total": 150,
  "limit": 20,
  "offset": 0
}
```

---

### Get Candidate Profile (PRO Required)
```http
GET /recruiters/candidate/{candidate_id}
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "id": "uuid",
  "email": "candidate@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "role": "CANDIDATE",
  "subscription_type": "BASIC",
  "created_at": "2024-01-15T10:30:00",
  "resumes": [
    {
      "id": "uuid",
      "file_name": "resume.pdf",
      "status": "PARSED",
      "parsed_data": {...}
    }
  ],
  "experiences": [...],
  "skills": [...]
}
```

---

### Send Email to Candidate (PRO Required)
```http
POST /recruiters/send-email
Authorization: Bearer <token>
Content-Type: application/json

{
  "candidate_id": "uuid",
  "subject": "Great opportunity for you!",
  "body": "We have an exciting opportunity that matches your profile..."
}
```

**Response (200):**
```json
{
  "message": "Email sent successfully",
  "email_id": "email-12345",
  "recipient": "candidate@example.com"
}
```

---

## Subscription Endpoints

### Upgrade Subscription
```http
POST /subscription/upgrade
Authorization: Bearer <token>
Content-Type: application/json

{
  "subscription_type": "PRO",
  "payment_method": "credit_card"
}
```

**Response (200):**
```json
{
  "user_id": "uuid",
  "subscription_type": "PRO",
  "message": "Subscription upgraded to PRO"
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "email",
      "error": "Not a valid email address"
    }
  }
}
```

### 401 Unauthorized
```json
{
  "error": {
    "code": "AUTHENTICATION_ERROR",
    "message": "Invalid email or password"
  }
}
```

### 403 Forbidden
```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "This feature requires PRO subscription"
  }
}
```

### 404 Not Found
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Candidate not found: uuid",
    "details": {
      "resource": "Candidate",
      "identifier": "uuid"
    }
  }
}
```

### 409 Conflict
```json
{
  "error": {
    "code": "CONFLICT",
    "message": "Email already registered"
  }
}
```

### 422 Unprocessable Entity
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Only PDF and DOCX files are supported"
  }
}
```

### 500 Internal Server Error
```json
{
  "error": {
    "code": "INTERNAL_SERVER_ERROR",
    "message": "An unexpected error occurred"
  }
}
```

---

## Rate Limiting
Currently not implemented. Can be added with:
- `slowapi` library
- Redis backend

---

## Pagination
List endpoints support pagination with:
- `limit`: Max items per page (default: 20, max: 100)
- `offset`: Number of items to skip (default: 0)

---

**Last Updated: January 2024**
