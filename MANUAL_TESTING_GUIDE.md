# MANUAL TESTING GUIDE - ALL IMPLEMENTATIONS

Complete step-by-step guide to manually test all three implementations in the running application.

---

## Prerequisites

### Start Backend Server
```bash
cd d:\recruitment\backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected Output**:
```
Uvicorn running on http://0.0.0.0:8000
```

### Start Frontend Server
```bash
cd d:\recruitment\frontend
npm run dev
```

**Expected Output**:
```
VITE v... ready in ... ms ➜  Local: http://localhost:5173/
```

### Login Credentials
- **Email**: lakshmi@example.com
- **Password**: password123

---

## TEST SCENARIO 1: Cache Control Headers

### What to Test
Verify that the profile endpoint returns proper cache control headers that prevent browser caching.

### Steps

1. **Open Browser DevTools**
   - Press F12
   - Go to "Network" tab
   - Keep DevTools open

2. **Login to Application**
   - Navigate to http://localhost:5173
   - Enter email and password
   - Click "Sign In"

3. **Check Network Request**
   - Look for request to `/api/candidates/me`
   - Click on this request in Network tab
   - Go to "Response Headers" tab

4. **Verify Cache Control Headers**
   ```
   ✓ Cache-Control: no-cache, no-store, must-revalidate
   ✓ Pragma: no-cache
   ✓ Expires: 0
   ```

5. **Expected Behavior**
   - Headers appear in response
   - Browser won't cache this response
   - Each page load gets fresh data from server

### Verification Points
- [ ] Cache-Control header present
- [ ] Pragma header present
- [ ] Expires header set to 0
- [ ] No caching directive missing

### Success Criteria
✅ All three headers are present with correct values

---

## TEST SCENARIO 2: Resume Delete Functionality

### What to Test
Verify that candidates can delete resumes which removes them from both UI and database.

### Prerequisites
- At least one resume should be uploaded
- If none exist, upload a test resume first

### Steps

#### Part A: Upload Test Resume (if needed)

1. **Navigate to Resumes Tab**
   - Click "Resumes" button on dashboard

2. **Upload a Resume**
   - Click "Choose File"
   - Select a PDF or DOCX file
   - Click "Upload Resume"
   - Wait for "Resume parsed successfully!" message

3. **Verify Resume Appears**
   - Resume should appear in the table below
   - Status should show "PARSED" or "UPLOADED"

#### Part B: Delete Resume

1. **Locate Resume to Delete**
   - See list of resumes in table
   - Find any resume row

2. **Click Delete Button**
   - Look for red "Delete" button in Action column
   - Click it

3. **Confirm Deletion**
   - Browser shows: "Are you sure you want to delete this resume?"
   - Click "OK" to confirm
   - Click "Cancel" to abort

4. **Observe UI Update**
   ```
   Expected:
   ✓ Button shows "Deleting..." state
   ✓ Button is disabled (grayed out)
   ✓ Resume immediately disappears from table
   ```

5. **Check Backend Processing**
   - Look at backend terminal
   - Should see logs like:
   ```
   [DELETE /resumes/{resume_id}] user_id=..., delete initiated
   Deleted X skills for resume_id: ...
   Deleted Y experiences for resume_id: ...
   Deleted Z educations for resume_id: ...
   Deleted file from S3 for resume_id: ...
   Deleted resume record for resume_id: ...
   ```

6. **Verify Success Message**
   - Green success message appears: "Resume deleted successfully!"
   - Message disappears after 3 seconds

7. **Refresh Page**
   - Press F5 to refresh
   - Resume should NOT reappear (verifies database deletion)
   - Profile counts should decrease

8. **Check Skills/Experiences/Educations**
   - Go to "Profile" tab
   - Verify counts decreased if deletion removed derived data

### Error Scenarios to Test

#### Scenario A: Network Error
1. **Start deletion**
2. **Disconnect internet** (simulate network error)
3. **Expected**: 
   - Error message appears
   - Resume is restored to list
   - Can try again

#### Scenario B: Multiple Deletes
1. **Start deleting one resume**
2. **Quickly click delete on another resume**
3. **Expected**:
   - Both appear to delete
   - Both should be removed on confirmation

### Verification Points
- [ ] Delete button shows "Deleting..." state
- [ ] Resume immediately disappears from UI
- [ ] Success message appears
- [ ] After refresh, resume stays deleted
- [ ] Backend logs show cascade delete
- [ ] Skills/experiences/educations counts decrease
- [ ] Error message and recovery works if network fails

### Success Criteria
✅ Resume disappears from UI and database after delete

---

## TEST SCENARIO 3: Resume View Functionality

### What to Test
Verify that candidates can view their resumes in a new browser tab.

### Prerequisites
- At least one resume should exist
- If none exist, upload a test resume first

### Steps

1. **Navigate to Resumes Tab**
   - Click "Resumes" button on dashboard
   - See list of resumes in table

2. **Locate Resume to View**
   - Find any resume in the table
   - Verify status is not blank

3. **Click View Button**
   - Click blue "View" button in Action column
   - Observe button behavior

4. **Observe Button State**
   ```
   Expected:
   ✓ Button text changes to "Opening..."
   ✓ Button becomes disabled (grayed out)
   ✓ No page navigation occurs
   ```

5. **New Tab Opens**
   ```
   Expected:
   ✓ Browser opens a new tab
   ✓ New tab shows resume document
   ✓ Can scroll through document in viewer
   ✓ Dashboard remains open in original tab
   ```

6. **View Resume Content**
   - **For PDF**: 
     - See PDF pages
     - Can scroll up/down
     - Can zoom in/out
     - Can download
   
   - **For DOCX**: 
     - Browser renders document
     - Can scroll
     - Can print/download

7. **Return to Dashboard**
   - Click "< Back" or original tab
   - Dashboard is still showing Resumes tab
   - View button returns to normal state "View"

8. **Test Multiple Views**
   - View same resume again
   - View different resume
   - Each should open in new tab

9. **Check Backend Logs**
   - Look at backend terminal
   - Should see logs like:
   ```
   [GET /resumes/{resume_id}/view] user_id=..., opening for view
   Resume {resume_id} viewed by user {current_user.id}
   ```

10. **Verify Audit Logging**
    - Each view is logged
    - Backend shows RESUME_VIEWED event

### Error Scenarios to Test

#### Scenario A: Invalid Resume
1. **Manually modify URL** in new tab to invalid ID
   - `http://localhost:8000/api/resumes/invalid-id/view`
