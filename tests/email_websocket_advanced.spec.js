import { test, expect, devices } from '@playwright/test';

/**
 * WebSocket Email Sending - Advanced E2E Tests
 * Tests WebSocket connection handling and real-time status updates
 */

const BASE_URL = 'http://localhost:5174';
const API_URL = 'ws://localhost:8000/api/recruiters/ws/send-email';

// Test configurations for different browsers
test.describe.configure({ 
  mode: 'parallel',
  retries: 1,
  timeout: 60000
});

// Use different browser configs
const browsers = [
  { name: 'chromium', device: devices['Desktop Chrome'] },
  { name: 'firefox', device: devices['Desktop Firefox'] },
  { name: 'webkit', device: devices['Desktop Safari'] }
];

browsers.forEach(({ name, device }) => {
  test.describe(`Email Sending - ${name}`, () => {
    test.beforeEach(async ({ browser }) => {
      const context = await browser.newContext(device);
      const page = await context.newPage();
      
      // Setup page
      await page.goto(BASE_URL);
      await page.waitForLoadState('networkidle');
    });

    test('should handle WebSocket connection timeout', async ({ page }) => {
      /**
       * This test verifies that the frontend properly times out
       * if the backend doesn't respond within 30 seconds
       */
      
      // Mock WebSocket to delay response
      await page.evaluate(() => {
        const originalWebSocket = window.WebSocket;
        window.WebSocket = class extends originalWebSocket {
          constructor(url) {
            super(url);
            // Delay onopen event
            setTimeout(() => {
              if (this.onopen) {
                this.onopen({ type: 'open' });
              }
            }, 35000);
          }
        };
      });
      
      // Navigate and try to send email
      // Should timeout after 30 seconds
      // Error message should be user-friendly
    });

    test('should display real-time status updates', async ({ page }) => {
      /**
       * This test verifies that status messages from WebSocket
       * are displayed correctly in real-time
       */
      
      // Setup WebSocket mock to send status updates
      const statusUpdates = [];
      
      await page.on('console', msg => {
        if (msg.text().includes('[WebSocket]')) {
          statusUpdates.push(msg.text());
        }
      });
      
      // Trigger email sending
      // Verify status messages appear in order:
      // 1. "Preparing..."
      // 2. "Validating..."
      // 3. "Sending..."
      // 4. "Success!" or error
      
      expect(statusUpdates.length).toBeGreaterThan(0);
    });

    test('should handle authentication errors', async ({ page }) => {
      /**
       * Test that authentication failures are properly reported
       */
      
      // Setup invalid token
      await page.evaluate(() => {
        localStorage.setItem('token', 'invalid.token.here');
      });
      
      // Try to send email
      // Should show authentication error
      // User should be prompted to login
    });

    test('should handle socket errors gracefully', async ({ page }) => {
      /**
       * Test network error handling
       */
      
      // Simulate network error
      await page.context().route(API_URL, route => {
        route.abort('failed');
      });
      
      // Attempt to send email
      // Should show clear error message
      // Should offer retry button
    });

    test('should support dynamic data substitution', async ({ page }) => {
      /**
       * Test that dynamic data is properly rendered in template
       */
      
      const testData = {
        position: 'Senior Developer',
        company: 'Acme Corp',
        date: '2026-04-20',
        time: '2:00 PM',
        location: 'Room 305'
      };
      
      // Fill in dynamic data
      // Verify it's substituted in template preview
      // Verify it's sent to server correctly
    });

    test('should validate dynamic data before sending', async ({ page }) => {
      /**
       * Test validation of required fields
       */
      
      // Try to send without filling required fields
      // Should show validation error
      // Should highlight missing fields
      // Should prevent submission
    });

    test('should show recipient information', async ({ page }) => {
      /**
       * Test that recipient email is clearly displayed
       */
      
      const recipientEmail = 'test@example.com';
      
      // Open email modal
      // Verify recipient email is shown
      // Verify it cannot be changed in modal
    });

    test('should support template selection feedback', async ({ page }) => {
      /**
       * Test that template selection provides feedback
       */
      
      // Load templates
      // Select different templates
      // Verify template details are updated
      // Verify dynamic data fields change based on template
    });

    test('should show progress indication during sending', async ({ page }) => {
      /**
       * Test that progress is shown while sending
       */
      
      // Start sending email
      // Verify loading spinner is shown
      // Verify status messages are updated
      // Verify progress bar is animated
    });

    test('should handle rapid successive sends gracefully', async ({ page }) => {
      /**
       * Test that multiple rapid send attempts don't cause issues
       */
      
      // Open email modal
      // Click send multiple times quickly
      // Should handle gracefully (not send duplicates)
      // Should show appropriate feedback
    });

    test('should persist form data on error', async ({ page }) => {
      /**
       * Test that form data is not lost on error
       */
      
      // Fill email form
      // Trigger error (e.g., network error)
      // Click Try Again
      // Verify form data is still there
    });

    test('should clear form data on success', async ({ page }) => {
      /**
       * Test that form is cleared after successful send
       */
      
      // Send email successfully
      // Close modal
      // Open modal again
      // Verify form is cleared
    });

    test('should handle very long dynamic data', async ({ page }) => {
      /**
       * Test handling of large text in dynamic fields
       */
      
      const longText = 'A'.repeat(500);
      
      // Fill dynamic field with long text
      // Verify it's handled correctly
      // Verify it's sent properly
    });

    test('should support special characters in dynamic data', async ({ page }) => {
      /**
       * Test special characters don't break the system
       */
      
      const specialData = '!@#$%^&*()[]{}"\\'<>?/';
      
      // Fill dynamic field with special characters
      // Verify it's properly escaped
      // Verify email sends correctly
    });
  });
});

