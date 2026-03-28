# Email Sending Feature - Test Suite

This directory contains comprehensive tests for the email sending feature, including unit tests, Python WebSocket tests, and Playwright E2E tests.

## Test Files

### 1. Python WebSocket Test (`test_websocket_email.py`)
Tests the WebSocket connection and email sending at the API level.

**Features:**
- Network connectivity check
- JWT token generation and validation
- WebSocket connection testing
- Real-time status message verification
- Error handling and timeout testing
- Detailed test report with timing information

**Usage:**
```bash
cd backend
python test_websocket_email.py
```

**Expected Output:**
```
[✓] SUCCESS: Backend is reachable at localhost:8000
[✓] SUCCESS: WebSocket connection established
[⏱  1.23s] Status: PREPARING  | Preparing email template
[⏱  2.45s] Status: VALIDATING | Validating template and recipient
[⏱  3.67s] Status: SENDING    | Sending via AWS SES
[⏱  8.90s] Status: SUCCESS    | Email sent successfully!
```

### 2. Playwright E2E Tests (`tests/email_sending.spec.js`)
Tests the complete user workflow in the browser.

**Test Cases:**
- User authentication (login as PRO recruiter)
- Navigation to candidate profile
- Email button visibility
- Email modal opening and template loading
- Dynamic data field display and validation
- Email sending with status updates
- Error handling and retry flow
- Modal closing and cleanup
- Subscription level checks (PRO vs BASIC)

**Usage:**
```bash
# Run all tests
npm run test:e2e

# Run specific test
npm run test:e2e -- email_sending

# Run with headed browser (see what's happening)
npm run test:e2e -- email_sending --headed

# Run on specific browser
npm run test:e2e -- email_sending --project=chromium
```

### 3. Advanced Playwright Tests (`tests/email_websocket_advanced.spec.js`)
Tests advanced scenarios and cross-browser compatibility.

**Test Scenarios:**
- WebSocket timeout handling
- Real-time status updates
- Authentication errors
- Network error simulation
- Dynamic data substitution and validation
- Recipient information display
- Template selection feedback
- Progress indication
- Rapid successive sends
- Form data persistence
- Special character handling
- Cross-browser consistency
- Performance testing
- Accessibility compliance

**Usage:**
```bash
# Run advanced tests
npm run test:e2e -- email_websocket_advanced

# Run specific test
npm run test:e2e -- email_websocket_advanced -g "timeout"

# Run on all browsers
npm run test:e2e -- email_websocket_advanced --project=chromium --project=firefox --project=webkit
```

## Test Architecture

### Frontend Changes
- **WebSocket Hook** (`src/hooks/useWebSocketEmailSend.js`)
  - Added 30-second timeout
  - Improved error messages
  - Proper resource cleanup
  - State management improvements

- **EmailSendLive Component** (`src/components/EmailSendLive.jsx`)
  - Enhanced loading states
  - Real-time status display
  - Detailed sending information
  - Better error messages
  - Improved user feedback

- **CSS Enhancements** (`src/components/EmailSendLive.css`)
  - Added `status-message` styling
  - Added `sending-details` section
  - Added `hint` text styling
  - Better visual feedback

### Backend Changes
- **WebSocket Router** (`backend/app/modules/recruiter/websocket_router.py`)
  - Added multiple status updates: preparing, validating, sending
  - Improved error messages with user-friendly explanations
  - Better logging for debugging
  - Specific error handling for common issues

## Setting Up Test Environment

### Prerequisites
```bash
# Install dependencies
npm install --save-dev @playwright/test

# For Playwright browsers
npx playwright install
```

### Configuration
1. Update test credentials in your test files:
   ```javascript
   const PRO_RECRUITER_EMAIL = 'your-test-recruiter@example.com';
   const PRO_RECRUITER_PASSWORD = 'test-password';
   ```

2. Ensure test candidates exist in the database

3. Update email templates as needed

4. Configuration in `playwright.config.js` handles:
   - Browser setup (Chromium, Firefox, WebKit)
   - Test server startup
   - Timeouts and retries
   - Screenshot/video capture
   - Report generation

## Running Tests

### Quick Start
```bash
# Terminal 1: Start backend
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level debug

# Terminal 2: Start frontend
cd frontend
npm run dev

# Terminal 3: Run tests
npm run test:e2e
```

