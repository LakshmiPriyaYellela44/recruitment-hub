# WebSocket Live Email Status - Debug Guide

## Current Status
✅ Backend WebSocket endpoint fully implemented with comprehensive logging  
✅ Frontend hook fully implemented with detailed console logs  
⚠️ Connection not working - need to debug

## Quick Reproduction Steps

### 1. **Restart Backend Server** (CRITICAL - loads new logging code)
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```
Wait for: `Application startup complete [uvicorn]`

### 2. **Reset Frontend** (Clear cache)
- Open browser to http://localhost:3000
- Press Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac) to hard refresh
- Or: DevTools > Network > Disable Cache (checkbox), then refresh

### 3. **Open Browser DevTools**
- Press F12
- Click "Console" tab
- Keep this visible while testing

### 4. **Send Test Email**
- Navigate to any candidate profile page
- Click "📧 Send Email" button
- Fill in:
  - Subject: `Test Email Websocket`
  - Body: `This is a test of the websocket connection`
- Click "Send Email" button

### 5. **Check Logs**

#### **Frontend Console (Most Important)**
Look for logs starting with `[WebSocket]`:
```
[WebSocket] Connection details:
  URL: ws://localhost:3000/api/recruiters/ws/send-email/...
  Protocol: ws:
  Host: localhost:3000
  Candidate ID: xxxxx
  Token length: 123

[WebSocket] ✓ Connected to email service
[WebSocket] ✓ Message received: {status: "sending", message: "Sending email..."}
```

#### **Backend Server Terminal**
Look for logs starting with `[WebSocket]` or `[WebSocket Auth]`:
```
[WebSocket] New connection attempt for candidate: xxxxx
[WebSocket Auth] Token found in query params: Bearer eyJxx...
[WebSocket Auth] User authenticated: test@example.com
[WebSocket] Validating recruiter role...
```

---

## Common Issues & Solutions

### **Issue 1: No Frontend Logs at All**
**Symptom:** Console completely silent after clicking "Send Email"  
**Likely Cause:** Frontend hook not being called or component not mounted  

**Solution:**
1. Check browser console for any JavaScript errors (red messages)
2. Verify token exists: Open Console, type: `localStorage.getItem('access_token')`
   - Should return a token string (looks like: `eyJhbGc...`)
   - If empty: Logout and login again
3. Verify component is mounted: Search console for "EmailSendLive" logs

---

### **Issue 2: `[WebSocket] ✗ Connection error`**
**Symptom:** Frontend shows connection error immediately after clicking "Send Email"  
**Log Example:**
```
[WebSocket] Connection details:...
[WebSocket] ✗ Connection error: Event {...}
```

**Likely Causes:**
- CORS issue (most common with WebSocket)
- Backend not running or wrong port
- URL format incorrect

**Solution:**
1. Verify backend is running: Open browser to `http://localhost:8000/health`
   - Should show: `{"status":"healthy"}`
2. Check backend logs for CORS errors or crashes
3. Try manual WebSocket test in console:
   ```javascript
   const token = localStorage.getItem('access_token');
   const ws = new WebSocket(`ws://localhost:8000/api/recruiters/ws/send-email/candidate123?token=${token}&subject=Test&body=Test`);
   ws.onopen = () => console.log("Connected!");
   ws.onerror = (e) => console.error("Error:", e);
   ```
4. If manual test fails, backend can't reach WebSocket

---

### **Issue 3: Connection Opens But No Messages Received**
**Symptom:** Console shows `✓ Connected` but then nothing else happens  
**Log Example:**
```
[WebSocket] ✓ Connected to email service
(silence...)
```

**Likely Causes:**
- Backend not receiving connection (backend logs empty)
- Backend authentication failing silently
- Connection lost before message sent

**Solution:**
1. Check backend logs for `[WebSocket]` entries
   - Should see: `[WebSocket] New connection attempt for candidate: xxxxx`
   - If missing: Backend not receiving the WebSocket upgrade request
2. If backend logs show connection but then error:
   - Check `[WebSocket Auth]` logs for token extraction failure
   - Verify query params being passed correctly
3. Add manual timeout check:
   ```javascript
   setTimeout(() => console.log("Still waiting for message..."), 3000);
   ```

---

### **Issue 4: Backend Shows Connection But Frontend Gets Error**
**Symptom:** Backend logs show `[WebSocket] New connection...` but frontend shows error  
**Backend Logs:** `[WebSocket] New connection attempt for candidate: xxxxx` then error

**Likely Causes:**
- Authentication failure
- Subscription check failure
- SES error

**Solution:**
1. Check backend logs for specific error:
   ```
   [WebSocket Auth] Token verification failed: Invalid token
   [WebSocket] Recruiter role verification failed
   [WebSocket] PRO subscription check failed
   [WebSocket] SES error: MessageId xxxxx
   ```
2. Based on error, fix:
   - **Token verification failed**: Token expired, logout and login again
   - **Recruiter role failed**: User is not recruiter, use recruiter account
   - **PRO subscription failed**: Upgrade subscription to PRO
   - **SES error**: Check AWS credentials and SES configuration

---

### **Issue 5: Special Characters Breaking URL**
**Symptom:** Email body with special chars (quotes, ampersand, etc.) causes connection to fail  
**Example:** Body with `{"key": "value"}` breaks URL

**Solution:** Already handled by `encodeURIComponent()` in hook - should work fine. If still failing:
1. Check frontend logs show properly encoded URL
2. Shorten body text to simple ASCII for testing
3. Try: `Test email body` instead of complex characters

---

### **Issue 6: CORS Error (Common for WebSocket)**
**Symptom:** Browser console shows CORS error or connection rejected  
**Log Example:**
```
WebSocket connection to 'ws://...' failed:
Access-Control-Allow-Origin header is missing
```

**Solution:**
- ✅ CORS is already configured in backend for WebSocket
- If error persists, verify:
  1. Frontend URL: `http://localhost:3000` (not `http://127.0.0.1:3000`)
  2. Backend CORS config includes `allow_headers=["*"]` (it does)
  3. Try restarting backend with: `python -m uvicorn app.main:app --reload --port 8000`

