# Admin-Controlled Subscription Management System

## Overview
This system implements admin-only subscription management for recruiters. Recruiters can no longer self-upgrade to PRO—only admins can assign subscription levels to recruiters.

## Key Changes

### 1. **New ADMIN Role** (`app/core/models.py`)
- Added `ADMIN` role to `UserRole` enum
- Three user roles now: `ADMIN`, `RECRUITER`, `CANDIDATE`

### 2. **Authentication Helper** (`app/utils/auth_utils.py`)
- Added `require_admin()` dependency to protect admin-only endpoints
- Only users with `role = "ADMIN"` can access protected endpoints

### 3. **Subscription Service** (`app/modules/subscription/service.py`)
- **New method**: `admin_set_recruiter_subscription(admin_id, recruiter_id, subscription_type)`
  - Sets BASIC or PRO subscription for a recruiter
  - Only callable by admins
  - Logs audit trail with admin who made the change
  
- **New method**: `admin_get_all_recruiters(limit, offset)`
  - Lists all recruiters with pagination
  - Admin-only access

### 4. **Subscription Repository** (`app/modules/subscription/repository.py`)
- `get_recruiter_by_id(recruiter_id)` - Fetch recruiter details
- `set_recruiter_subscription(recruiter_id, subscription_type, admin_id)` - Assign subscription
- `get_all_recruiters(limit, offset)` - List all recruiters

### 5. **Recruiter Admin Router** (`app/modules/recruiter/admin_router.py`)
New admin endpoints:
- `GET /api/admin/recruiters` - List all recruiters with pagination
- `GET /api/admin/recruiters/{recruiter_id}` - Get detailed recruiter info
- `POST /api/admin/recruiters/{recruiter_id}/deactivate` - Deactivate recruiter
- `POST /api/admin/recruiters/{recruiter_id}/activate` - Activate recruiter

### 6. **Subscription Admin Endpoints** (`app/modules/subscription/router.py`)
New subscription endpoints:
- `GET /api/subscription/admin/recruiters` - List all recruiters (pagination)
- `POST /api/subscription/admin/recruiters/{recruiter_id}/subscription` - Assign subscription

### 7. **Recruiter Service** (`app/modules/recruiter/service.py`)
New admin methods:
- `admin_get_all_recruiters(limit, offset)` - Fetch all recruiters
- `admin_get_recruiter_details(recruiter_id)` - Get detailed recruiter info
- `admin_deactivate_recruiter(recruiter_id)` - Deactivate account
- `admin_activate_recruiter(recruiter_id)` - Activate account

### 8. **Recruiter Repository** (`app/modules/recruiter/repository.py`)
New admin methods:
- `get_all_recruiters(limit, offset)` - List recruiters with pagination
- `get_recruiter_by_id(recruiter_id)` - Get recruiter by ID
- `deactivate_recruiter(recruiter_id)` - Deactivate recruiter
- `activate_recruiter(recruiter_id)` - Activate recruiter

## API Endpoints

### Admin Subscription Management

#### List All Recruiters
```
GET /api/subscription/admin/recruiters?limit=20&offset=0
Authorization: Bearer <admin_token>

Response:
{
  "recruiters": [
    {
      "id": "uuid",
      "email": "recruiter@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "subscription_type": "BASIC",
      "is_active": true,
      "created_at": "2025-01-01T00:00:00"
    }
  ],
  "total": 50,
  "limit": 20,
  "offset": 0
}
```

#### Set Recruiter Subscription
```
POST /api/subscription/admin/recruiters/{recruiter_id}/subscription
Authorization: Bearer <admin_token>

Request:
{
  "subscription_type": "PRO"
}

Response:
{
  "recruiter_id": "uuid",
  "subscription_type": "PRO",
  "message": "Recruiter subscription set to PRO"
}
```

### Admin Recruiter Management

#### List All Recruiters (Alternative)
```
GET /api/admin/recruiters?limit=20&offset=0
Authorization: Bearer <admin_token>
```

#### Get Recruiter Details
```
GET /api/admin/recruiters/{recruiter_id}
Authorization: Bearer <admin_token>

Response:
{
  "id": "uuid",
  "email": "recruiter@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "subscription_type": "BASIC",
  "is_active": true,
  "created_at": "2025-01-01T00:00:00",
  "updated_at": "2025-01-01T00:00:00",
  "created_by": "admin_email",
  "updated_by": "admin_email"
}
```

#### Deactivate Recruiter
```
POST /api/admin/recruiters/{recruiter_id}/deactivate
Authorization: Bearer <admin_token>

Response:
{
  "message": "Recruiter deactivated successfully",
  "recruiter_id": "uuid",
  "is_active": false
}
```

#### Activate Recruiter
```
POST /api/admin/recruiters/{recruiter_id}/activate
Authorization: Bearer <admin_token>

Response:
{
  "message": "Recruiter activated successfully",
  "recruiter_id": "uuid",
  "is_active": true
}
```

## Security

1. **All admin endpoints require ADMIN role**
   - Non-admin users get 403 Forbidden
   
2. **Audit Logging**
   - All subscription changes are logged with admin ID
   - All recruiter status changes are logged
   
3. **Role-Based Access Control**
   - Recruiters cannot self-upgrade
   - Only admins can modify recruiter subscriptions
   - Admins can manage recruiter accounts (activate/deactivate)

## What's Removed

- Self-service subscription upgrade capability for recruiters
- Users can no longer call `POST /api/subscription/upgrade` to change their own subscription

## Migration Notes

1. **Existing Recruiters**: Keep their current subscription level
2. **New Recruitment Button**: Add subscription assignment to admin dashboard
3. **Admin Registration**: Create initial admin account via database seed or API

## Example Usage

```python
# Admin assigns PRO to recruiter
admin_id = "admin-uuid"
recruiter_id = "recruiter-uuid"

response = await client.post(
    "/api/subscription/admin/recruiters/{recruiter_id}/subscription",
    json={"subscription_type": "PRO"},
    headers={"Authorization": f"Bearer {admin_token}"}
)
```

## Frontend Changes Needed

1. Remove self-upgrade button from recruiter dashboard
2. Add admin subscription management UI:
   - List all recruiters
   - Show current subscription status
   - Dropdown to select BASIC or PRO
   - Button to apply changes
3. Add recruiter status management (activate/deactivate)
