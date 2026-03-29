import { useState, useCallback, useRef } from 'react';

/**
* Custom hook for WebSocket email sending with real-time status updates.
* 
* Usage:
* const { sendEmail, status, message, messageId, error, isLoading } = useWebSocketEmailSend();
* 
* await sendEmail(candidateId, subject, body);
*/
export const useWebSocketEmailSend = () => {
  const [status, setStatus] = useState('idle'); // idle, sending, success, error
  const [message, setMessage] = useState('');
  const [messageId, setMessageId] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const wsRef = useRef(null);
  const timeoutRef = useRef(null);
  const messageHandledRef = useRef(false);

  const sendEmail = useCallback((candidateId, candidateEmail, templateId, dynamicData, token) => {
    return new Promise((resolve, reject) => {
      setIsLoading(true);
      setStatus('idle');
      setMessage('');
      setError('');
      setMessageId('');
      messageHandledRef.current = false;

      try {
        // Validate inputs
        if (!token) {
          console.error('[WebSocket] No token provided');
          setStatus('error');
          setError('Authentication token missing - try logging in again');
          setIsLoading(false);
          reject(new Error('No authentication token provided'));
          return;
        }

        // Get WebSocket protocol (ws or wss based on location protocol)
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';

        // Get backend host from environment or default to current host
        // Use VITE_API_URL or window.location.host for relative paths
        const apiUrl = import.meta.env.VITE_API_URL || '/api';
        const backendHost = apiUrl.startsWith('http') ? new URL(apiUrl).host : window.location.host;

        // Serialize dynamic data to JSON string
        const dynamicDataStr = JSON.stringify(dynamicData || {});

        // Build WebSocket URL with proper escaping using backend host
        const wsUrl = `${wsProtocol}//${backendHost}/api/recruiters/ws/send-email/${candidateId}?template_id=${encodeURIComponent(templateId)}&candidate_email=${encodeURIComponent(candidateEmail)}&dynamic_data=${encodeURIComponent(dynamicDataStr)}&token=${token}`;

        console.log('[WebSocket] Connection details:');
        console.log('  URL:', wsUrl.replace(token, 'TOKEN').replace(dynamicDataStr, 'DATA'));
        console.log('  Protocol:', wsProtocol);
        console.log('  Backend Host:', backendHost);
        console.log('  Candidate ID:', candidateId);
        console.log('  Template ID:', templateId);
        console.log('  Candidate Email:', candidateEmail);
        console.log('  Token length:', token.length);

        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        // Set timeout for connection establishment (30 seconds)
        timeoutRef.current = setTimeout(() => {
          if (ws && ws.readyState !== WebSocket.CLOSED) {
            console.error('[WebSocket] ✗ Connection timeout - no response from server');
            ws.close();
            setStatus('error');
            setError('Connection timeout - server not responding. Please try again.');
            setIsLoading(false);
            reject(new Error('WebSocket connection timeout'));
          }
        }, 30000);

        ws.onopen = () => {
          console.log('[WebSocket] ✓ Connected to email service');
          setMessage('Connected. Preparing to send email...');
        };

        ws.onmessage = (event) => {
          console.log('[WebSocket] 📨 RAW MESSAGE RECEIVED:', event.data);
          try {
            const data = JSON.parse(event.data);
            console.log('[WebSocket] ✓ Message received:', data);

            const { status: msgStatus, message: msgText, message_id, error: msgError } = data;

            console.log('[WebSocket] Setting status to:', msgStatus);
            setStatus(msgStatus);
            setMessage(msgText);
            console.log('[WebSocket] State updated - status:', msgStatus, 'message:', msgText);

            if (msgStatus === 'sending') {
              console.log('[WebSocket] Status: sending...');
              // Keep loading during sending
            } else if (msgStatus === 'success') {
              console.log('[WebSocket] Status: success!', message_id);
              clearTimeout(timeoutRef.current);
              messageHandledRef.current = true;
              setMessageId(message_id);
              setStatus('success');
              setIsLoading(false);
              console.log('[WebSocket] States set: messageId, status=success, isLoading=false');
              ws.close();
              // Wait for React to render the success state before resolving
              setTimeout(() => {
                console.log('[WebSocket] Resolving promise after 1500ms delay');
                resolve({ success: true, message_id });
              }, 1500);
            } else if (msgStatus === 'error') {
              console.error('[WebSocket] Status: error -', msgError);
              clearTimeout(timeoutRef.current);
              messageHandledRef.current = true;
              setError(msgError || msgText);
              setIsLoading(false);
              ws.close();
              reject(new Error(msgError || msgText));
            }
          } catch (err) {
            console.error('[WebSocket] Failed to parse message:', err);
            setStatus('error');
            setError('Failed to parse server response');
            setIsLoading(false);
            clearTimeout(timeoutRef.current);
            ws.close();
            reject(err);
          }
        };

        ws.onerror = (event) => {
          console.error('[WebSocket] ✗ Connection error:', event);
          console.error('[WebSocket] Error details:', {
            type: event.type,
            bubbles: event.bubbles,
            cancelable: event.cancelable
          });
          clearTimeout(timeoutRef.current);
          setStatus('error');
          setError('WebSocket connection error. Please check your network and try again.');
          setIsLoading(false);
          reject(new Error('WebSocket connection error'));
        };

        ws.onclose = (event) => {
          console.log('[WebSocket] 🔌 Connection closed:', {
            code: event.code,
            reason: event.reason,
            wasClean: event.wasClean,
            messageHandled: messageHandledRef.current
          });
          clearTimeout(timeoutRef.current);

          // If connection closed unexpectedly (not after success/error was handled)
          if (!messageHandledRef.current) {
            console.error('[WebSocket] ✗ Connection closed before message was handled');
            setStatus('error');
            setError(`Connection closed unexpectedly (code: ${event.code}). Please try again.`);
            setIsLoading(false);
            reject(new Error('WebSocket connection closed unexpectedly'));
          }
          wsRef.current = null;
        };
      } catch (err) {
        console.error('[WebSocket] ✗ Error creating connection:', err);
        clearTimeout(timeoutRef.current);
        setStatus('error');
        setError(err.message || 'Failed to establish connection');
        setIsLoading(false);
        reject(err);
      }
    });
  }, [isLoading, status]);

  const close = useCallback(() => {
    clearTimeout(timeoutRef.current);
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.close();
    }
  }, []);

  return {
    sendEmail,
    status,
    message,
    messageId,
    error,
    isLoading,
    close
  };
};
 