### Individual Test Suites

**Python WebSocket Tests:**
```bash
cd backend
python test_websocket_email.py
```

**JavaScript E2E Tests:**
```bash
# All tests
npm run test:e2e

# Specific file
npm run test:e2e -- email_sending.spec.js

# Specific test case
npm run test:e2e -- email_sending.spec.js -g "should send email successfully"

# With UI mode (interactive debugging)
npx playwright test --ui

# Debug mode (step through tests)
npx playwright test --debug
```

## Test Reports

After running Playwright tests, reports are generated:

```bash
# Open HTML report
npx playwright show-report

# JSON report (for CI integration)
cat test-results.json

# JUnit XML report (for CI/CD pipelines)
cat junit-results.xml
```

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Email Sending Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
    
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18
      - uses: actions/setup-python@v4
        with:
          python-version: 3.10
      
      - name: Install dependencies
        run: |
          npm install
          npm install -D @playwright/test
          npx playwright install
      
      - name: Run Playwright tests
        run: npm run test:e2e
      
      - name: Upload Playwright report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: playwright-report/
```

## Troubleshooting

### WebSocket Connection Timeout
**Problem:** Tests timeout waiting for WebSocket messages
**Solution:**
1. Verify backend is running: `curl http://localhost:8000/health`
2. Check JWT token is valid
3. Verify recruiter has PRO subscription
4. Check AWS SES configuration

### Authentication Errors
**Problem:** Tests fail with 401/403 errors
**Solution:**
1. Update test credentials in test files
2. Verify user exists in database
3. Check JWT_SECRET matches backend
4. Verify user has RECRUITER role

### Template Not Found
**Problem:** Template selection fails
**Solution:**
1. Verify templates exist in database
2. Check template IDs in test data
3. Verify templates are marked as active

### Email Sending Fails
**Problem:** Email doesn't send despite tests passing to sending stage
**Solution:**
1. Check AWS SES sandbox mode limitations
2. Verify recipient email is whitelisted in SES
3. Check SES sender email verification
4. Review AWS CloudWatch logs

### Browser Compatibility Issues
**Problem:** Tests pass on one browser but fail on another
**Solution:**
1. Run tests with `--headed` to see UI differences
2. Check viewport size settings
3. Verify WebSocket support (usually always supported)
4. Check for browser-specific event handling

## Performance Baseline

Expected timings for successful email send:
- **Connection**: < 1 second
- **Validation**: < 2 seconds
- **Sending**: 2-5 seconds (depends on AWS SES)
- **Total**: 5-10 seconds typical, max 30 seconds with delays

## Best Practices

1. **Test Data Isolation**: Use unique test data for each test run
2. **Cleanup**: Ensure database is cleaned up after tests
3. **Mocking**: Mock external services (AWS SES) when needed
4. **Error Handling**: Test both success and failure paths
5. **Accessibility**: Verify keyboard navigation and screen reader support
6. **Performance**: Monitor test execution time
7. **CI/CD**: Run tests on every commit to catch regressions

## Test Coverage Goals

- **Unit Tests**: 80%+ coverage of email service functions
- **Integration Tests**: WebSocket communication
- **E2E Tests**: Complete user workflows
- **Cross-browser**: Chromium, Firefox, WebKit
- **Responsive**: Mobile and desktop viewports

## Future Improvements

- [ ] Performance benchmarking
- [ ] Load testing with multiple concurrent sends
- [ ] Multi-language UI testing
- [ ] A/B testing different UI variations
- [ ] Analytics and metrics tracking
- [ ] Error recovery strategies
- [ ] GraphQL validation
- [ ] WebSocket reconnection testing

## Support

For issues or questions:
1. Check test logs: `npm run test:e2e -- --debug`
2. Review browser console: Use `--headed` mode
3. Check backend logs: `docker logs backend`
4. Review Playwright documentation: https://playwright.dev

## Related Documentation

- [Email Feature Guide](../EMAIL_SENDING_FIX_SUMMARY.md)
- [Architecture Guide](../ARCHITECTURE.md)
- [API Documentation](../API.md)
- [Deployment Guide](../DEPLOYMENT.md)
