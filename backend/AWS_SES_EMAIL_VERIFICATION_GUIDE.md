# AWS SES Email Verification Guide

## Problem
When attempting to send emails via AWS SES, you may receive this error:
```
Email address is not verified. The following identities failed the check in region US-EAST-1: candidate@example.com
```

## Root Cause
AWS SES operates in **Sandbox Mode** by default for new AWS accounts. In sandbox mode:
- ✅ You can send emails FROM any verified email address
- ❌ You can only send emails TO verified email addresses
- ❌ Limited to 1 email per second
- ❌ Limited to 200 emails per 24 hours

## Solution: Verify Recipient Email Addresses

### Step 1: Go to AWS SES Console
1. Open [AWS SES Console](https://console.aws.amazon.com/sesv2/)
2. Make sure you're in the correct region: **US-EAST-1** (us-east-1)

### Step 2: Verify Email Address
1. Navigate to **Verified Identities** (left menu)
2. Click **"Create Identity"** button
3. Select **"Email address"** radio button
4. Enter the email address you want to verify (e.g., `priya12@gmail.com`)
5. Click **"Create Identity"**

### Step 3: Check Your Email
1. Go to your email inbox for the address you just verified
2. Find the verification email from AWS
3. Click the verification link in the email
4. You should see a confirmation page

### Step 4: Verify in SES Console
1. Refresh the AWS SES Verified Identities page
2. You should now see your email with status **"Verified"** ✅

## Now You Can Send Emails!

After verifying an email address, you can immediately send emails to it via the app.

### Example Flow:
1. **Recruiter** (bob@gmail.com - already verified)
2. **Candidate** (priya12@gmail.com - NOW verified ✅)
3. **Send Email** → Should work! ✅

## Testing

### Test 1: Send to Verified Email
```bash
# In browser, go to candidate profile and send email
# Expected: Email sent successfully ✅
```

### Test 2: Send to Unverified Email
```bash
# Try sending to an unverified email like test@example.com
# Expected: Error message - Email address not verified ❌
# Next step: Verify test@example.com in AWS SES console
```

## Future: Request Production Access

If you want to send emails to any email address (remove sandbox restrictions):
1. Go to AWS SES Console
2. Click **"Account Dashboard"**
3. Look for **"Send quota"** section
4. Click **"Edit sending quota and constraints"**
5. Check for **"Request production access"** link
6. Fill out the form explaining your use case
7. AWS will review and respond within 24 hours

For production access, AWS typically requires:
- Valid email verification process
- Opt-in/opt-out mechanisms
- Low complaint rate
- Proof of legitimate use case

## Verification Status Indicators

### In the Application:
- ✅ **Email sent successfully** = Recipient email is verified
- ❌ **Email address is not verified** = Recipient email needs verification
- ❌ **Cannot send email** = Sender email might not be verified (contact admin)

### In AWS SES Console:
- 🟢 Green checkmark = Verified ✅
- ⏳ Pending = Awaiting email confirmation
- 🔴 Red X = Not verified

## Verified Emails in Your System

Currently verified for sending emails:
- ✅ **priyachatgpt44@gmail.com** (Sender - already verified)

Emails that need verification to receive emails:
- ❌ Any candidate email address (must be verified individually)

## Common Issues

### Issue: "Email address is not verified"
**Solution:** Follow Step 1-4 above to verify the email

### Issue: "Verification email not received"
**Solution:** 
1. Check spam/junk folder
2. Wait 5 minutes (verification email should arrive)
3. If still not received, delete and recreate the identity

### Issue: "Still can't send after verifying"
**Solution:**
1. Refresh the browser
2. Restart the backend server
3. Check AWS console that email is marked "Verified" ✅

## Architecture Flow

```
Recruiter Sends Email
    ↓
Frontend validates input
    ↓
Backend renders template
    ↓
Backend calls AWS SES
    ↓
AWS SES checks:
   - Sender verified? ✅ (priyachatgpt44@gmail.com)
   - Recipient verified? ✅ (must be verified)
   - Both OK?
        YES → Email sent ✅
        NO → MessageRejected error ❌
```

## Quick Reference

| Item | Status | Action |
|------|--------|--------|
| Sender Email | ✅ Verified | None needed |
| AWS Region | ✅ US-EAST-1 | Correct |
| Sandbox Mode | ✅ Active | Request production access if needed |
| Recipient Email | ❌ NOT Verified | Verify in AWS SES console |

## Database Verification Status

Wait, I realized the application also stores emails in the database. Let me check:

```sql
-- Check emails sent in database:
SELECT to_email, status, created_at FROM emails_sent 
ORDER BY created_at DESC 
LIMIT 10;

-- Expected output:
-- to_email | status | created_at
-- priya12@gmail.com | SENT | 2026-03-28 ...
```

## Support

If emails still aren't sending after verification:
1. Check browser console for errors (F12 → Console tab)
2. Check backend logs for detailed error messages
3. Verify recipient email in AWS SES console is showing ✅
4. Try sending from a different template
5. Check that recruiter has PRO subscription

---

**Last Updated:** March 28, 2026
**Status:** ✅ Ready to test email sending
