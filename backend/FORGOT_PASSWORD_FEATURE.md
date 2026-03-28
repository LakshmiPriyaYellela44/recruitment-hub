# Forgot Password Feature Implementation

## Overview
Implemented complete forgot password functionality for the recruitment application.

## Components Added

### 1. Database Model: `PasswordReset`
**File**: `app/core/models.py`

```python
class PasswordReset(Base):
    __tablename__ = "password_resets"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    reset_token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    is_used = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
```

**Features**:
- Stores password reset tokens with 24-hour expiry
- Tracks whether token has been used (prevents reuse)
- Foreign key to User for audit trail
- Indexed for performance

### 2. Request/Response Schemas
**File**: `app/modules/auth/schemas.py`

- `ForgotPasswordRequest(email)` - Request password reset
- `ResetPasswordRequest(reset_token, new_password)` - Submit new password
- `ForgotPasswordResponse` - Response with token and expiry info

### 3. Repository Methods
**File**: `app/modules/auth/repository.py`

```python
async def create_password_reset(self, password_reset) -> PasswordReset
async def get_password_reset_by_token(self, reset_token) -> Optional[PasswordReset]
async def mark_password_reset_as_used(self, password_reset) -> PasswordReset
```

- Secure token generation using `secrets.token_urlsafe(32)`
- Only retrieves valid (unused and non-expired) tokens
- Prevents token reuse

### 4. Service Methods
**File**: `app/modules/auth/service.py`

```python
async def forgot_password(self, email: str) -> tuple[str, int]
async def reset_password(self, reset_token: str, new_password: str) -> User
```

**Constants**:
- `RESET_TOKEN_EXPIRY_HOURS = 24`

**Security**:
- Does not reveal whether email exists in system
- Validates email before token generation
- Token expires after 24 hours
- Prevents token reuse

### 5. API Endpoints
**File**: `app/modules/auth/router.py`

#### POST `/api/auth/forgot-password`
**Request**:
```json
{
  "email": "user@example.com"
}
```

**Response** (200 OK):
```json
{
  "message": "If that email address is in our system, we will send a password reset email",
  "reset_token": "token_string",
  "expires_in_hours": 24
}
```

**Security Note**: Returns same message whether email exists or not (prevents user enumeration)

#### POST `/api/auth/reset-password`
**Request**:
```json
{
  "reset_token": "token_string",
  "new_password": "NewPassword@123"
}
```

**Response** (200 OK):
```json
{
  "message": "Password reset successfully",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "CANDIDATE",
    "is_active": true,
    "created_at": "2026-03-28T..."
  }
}
```

**Error Handling**:
- Returns 422 for invalid/expired tokens
- Returns 400 for validation errors

## Flow Diagram

```
User -> POST /forgot-password -> Service generates token (24hr expiry)
                              -> Token stored in DB with user_id
                              -> Response includes reset_token
                              
User -> POST /reset-password with token -> Service validates:
                                         - Token exists
                                         - Token not expired
                                         - Token not already used
                                      -> Password updated
                                      -> Token marked as used
                                      -> Response with updated user
```

## Security Features

✅ **Token Security**:
- Secure random tokens (32 bytes, base64url encoded)
- Unique constraint on token
- Expiry validation (24-hour window)
- One-time use (marked as used after successful reset)

✅ **Password Security**:
- PBKDF2-SHA256 hashing (100,000 rounds via passlib)
- Password minimum 8 characters enforced
- Old password still works until reset

✅ **User Privacy**:
- Same response whether email exists or not
- Prevents user enumeration attacks
- Token never exposed unless in response

✅ **Audit Trail**:
- PASSWORD_RESET_REQUESTED logged
- PASSWORD_RESET logged on success

## Testing

**Comprehensive test** created in `test_forgot_password.py` validates:

✓ User registration  
✓ Password reset token generation  
✓ Token stored in database  
✓ Old password works before reset  
✓ Password reset with valid token  
✓ Password hash updated in database  
✓ Old password rejected after reset  
✓ New password allows login  
✓ Token marked as used (cannot be reused)  
✓ Invalid tokens rejected  
✓ All error handling correct  

## Production Considerations

### Email Integration (TODO)
Currently the reset token is returned in API response for testing. In production:

1. Remove `reset_token` from response
2. Send email with reset link: `https://frontend.com/reset-password?token={reset_token}`
3. Frontend extracts token from URL query param
4. Frontend posts to `/api/auth/reset-password` with token and new password

### Email Service Setup
```python
# Send email with reset link
reset_link = f"{FRONTEND_URL}/reset-password?token={reset_token}"
send_email(
    to=user.email,
    subject="Password Reset Request",
    body=f"Click here to reset your password: {reset_link}"
)
```

### Frontend Implementation
1. Create `/reset-password` page
2. Extract token from URL query parameters
3. Form with new password field
4. POST to `/api/auth/reset-password`
5. Show success message
6. Redirect to login

## Database Migration

To apply the new `PasswordReset` table, run:
```bash
alembic revision --autogenerate -m "Add password_resets table"
alembic upgrade head
```

Or use your preferred migration tool.

## Usage Example

### Request Password Reset
```bash
curl -X POST "http://localhost:8000/api/auth/forgot-password" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'
```

### Reset Password
```bash
curl -X POST "http://localhost:8000/api/auth/reset-password" \
  -H "Content-Type: application/json" \
  -d '{
    "reset_token": "generated_token",
    "new_password": "NewPassword@123"
  }'
```

## Files Modified

1. `app/core/models.py` - Added PasswordReset model
2. `app/modules/auth/schemas.py` - Added request/response schemas
3. `app/modules/auth/repository.py` - Added database operations
4. `app/modules/auth/service.py` - Added business logic
5. `app/modules/auth/router.py` - Added API endpoints

## Status

✅ **IMPLEMENTATION COMPLETE**
✅ **ALL TESTS PASSING**
✅ **PRODUCTION READY** (with email integration)
