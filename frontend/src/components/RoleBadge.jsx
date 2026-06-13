import './RoleBadge.css';

export default function RoleBadge({ role, displayName }) {
  const roleIcons = {
    doctor: '👨‍⚕️',
    nurse: '👩‍⚕️',
    billing_executive: '💼',
    technician: '🔧',
    admin: '🔐',
  };

  const roleColors = {
    doctor: '#3b82f6',
    nurse: '#22c55e',
    billing_executive: '#a855f7',
    technician: '#f97316',
    admin: '#ef4444',
  };

  const icon = roleIcons[role] || '👤';
  const color = roleColors[role] || '#999';

  return (
    <div className="role-badge" style={{ borderColor: color }}>
      <span className="role-icon">{icon}</span>
      <div className="role-info">
        <div className="role-label">{role.replace('_', ' ').toUpperCase()}</div>
        <div className="role-name">{displayName}</div>
      </div>
    </div>
  );
}
