import React, { useState, useEffect } from 'react';
import { useWebSocketEmailSend } from '../hooks/useWebSocketEmailSend';
import recruiterService from '../services/recruiterService';
import './EmailSendLive.css';

/**
 * Helper function to safely parse placeholders from template
 * Handles both string (JSON) and array formats, as well as dictionaries
 */
const getParsedPlaceholders = (placeholders) => {
  if (!placeholders) return [];
  
  // If it's already an array, return it
  if (Array.isArray(placeholders)) return placeholders;
  
  // If it's a string, try to parse it
  if (typeof placeholders === 'string') {
    try {
      const parsed = JSON.parse(placeholders);
      // If parsed result is an array, return it
      if (Array.isArray(parsed)) return parsed;
      // If parsed result is an object/dictionary, extract the keys
      if (typeof parsed === 'object' && parsed !== null) {
        return Object.keys(parsed);
      }
      return [];
    } catch (e) {
      console.warn('Failed to parse placeholders:', e);
      return [];
    }
  }
  
  // If it's an object/dictionary, extract the keys
  if (typeof placeholders === 'object' && placeholders !== null) {
    return Object.keys(placeholders);
  }
  
  return [];
};

/**
 * Component for sending emails with templates and live status updates.
 * 
 * Props:
 * - candidateId: UUID of the candidate to send email to
 * - candidateName: Name of the candidate (for display)
 * - candidateEmail: Email address of the candidate
 * - token: JWT authentication token
 * - onSuccess: Callback when email is sent successfully
 * - onError: Callback when email sending fails
 * - onClose: Callback to close the modal/dialog
 */