2. **Expected**: 
   - Browser shows error: "Invalid resume ID format" (400)
   - Or "Resume not found" (404)

#### Scenario B: Network Error During View
1. **Start viewing resume**
2. **Dashboard error message appears** if view fails
3. **Expected**:
   - Message: "Failed to view resume: [error]"
   - Can try again
   - Button returns to normal state

### Verification Points
- [ ] View button shows "Opening..." state
- [ ] View button is disabled during load
- [ ] New tab opens with resume
- [ ] Dashboard remains open
- [ ] Button returns to normal after tab opens
- [ ] Can view multiple resumes
- [ ] Backend logs show view event
- [ ] Audit logging records the view

### Success Criteria
✅ Resume opens in new browser tab and displays correctly

---

## TEST SCENARIO 4: UI/UX Integration

### Verify Dashboard Consistency

1. **Check Profile Tab**
   - View Profile tab
   - Skills, Experiences, Educations should display
   - Verify "View Full Profile" button is REMOVED
   - Dashboard should show counts only

2. **Check Resumes Tab**
   - See table with File Name, Type, Status, Uploaded, Action columns
   - View and Delete buttons present for each resume

3. **Check Tab Switching**
   - Click Profile tab → shows profile data
   - Click Resumes tab → shows resume list
   - Switching back and forth works smoothly

4. **Check Message Display**
   - Upload message shows in green
   - Delete message shows in green
   - Error messages show in red
   - Messages auto-dismiss after 3 seconds

### Verification Points
- [ ] "View Full Profile" button is gone
- [ ] Tab switching works
- [ ] Messages display with correct colors
- [ ] Messages auto-dismiss
- [ ] No console errors

---

## TEST SCENARIO 5: Edge Cases

