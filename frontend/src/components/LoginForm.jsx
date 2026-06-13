import { useState } from 'react';
import './LoginForm.css';

export default function LoginForm({ onLogin, loading }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (username && password) {
      onLogin(username, password);
    }
  };

  const quickLogin = (u, p) => {
    setUsername(u);
    setPassword(p);
    onLogin(u, p);
  };

  return (
    <form className="login-form" onSubmit={handleSubmit}>
      <div className="form-group">
        <label htmlFor="username">Username</label>
        <input
          id="username"
          type="text"
          placeholder="e.g., dr.mehta"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          disabled={loading}
          required
        />
      </div>

      <div className="form-group">
        <label htmlFor="password">Password</label>
        <input
          id="password"
          type="password"
          placeholder="e.g., doctor123"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          disabled={loading}
          required
        />
      </div>

      <button type="submit" className="login-btn" disabled={loading}>
        {loading ? 'Logging in...' : 'Login'}
      </button>

      <div className="quick-login">
        <p>Quick Login:</p>
        <div className="quick-buttons">
          <button
            type="button"
            onClick={() => quickLogin('dr.mehta', 'doctor123')}
            disabled={loading}
            title="Doctor"
          >
            👨‍⚕️
          </button>
          <button
            type="button"
            onClick={() => quickLogin('nurse.priya', 'nurse123')}
            disabled={loading}
            title="Nurse"
          >
            👩‍⚕️
          </button>
          <button
            type="button"
            onClick={() => quickLogin('billing.ravi', 'billing123')}
            disabled={loading}
            title="Billing Executive"
          >
            💼
          </button>
          <button
            type="button"
            onClick={() => quickLogin('tech.anand', 'tech123')}
            disabled={loading}
            title="Technician"
          >
            🔧
          </button>
          <button
            type="button"
            onClick={() => quickLogin('admin.sys', 'admin123')}
            disabled={loading}
            title="Admin"
          >
            🔐
          </button>
        </div>
      </div>
    </form>
  );
}
