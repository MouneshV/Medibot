import { useState, useRef, useEffect } from 'react';
import { api } from '@/lib/api';
import MessageBubble from './MessageBubble';
import SourceCitation from './SourceCitation';
import './ChatInterface.css';

export default function ChatInterface({ userRole }) {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'bot',
      content: `Hello! I'm MediBot, your intelligent medical assistant. I can help you find information from our knowledge base including clinical protocols, nursing procedures, billing guides, and equipment manuals.

As a **${userRole}**, you have access to the relevant documents for your role.

What would you like to know?`,
      sources: [],
      retrievalType: null,
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputValue.trim() || loading) return;

    // Add user message
    const userMessage = {
      id: messages.length + 1,
      type: 'user',
      content: inputValue,
      sources: [],
    };
    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setError(null);
    setLoading(true);

    try {
      // Call API
      const response = await api.chat(inputValue);

      // Add bot response
      const botMessage = {
        id: messages.length + 2,
        type: 'bot',
        content: response.answer,
        sources: response.sources || [],
        retrievalType: response.retrieval_type,
      };
      setMessages((prev) => [...prev, botMessage]);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error sending message. Please try again.');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-interface">
      <div className="messages-container">
        {messages.map((message) => (
          <div key={message.id} className={`message-wrapper ${message.type}`}>
            <MessageBubble
              type={message.type}
              content={message.content}
              retrievalType={message.retrievalType}
            />
            {message.sources && message.sources.length > 0 && (
              <div className="sources-section">
                <div className="sources-header">
                  📚 Sources ({message.sources.length}):
                </div>
                {message.sources.map((source, idx) => (
                  <SourceCitation key={idx} source={source} />
                ))}
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="message-wrapper bot">
            <div className="message-bubble bot">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
        {error && (
          <div className="message-wrapper bot">
            <div className="message-bubble error">
              <strong>Error:</strong> {error}
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form className="input-form" onSubmit={handleSendMessage}>
        <div className="input-wrapper">
          <input
            type="text"
            placeholder="Ask me anything..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            disabled={loading}
            className="message-input"
          />
          <button type="submit" disabled={loading || !inputValue.trim()} className="send-btn">
            {loading ? '⏳' : '➤'}
          </button>
        </div>
      </form>
    </div>
  );
}