export const EmailSendLive = ({
  candidateId,
  candidateName,
  candidateEmail,
  token,
  onSuccess,
  onError,
  onClose
}) => {
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [templateLoading, setTemplateLoading] = useState(true);
  const [dynamicData, setDynamicData] = useState({});
  const [hasStarted, setHasStarted] = useState(false);
  
  const { sendEmail, status, message, messageId, error, isLoading, close } = useWebSocketEmailSend();

  // Fetch email templates on mount
  useEffect(() => {
    const fetchTemplates = async () => {
      try {
        const response = await recruiterService.getEmailTemplates();
        setTemplates(response.data.templates || []);
        if (response.data.templates && response.data.templates.length > 0) {
          setSelectedTemplate(response.data.templates[0]);
        }
      } catch (err) {
        console.error('Failed to load templates:', err);
        alert('Failed to load email templates. Please try again.');
      } finally {
        setTemplateLoading(false);
      }
    };

    fetchTemplates();
  }, []);

  // Initialize dynamic data when template changes
  useEffect(() => {
    if (selectedTemplate) {
      const placeholders = getParsedPlaceholders(selectedTemplate.placeholders);
      const initialData = {};
      placeholders.forEach(placeholder => {
        initialData[placeholder] = '';
      });
      setDynamicData(initialData);
    }
  }, [selectedTemplate]);

  const handleSendEmail = async (e) => {
    e.preventDefault();
    
    if (!selectedTemplate) {
      alert('Please select an email template');
      return;
    }

    // Verify all required fields are filled
    const placeholders = getParsedPlaceholders(selectedTemplate.placeholders);
    const missingFields = placeholders.filter(p => !dynamicData[p] || dynamicData[p].trim() === '');
    
    if (missingFields.length > 0) {
      alert(`Please fill in all required fields: ${missingFields.join(', ')}`);
      return;
    }

    setHasStarted(true);

    try {
      const result = await sendEmail(
        candidateId,
        candidateEmail,
        selectedTemplate.id,
        dynamicData,
        token
      );
      
      if (onSuccess) {
        onSuccess(result);
      }
    } catch (err) {
      console.error('Email sending failed:', err);
      if (onError) {
        onError(err);
      }
    }
  };

  if (templateLoading) {
    return (
      <div className="email-modal-overlay" onClick={onClose}>
        <div className="email-modal" onClick={(e) => e.stopPropagation()}>
          <div className="email-modal-header">
            <h2>📧 Send Email</h2>
            <button 
              className="email-modal-close" 
              onClick={onClose}
              aria-label="Close modal"
            >
              ✕
            </button>
          </div>
          <div className="email-modal-body">
            <div className="email-loading">
              <div className="spinner"></div>
              <p>Loading email templates...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Form view - before sending
  if (!hasStarted) {
    return (
      <div className="email-modal-overlay" onClick={onClose}>
        <div className="email-modal" onClick={(e) => e.stopPropagation()}>
          <div className="email-modal-header">
            <h2>📧 Send Email to {candidateName}</h2>
            <button 
              className="email-modal-close" 
              onClick={onClose}
              aria-label="Close modal"
            >
              ✕
            </button>
          </div>
          
          <div className="email-modal-body">
            <form onSubmit={handleSendEmail}>
              {/* Template Selection */}
              <div className="form-group">
                <label htmlFor="template-select">
                  Select Email Template <span className="required">*</span>
                </label>
                <select
                  id="template-select"
                  value={selectedTemplate?.id || ''}
                  onChange={(e) => {
                    const selected = templates.find(t => t.id === e.target.value);
                    setSelectedTemplate(selected);
                  }}
                  className="form-input"
                  required
                >
                  <option value="">-- Choose a template --</option>
                  {templates.map((template) => (
                    <option key={template.id} value={template.id}>
                      {template.name}
                    </option>
                  ))}
                </select>
                {selectedTemplate && (
                  <p className="template-description">{selectedTemplate.description}</p>
                )}
              </div>

              {/* Template Preview */}
              {selectedTemplate && (
                <div className="template-preview">
                  <h4>Template Preview</h4>
                  <div className="preview-content">
                    <div className="preview-subject">
                      <strong>Subject:</strong> {selectedTemplate.subject}
                    </div>
                    <div className="preview-body">
                      <strong>Body:</strong>
                      <p>{selectedTemplate.body}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Dynamic Data Fields */}
              {selectedTemplate && (() => {
                const placeholders = getParsedPlaceholders(selectedTemplate.placeholders);
                return placeholders && placeholders.length > 0 && (
                  <div className="dynamic-data-section">
                    <h4>Fill in the Details</h4>
                    {placeholders.map((placeholder) => (
                      <div key={placeholder} className="form-group">
                        <label htmlFor={`data-${placeholder}`}>
                          {placeholder.replace(/_/g, ' ').toLowerCase()} <span className="required">*</span>
                        </label>
                        <input
                          id={`data-${placeholder}`}
                          type="text"
                          value={dynamicData[placeholder] || ''}
                          onChange={(e) => setDynamicData({
                            ...dynamicData,
                            [placeholder]: e.target.value
                          })}
                          className="form-input"
                          placeholder={`Enter ${placeholder.replace(/_/g, ' ').toLowerCase()}`}
                          required
                        />
                      </div>
                    ))}
                  </div>
                );
              })()}

              {/* Recipient Info */}
              <div className="recipient-info">
                <p><strong>Sending to:</strong> {candidateEmail}</p>
              </div>

              {/* Buttons */}
              <div className="form-actions">
                <button 
                  type="button" 
                  className="btn btn-secondary" 
                  onClick={onClose}
                >
                  Cancel
                </button>
                <button 
                  type="submit" 
                  className="btn btn-primary"
                  disabled={!selectedTemplate || templates.length === 0}
                >
                  Send Email
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    );
  }

  // Success view
  if (status === 'success') {
    return (
      <div className="email-modal-overlay" onClick={onClose}>
        <div className="email-modal" onClick={(e) => e.stopPropagation()}>
          <div className="email-modal-header">
            <h2>✅ Email Sent Successfully</h2>
            <button 
              className="email-modal-close" 
              onClick={onClose}
              aria-label="Close modal"
            >
              ✕
            </button>
          </div>
          
          <div className="email-modal-body">
            <div className="email-success">
              <div className="success-icon">✓</div>
              <h3>Success!</h3>
              <p>Email sent to <strong>{candidateEmail}</strong></p>
              <div className="message-id">
                <p><strong>Message ID:</strong></p>
                <code>{messageId}</code>
              </div>
              <p className="success-message">{message}</p>
            </div>

            <div className="form-actions">
              <button 
                type="button" 
                className="btn btn-primary" 
                onClick={onClose}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Error view
  if (status === 'error') {
    return (
      <div className="email-modal-overlay" onClick={onClose}>
        <div className="email-modal" onClick={(e) => e.stopPropagation()}>
          <div className="email-modal-header">
            <h2>❌ Error Sending Email</h2>
            <button 
              className="email-modal-close" 
              onClick={onClose}
              aria-label="Close modal"
            >
              ✕
            </button>
          </div>
          
          <div className="email-modal-body">
            <div className="email-error">
              <div className="error-icon">✕</div>
              <h3>Failed</h3>
              <p className="error-message">{error || message}</p>
            </div>

            <div className="form-actions">
              <button 
                type="button" 
                className="btn btn-secondary" 
                onClick={() => {
                  setHasStarted(false);
                  setDynamicData({});
                }}
              >
                Try Again
              </button>
              <button 
                type="button" 
                className="btn btn-primary" 
                onClick={onClose}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Sending view (loading)
  return (
    <div className="email-modal-overlay">
      <div className="email-modal" onClick={(e) => e.stopPropagation()}>
        <div className="email-modal-header">
          <h2>📧 Sending Email</h2>
        </div>
        
        <div className="email-modal-body">
          <div className="email-sending">
            <div className="spinner"></div>
            <h3>
              {status === 'preparing' && 'Preparing...'}
              {status === 'validating' && 'Validating...'}
              {status === 'sending' && 'Sending Email...'}
              {status === 'idle' && 'Connecting...'}
            </h3>
            <p className="status-message">{message || 'Connecting to email service...'}</p>
            <div className="progress-bar">
              <div className="progress-fill"></div>
            </div>
            
            {/* Show detailed status info */}
            <div className="sending-details">
              <p><strong>To:</strong> {candidateEmail}</p>
              <p><strong>Template:</strong> {selectedTemplate?.name}</p>
              <p className="hint">This usually takes 5-30 seconds...</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EmailSendLive;
