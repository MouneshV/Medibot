import './MessageBubble.css';

export default function MessageBubble({ type, content, retrievalType }) {
  return (
    <div className={`message-bubble ${type}`}>
      <div className="message-content">{content}</div>
      {retrievalType && (
        <div className={`retrieval-badge ${retrievalType}`}>
          {retrievalType === 'hybrid_rag' ? '🔍 Hybrid RAG' : '💾 SQL RAG'}
        </div>
      )}
    </div>
  );
}
