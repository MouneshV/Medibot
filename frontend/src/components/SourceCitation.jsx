import './SourceCitation.css';

export default function SourceCitation({ source }) {
  const getCollectionIcon = (collection) => {
    const icons = {
      clinical: '🔬',
      nursing: '👩‍⚕️',
      billing: '💰',
      equipment: '⚙️',
      general: '📄',
    };
    return icons[collection] || '📄';
  };

  return (
    <div className="source-citation">
      <div className="source-icon">{getCollectionIcon(source.collection)}</div>
      <div className="source-info">
        <div className="source-document">
          <strong>{source.source_document}</strong>
        </div>
        <div className="source-section">{source.section_title}</div>
        <div className="source-collection">
          Collection: <span className="badge">{source.collection}</span>
        </div>
      </div>
    </div>
  );
}
