import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import './AIChatBox.css';

// Backend API URL
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

/**
 * AI Chat Sidebar Component
 * - Opens/closes with icon click
 * - Session memory for conversation context
 * - Long-term memory for conversation history
 * - Role-based prompts (Candidate vs Recruiter)
 */

export function AIChatBox() {
  const { user } = useAuth();
  
  // State Management
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionMemory, setSessionMemory] = useState([]);
  const [chatHistory, setChatHistory] = useState([]);
  const [conversationId, setConversationId] = useState(null);
  const messagesEndRef = useRef(null);

  // Auto-scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Load chat history on mount
  useEffect(() => {
    if (user && isOpen) {
      loadChatHistory();
      initializeSystemMessage();
    }
  }, [user, isOpen]);

  /**
   * Initialize system message based on user role
   */
  const initializeSystemMessage = () => {
    if (!messages.length) {
      const roleInfo = user?.role === 'recruiter' 
        ? 'I\'m here to help you find and analyze candidates.'
        : 'I\'m here to help you with job opportunities and application insights.';
      
      const systemMsg = {
        id: 'system-init',
        role: 'assistant',
        content: roleInfo,
        timestamp: new Date(),
        type: 'system'
      };
      
      setMessages([systemMsg]);
      
      // Initialize session memory with user context
      setSessionMemory([{
        type: 'system_context',
        value: {
          user_role: user?.role,
          user_id: user?.id,
          user_name: user?.full_name,
          timestamp: new Date()
        }
      }]);
    }
  };

  /**
   * Load conversation history from backend
   */
  const loadChatHistory = async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        console.log('No token found, skipping chat history load');
        setMessages([]);  // Clear messages if not authenticated
        return;
      }
      const response = await fetch(`${API_BASE_URL}/ai/chat/history`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setChatHistory(data.conversations);
        
        // Load latest conversation if exists
        if (data.conversations && data.conversations.length > 0) {
          const latestConv = data.conversations[0];
          setConversationId(latestConv.id);
          setMessages(latestConv.messages || []);
          
          // Rebuild session memory from conversation
          const memoryPoints = latestConv.messages
            .filter(m => m.memory_context)
            .map(m => m.memory_context);
          setSessionMemory(memoryPoints);
        } else {
          // No conversations for this user - clear old messages
          setMessages([]);
          setConversationId(null);
          setSessionMemory([]);
        }
      } else {
        // Error loading - clear messages to prevent data leak
        setMessages([]);
      }
    } catch (error) {
      console.error('Error loading chat history:', error);
      setMessages([]);  // Clear on error to prevent data leak
    }
  };

  /**
   * Send message and get AI response
   */
  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    // Add user message
    const userMessage = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: inputValue,
      timestamp: new Date(),
      type: 'user'
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      // Build context for LLM
      const context = buildContext(inputValue);

      // Send to backend with trailing slash
      const token = localStorage.getItem('access_token');
      if (!token) {
        setIsLoading(false);
        const errorMsg = {
          id: `msg-${Date.now()}-error`,
          role: 'assistant',
          content: 'Authentication required. Please login first.',
          timestamp: new Date(),
          type: 'error'
        };
        setMessages(prev => [...prev, errorMsg]);
        return;
      }
      
      const response = await fetch(`${API_BASE_URL}/ai/chat/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          message: inputValue,
          conversation_id: conversationId,
          context: context,
          user_role: user?.role,
          session_memory: sessionMemory
        })
      });

      const data = await response.json();

      if (data.success) {
        // Add AI response
        const aiMessage = {
          id: `msg-${Date.now()}-ai`,
          role: 'assistant',
          content: data.response,
          timestamp: new Date(),
          type: 'assistant',
          memory_context: data.memory_context // Long-term memory
        };

        setMessages(prev => [...prev, aiMessage]);
        setConversationId(data.conversation_id);

        // Update session memory
        if (data.memory_context) {
          setSessionMemory(prev => [...prev, data.memory_context]);
        }
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMsg = {
        id: `msg-${Date.now()}-error`,
        role: 'assistant',
        content: 'Sorry, I had an error. Please try again.',
        timestamp: new Date(),
        type: 'error'
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Build context for AI based on user role and conversation
   */
  const buildContext = (userInput) => {
    const context = {
      user_role: user?.role,
      user_id: user?.id,
      conversation_length: messages.length,
      recent_topics: extractTopics(sessionMemory),
      user_intent: detectIntent(userInput)
    };

    if (user?.role === 'recruiter') {
      context.recruiter_context = {
        can_search_candidates: true,
        can_view_applications: true,
        can_view_resumes: true
      };
    } else {
      context.candidate_context = {
        can_view_jobs: true,
        can_view_applications: true,
        can_view_resume_score: true
      };
    }

    return context;
  };

  /**
   * Extract conversation topics from session memory
   */
  const extractTopics = (memory) => {
    return memory
      .filter(m => m.type === 'topic')
      .map(m => m.value)
      .slice(-5); // Last 5 topics
  };

  /**
   * Detect user intent (search, analyze, etc.)
   */
  const detectIntent = (input) => {
    const lowerInput = input.toLowerCase();
    
    if (lowerInput.includes('find') || lowerInput.includes('search')) {
      return 'search';
    } else if (lowerInput.includes('analyze') || lowerInput.includes('score')) {
      return 'analyze';
    } else if (lowerInput.includes('help') || lowerInput.includes('how')) {
      return 'help';
    } else if (lowerInput.includes('job') || lowerInput.includes('application')) {
      return 'job_inquiry';
    }
    return 'general';
  };

  /**
   * Clear chat history
   */
  const handleClearChat = () => {
    if (window.confirm('Clear conversation? This cannot be undone.')) {
      setMessages([]);
      setSessionMemory([]);
      setConversationId(null);
      initializeSystemMessage();
    }
  };

  /**
   * Get quick action buttons based on role
   */
  const getQuickActions = () => {
    if (user?.role === 'recruiter') {
      return [
        { label: '🔍 Search Candidates', message: 'Help me find senior Python developers' },
        { label: '📊 Analyze Resume', message: 'Analyze this candidate\'s resume' },
        { label: '⭐ Top Matches', message: 'Show me top candidates for Python role' },
        { label: '💡 Tips', message: 'Give me tips on recruiting' }
      ];
    } else {
      return [
        { label: '🎯 Find Jobs', message: 'Show me job opportunities' },
        { label: '📋 Resume Score', message: 'What\'s my resume score?' },
        { label: '💼 Applications', message: 'Tell me about my applications' },
        { label: '🤝 Advice', message: 'Give me tips to improve my profile' }
      ];
    }
  };

  if (!user) return null;

  return (
    <>
      {/* Chat Toggle Button */}
      <div 
        className="ai-chat-toggle-btn" 
        onClick={() => setIsOpen(!isOpen)} 
        title="AI Assistant"
        data-testid="ai-chat-toggle-btn"
      >
        <span className="toggle-icon">🤖</span>
        {isOpen && <span className="close-icon">✕</span>}
      </div>

      {/* Chat Sidebar */}
      {isOpen && (
        <div className="ai-chat-container" data-testid="ai-chat-container">
          <div className="chat-header" data-testid="chat-header">
            <h3>🤖 AI Assistant</h3>
            <p className="role-badge" data-testid="role-badge">{user?.role === 'recruiter' ? '👔 Recruiter Mode' : '🎓 Candidate Mode'}</p>
            <button className="clear-btn" onClick={handleClearChat} title="Clear chat" data-testid="clear-chat-btn">🗑️</button>
          </div>

          {/* Messages Area */}
          <div className="chat-messages" data-testid="chat-messages">
            {messages.length === 0 ? (
              <div className="empty-state">
                <p>👋 How can I help you today?</p>
              </div>
            ) : (
              messages.map(msg => (
                <div 
                  key={msg.id} 
                  className={`message message-${msg.role}`}
                  data-testid="message-item"
                  data-role={msg.role}
                >
                  <div className="message-avatar">
                    {msg.role === 'user' ? '👤' : '🤖'}
                  </div>
                  <div className="message-content">
                    <p>{msg.content}</p>
                    <span className="message-time" data-testid="message-timestamp">
                      {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                </div>
              ))
            )}
            {isLoading && (
              <div className="message message-assistant" data-testid="typing-animation">
                <div className="message-avatar">🤖</div>
                <div className="message-content typing">
                  <span></span><span></span><span></span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Actions */}
          {messages.length <= 1 && (
            <div className="quick-actions" data-testid="quick-actions">
              {getQuickActions().map((action, idx) => (
                <button
                  key={idx}
                  className="quick-action-btn"
                  onClick={() => {
                    setInputValue(action.message);
                  }}
                  data-testid="quick-action-btn"
                >
                  {action.label}
                </button>
              ))}
            </div>
          )}

          {/* Input Area */}
          <form className="chat-input-form" onSubmit={handleSendMessage} data-testid="chat-input-form">
            <input
              type="text"
              value={inputValue}
              onChange={e => setInputValue(e.target.value)}
              placeholder={user?.role === 'recruiter' 
                ? "Ask me to find candidates..." 
                : "Ask me about jobs..."}
              disabled={isLoading}
              className="chat-input"
              data-testid="chat-input"
            />
            <button type="submit" disabled={isLoading || !inputValue.trim()} className="send-btn" data-testid="send-btn">
              ➤
            </button>
          </form>

          {/* Memory Status */}
          <div className="memory-status" data-testid="memory-status">
            <small>
              <span data-testid="session-memory-badge">Session: {sessionMemory.length}</span> | History: {chatHistory.length}
            </small>
          </div>
        </div>
      )}
    </>
  );
}

export default AIChatBox;