---

## Diagnostic Commands

### **Test Backend is Running**
```bash
# From terminal
curl http://localhost:8000/health
# Should return: {"status":"healthy","app":"Recruitment Platform"}
```

### **Check Token Format**
Console:
```javascript
let token = localStorage.getItem('access_token');
console.log("Token exists:", !!token);
console.log("Token starts with Bearer:", token?.startsWith('Bearer'));
console.log("Token length:", token?.length);
```

### **Manual WebSocket Connection Test**
Console:
```javascript
let token = localStorage.getItem('access_token');
let ws = new WebSocket(`ws://localhost:8000/api/recruiters/ws/send-email/test123?subject=Test&body=Test&token=${token}`);
ws.onopen = () => console.log("✓ WebSocket connected!");
ws.onmessage = (e) => console.log("Message:", e.data);
ws.onerror = (e) => console.error("✗ WebSocket error:", e);
```

### **Check Backend Logs Include WebSocket**
Terminal (backend):
```
# Should see lines like:
# [WebSocket] New connection attempt for candidate: xxxxx
# [WebSocket Auth] Token found in query params
# [WebSocket] Sending email via SES...
```

---

## Checklist for Debugging

- [ ] Backend restarted? (New logging code loads on startup)
- [ ] Frontend page hard-refreshed? (Ctrl+Shift+R)
- [ ] You're logged in? (Token exists in localStorage)
- [ ] Browser console open and watching? (F12)
- [ ] Backend server shows "startup complete"?
- [ ] Health check works? (http://localhost:8000/health)
- [ ] Candidate ID is valid? (Real candidate in database)
- [ ] Recruiter account has PRO subscription?

---

## Expected Log Sequence (Happy Path)

### Frontend Console:
```
[WebSocket] Connection details:
  URL: ws://localhost:8000/api/recruiters/ws/send-email/xxxxx?subject=Test&body=Test&token=Bearer...
  Protocol: ws:
  Host: localhost:8000
  Candidate ID: xxxxx
  Token length: 250
[WebSocket] ✓ Connected to email service
[WebSocket] ✓ Message received: {status: "sending", message: "Sending email..."}
[WebSocket] Status: sending...
[WebSocket] ✓ Message received: {status: "success", message: "Email sent successfully!", message_id: "0000017d-xxxx-xxxx-xxxx-xxxxxxx"}
[WebSocket] Status: success! 0000017d-xxxx-xxxx-xxxx-xxxxxxx
```

### Backend Terminal:
```
[WebSocket] New connection attempt for candidate: xxxxx
[WebSocket Auth] Token found in query params: Bearer eyJhbGc...
[WebSocket Auth] User authenticated: recruiter@example.com
[WebSocket] Validating recruiter role...
[WebSocket] Recruiter role verified ✓
[WebSocket] Checking PRO subscription...
[WebSocket] PRO subscription verified ✓
[WebSocket] Valid candidate ID: xxxxx
[WebSocket] Sending email via SES...
[WebSocket] SES MessageId: 0000017d-xxxx-xxxx-xxxx-xxxxxxx
[WebSocket] ✓ Email sent successfully
[WebSocket] Closing connection after success
```

### UI Display:
```
Form loads
User enters subject & body
User clicks "Send Email"
Modal shows: "Connected. Preparing to send email..."
Modal shows spinner and: "Sending email..."
Modal shows success: "Email sent successfully! ✓"
Modal shows: MessageId: 0000017d-xxxx-xxxx-xxxx-xxxxxxx
```

---

## Need Help?

1. **Collect logs:**
   - Copy entire frontend console output (right-click > Save as)
   - Copy backend server output (select all, copy)
   
2. **Provide:**
   - Frontend logs (starting with `[WebSocket]`)
   - Backend logs (starting with `[WebSocket]`)
   - Exact error message shown in modal (if any)

3. **Last resort:**
   - Check browser Network tab (F12 > Network > Filter "websocket")
   - Look for WebSocket connection - should show status 101 (Switching Protocols)
   - If status is 400/403/401 - backend rejected connection
   - If status is different or missing - connection never reached backend