### Test Case A: Empty Resume List
1. **Delete all resumes**
2. **Click Resumes tab**
3. **Expected**: "No resumes uploaded yet..." message appears

### Test Case B: Resume Still Processing
1. **Upload resume**
2. **Quickly try to view before PARSED**
3. **Expected**: Resume status shows "UPLOADED" or similar
4. **After parsing**: Can then view

### Test Case C: Rapid Clicks
1. **Click View multiple times quickly**
2. **Expected**: Only first click triggers view, others ignored

### Test Case D: Multiple Browser Tabs
1. **Open dashboard in two tabs**
2. **Delete resume in Tab A**
3. **Refresh Tab B**
4. **Expected**: Resume gone in Tab B (shows fresh data)

### Test Case E: Long File Names
1. **Upload resume with long filename**
2. **View in table**
3. **Expected**: Filename displays properly, doesn't break layout

---

## Performance Testing

### Measure Load Times

1. **Profile Load**
   - Time from login to dashboard showing
   - Expected: < 3 seconds

2. **Resume Delete**
   - Time from click to disappear
   - Expected: < 1 second (UI), < 5 seconds (API)

3. **Resume View**
   - Time from click to tab opening with content
   - Expected: < 3 seconds

### Monitor Network

1. **Use DevTools Network Tab**
2. **Delete operation**:
   - Should see: DELETE /api/resumes/{id}
   - Response size: small (JSON)
   - Time: < 2 seconds

3. **View operation**:
   - Should see: GET /api/resumes/{id}/view
   - Response size: large (file content)
   - Time: depends on file size

---

## Bug Report Template

If you find issues, use this template:

```
## Bug Report
- **Feature**: [Cache Control / Delete / View]
- **Steps to Reproduce**: [specific steps]
- **Expected**: [what should happen]
- **Actual**: [what actually happened]
- **Screenshot**: [if applicable]
- **Browser**: [Chrome/Firefox/Safari version]
- **Backend Logs**: [relevant log lines]
```

---

## Success Checklist

Use this checklist to verify all implementations:

### Cache Control Headers
- [ ] Headers present in response
- [ ] Cache-Control correct
- [ ] Pragma set
- [ ] Expires set to 0
- [ ] Profile always shows fresh data

### Resume Delete
- [ ] Delete button appears
- [ ] Confirmation dialog works
- [ ] Optimistic UI update removes resume
- [ ] Success message displays
- [ ] After refresh, deleted resume stays gone
- [ ] Backend logs show cascade delete
- [ ] Skills/experience counts decrease
- [ ] Error recovery works

### Resume View
- [ ] View button appears
- [ ] Button shows "Opening..." during load
- [ ] New tab opens with resume
- [ ] Resume displays correctly
- [ ] Can view multiple resumes
- [ ] Backend logs show view event
- [ ] View button disabled during load
- [ ] Multiple rapid clicks handled correctly

### General
- [ ] No console errors
- [ ] No network errors
- [ ] Responsive UI (buttons work)
- [ ] Dark mode works (if applicable)
- [ ] Mobile view works (if applicable)

---

## Troubleshooting

### Backend Won't Start
```bash
# Check if port 8000 in use
netstat -ano | findstr ":8000"

# Kill process on port 8000
taskkill /PID <PID> /F
```

### Frontend Won't Start
```bash
# Clear npm cache
npm cache clean --force

# Reinstall dependencies
rm -r node_modules package-lock.json
npm install

# Start dev server
npm run dev
```

### Resume Delete Fails
- Check backend logs for errors
- Verify user owns the resume
- Check S3 credentials
- Check database connection

### Resume View Shows Error
- Check resume file exists in S3
- Check file permissions
- Verify browser can display file type
- Check CORS headers

### No Audit Logs
- Check audit table in database
- Verify logging is enabled
- Check backend log level

---

## Submit Test Results

After completing manual tests, note:
- Date of testing
- Browser and version
- Number of tests passed/failed
- Any issues encountered
- Suggestions for improvement

---

**Last Updated**: March 28, 2026  
**Version**: 1.0  
**Status**: Ready for Manual Testing