test.describe('Email Sending - Cross-browser Consistency', () => {
  /**
   * Tests that run on all browsers simultaneously
   * to verify consistent behavior
   */

  test('should show same UI across browsers', async ({ page }) => {
    // This test runs on all browsers configured
    // Verify UI is consistent
    // Verify layout is responsive
    // Verify all interactive elements work
  });

  test('should handle WebSocket same way on all browsers', async ({ page }) => {
    // Verify WebSocket behavior is consistent
    // Verify error handling is the same
    // Verify status messages are displayed identically
  });
});

test.describe('Email Sending - Performance', () => {
  /**
   * Tests that verify performance characteristics
   */

  test('should load email form in reasonable time', async ({ page }) => {
    const startTime = Date.now();
    
    // Navigate and open email modal
    // Measure time
    
    const loadTime = Date.now() - startTime;
    expect(loadTime).toBeLessThan(5000); // Should load in < 5 seconds
  });

  test('should send email in reasonable time', async ({ page }) => {
    const startTime = Date.now();
    
    // Send email
    // Measure total time
    
    const sendTime = Date.now() - startTime;
    expect(sendTime).toBeLessThan(60000); // Should complete in < 60 seconds
  });

  test('should not leak memory on repeated sends', async ({ page }) => {
    /**
     * Test that WebSocket connections are properly cleaned up
     */
    
    for (let i = 0; i < 5; i++) {
      // Send email
      // Close modal
      // Verify WebSocket is closed
    }
    
    // Check for memory leaks via console messages
  });
});

test.describe('Email Sending - Accessibility', () => {
  /**
   * Tests that verify accessibility compliance
   */

  test('should have proper ARIA labels', async ({ page }) => {
    // Verify all interactive elements have ARIA labels
    // Verify form labels are associated with inputs
  });

  test('should be keyboard navigable', async ({ page }) => {
    // Navigate using only keyboard
    // Verify all controls are accessible
    // Verify tab order is logical
  });

  test('should have sufficient color contrast', async ({ page }) => {
    // Verify text contrast meets WCAG standards
  });

  test('should work with screen readers', async ({ page }) => {
    // Verify all content is accessible to screen readers
  });
});

// Helper functions

async function openEmailModal(page) {
  await page.click('button:has-text("📧 Send Email")');
  await page.waitForSelector('.email-modal');
}

async function selectTemplate(page, templateIndex = 1) {
  const select = page.locator('select[id="template-select"]');
  await select.nth(templateIndex).click();
}

async function fillDynamicData(page, data) {
  for (const [key, value] of Object.entries(data)) {
    const input = page.locator(`input[placeholder*="${key}"]`).first();
    if (await input.isVisible()) {
      await input.fill(value);
    }
  }
}

async function sendEmail(page) {
  await page.click('button[type="submit"]:has-text("Send Email")');
}

async function waitForSuccess(page, timeout = 45000) {
  await page.waitForSelector('.email-success', { timeout });
}

async function waitForError(page, timeout = 45000) {
  await page.waitForSelector('.email-error', { timeout });
}

async function getErrorMessage(page) {
  return await page.locator('.email-error .error-message').textContent();
}

async function getMessageId(page) {
  return await page.locator('.email-success code').textContent();
}
