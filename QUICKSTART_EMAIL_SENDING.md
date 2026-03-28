# Quick Start - Email Sending Feature

## 🚀 Running the System

### Step 1: Start Backend
```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level debug
```

### Step 2: Start Frontend
```bash
cd frontend
npm run dev
# Visit http://localhost:5174
```

## 🧪 Testing

### Quick Test (Python WebSocket)
```bash
cd backend
python test_websocket_email.py
```

### Full Test Suite (E2E)
```bash
python test_e2e_email_complete.py
```

### Playwright Tests
```bash
npm run test:e2e
npm run test:e2e -- --headed  # See what's happening
npm run test:e2e -- --debug   # Step through tests
```

## 📋 Using the Email Feature

### For Recruiters (Frontend)
1. Login as PRO recruit (requires PRO subscription)
2. Search for a candidate
3. Open candidate profile
4. Click "📧 Send Email" button
5. Select email template
6. Fill in required dynamic data:
   - Position
   - Company name
   - Interview date
   - Interview time
   - Location
7. Review recipient info
8. Click "Send Email"
9. Wait for success message (5-30 seconds)

### For Developers (Backend)

**Email Templates:**
- Located in database `EmailTemplate` table
- Must have `placeholders` field (JSON array)
- Each placeholder becomes a required form field

**Example Template:**
```python
{
    "name": "Interview Invitation",
    "subject": "Interview Opportunity at {company_name}",
    "body": """
        Dear Candidate,
        
        We're excited to invite you for an interview for the {position} role at {company_name}.
        
        Interview Details:
        Date: {interview_date}
        Time: {interview_time}
        Location: {location}
        
        Best regards,
        Your Recruitment Team
    """,
    "placeholders": ["position", "company_name", "interview_date", "interview_time", "location"]
}
```

## 🔧 Configuration

### Environment Variables
```bash
# Backend (.env or environment)
JWT_SECRET=your-secret-key
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_REGION=us-east-1
SES_SENDER_EMAIL=no-reply@yourcompany.com

# Frontend (.env)
VITE_API_URL=http://localhost:8000/api
VITE_WS_URL=ws://localhost:8000
```

### Timeouts
- **WebSocket Connection**: 30 seconds (settable in hook)
- **Overall Operation**: 60 seconds (browser default)
- **API Call**: 10 seconds (per request)

## 📊 Monitoring

### Check Status
```bash
# Backend health
curl http://localhost:8000/health

# API docs
curl http://localhost:8000/docs

# Database schema
cd backend
python check_db_schema.py
```

### Debug Messages
```javascript
// In browser console
// WebSocket messages are logged with [WebSocket] prefix
// Look in browser console for real-time updates
```

## ❌ Troubleshooting

### "Connection timeout - server not responding"
- Is backend running? `curl http://localhost:8000/health`
- Is frontend running? `curl http://localhost:5174`
- Are they on correct ports?

### "Email address not verified in AWS SES"
- Add recipient to SES Verified Identities
- Or request production access to remove sandbox restrictions
- Contact AWS Support

### "Upgrade required"
- Check user subscription type in database
- Upgrade user to "pro" subscription
- Must have `subscription_type = 'pro'`

### "Authentication token missing"
- Refresh page and login again
- Check browser DevTools → Application → Local Storage → token
- Token should be a valid JWT

### "Template not found"
- Check template exists in database
- Verify template ID is correct
- Ensure template is marked `is_active = true`

### "Email sending takes too long"
- AWS SES can be slow in sandbox mode (5-30s normal)
- Network latency affects response time
- Try again - transient issues are normal

## 📈 Performance Tips

1. **Use WebSocket instead of REST** - Already implemented ✓
2. **Batch emails** - Send multiple to same recipient in one flow
3. **Optimize templates** - Keep subject/body reasonable length
4. **Pre-select template** - Default to most used template
5. **Cache templates locally** - On first load, store in state

## 🔒 Security

- PRO subscription required to send emails
- JWT token validated on every WebSocket connection
- User role must be RECRUITER
- Sender email must be verified in AWS SES
- Recipient email must be verified (in sandbox mode)
- Dynamic data properly escaped before sending

## 📞 Support Resources

- **Frontend Component**: `src/components/EmailSendLive.jsx`
- **WebSocket Hook**: `src/hooks/useWebSocketEmailSend.js`
- **Backend Router**: `backend/app/modules/recruiter/websocket_router.py`
- **Test Guide**: `TEST_EMAIL_SENDING.md`
- **Full Docs**: `EMAIL_WEBSOCKET_FIX_COMPLETE.md`

## 🎯 Key Features

✅ **Real-time Status Updates**
- See exact step: Preparing → Validating → Sending
- Clear progress indication

✅ **Dynamic Templates**
- Recruiters fill in required fields
- Fields auto-generated from template
- Pre-filled form values on retry

✅ **Error Handling**
- Clear, actionable error messages
- Automatic data preservation on retry
- Network error recovery

✅ **Responsive Design**
- Works on desktop, tablet, mobile
- Touch-friendly interface
- Accessible keyboard navigation

✅ **Cross-Browser Support**
- Chrome, Firefox, Safari, Edge
- Mobile browsers (iOS, Android)
- Consistent behavior across all

## 📝 Example Workflow

```
1. Recruiter logs in (must be PRO)
   ↓
2. Searches for candidate: "John Doe"
   ↓
3. Clicks candidate → Opens profile
   ↓
4. Clicks "📧 Send Email" button
   ↓ Modal opens ↓
5. Modal shows "Loading templates..."
   ↓
6. Templates loaded → User selects "Interview Invitation"
   ↓
7. Form shows dynamic fields to fill:
     - Position: "Senior Developer"
     - Company: "Acme Corp"
     - Date: "2026-04-20"
     - Time: "2:00 PM"
     - Location: "Room 305"
   ↓
8. User clicks "Send Email"
   ↓
9. Status updates:
     - "Connected. Preparing email..."
     - "Validating template and recipient..."
     - "Sending via AWS SES..."
   ↓
10. Success! Shows:
     - ✅ Email sent successfully
     - Message ID: 0100019d311281d5-...
     - Close button
   ↓
11. User clicks "Close"
   ↓
12. Modal closes, user back to profile
```

## 🚨 Emergency Troubleshooting

**If nothing works:**
1. Restart backend: `Ctrl+C` then run again
2. Restart frontend: `Ctrl+C` then `npm run dev`
3. Clear browser cache: DevTools → Application → Clear All
4. Check ports are available: `lsof -i :8000` and `lsof -i :5174`
5. Check database is up: Run `python check_db.py`

**If you see errors in console:**
1. Take screenshot of error
2. Note the request/response in Network tab
3. Check backend logs for matching errors
4. Run test: `python test_websocket_email.py`

## 📚 Further Reading

- [Complete Testing Guide](TEST_EMAIL_SENDING.md)
- [Detailed Architecture](EMAIL_WEBSOCKET_FIX_COMPLETE.md)
- [API Documentation](../API.md)
- [Architecture Overview](../ARCHITECTURE.md)
