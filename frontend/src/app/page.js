'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import LoginForm from '@/components/LoginForm';
import './login.css';

export default function LoginPage() {
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleLogin = async (username, password) => {
    setError(null);
    setLoading(true);

    try {
      const response = await api.login(username, password);
      
      // Store token and user info
      localStorage.setItem('token', response.token);
      localStorage.setItem('role', response.role);
      localStorage.setItem('username', response.username);
      localStorage.setItem('displayName', response.display_name);
      localStorage.setItem('collections', JSON.stringify(response.collections));

      // Redirect to chat
      router.push('/chat');
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-header">
          <h1>🏥 MediBot</h1>
          <p>Intelligent Medical Assistant for MediAssist Health Network</p>
        </div>

        <LoginForm onLogin={handleLogin} loading={loading} />

        {error && <div className="error-message">{error}</div>}

        <div className="demo-credentials">
          <h3>Demo Accounts</h3>
          <table>
            <thead>
              <tr>
                <th>Role</th>
                <th>Username</th>
                <th>Password</th>
                <th>Access</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>👨‍⚕️ Doctor</td>
                <td><code>dr.mehta</code></td>
                <td><code>doctor123</code></td>
                <td>Clinical, Nursing, General</td>
              </tr>
              <tr>
                <td>👩‍⚕️ Nurse</td>
                <td><code>nurse.priya</code></td>
                <td><code>nurse123</code></td>
                <td>Nursing, General</td>
              </tr>
              <tr>
                <td>💼 Billing Executive</td>
                <td><code>billing.ravi</code></td>
                <td><code>billing123</code></td>
                <td>Billing, General</td>
              </tr>
              <tr>
                <td>🔧 Technician</td>
                <td><code>tech.anand</code></td>
                <td><code>tech123</code></td>
                <td>Equipment, General</td>
              </tr>
              <tr>
                <td>🔐 Admin</td>
                <td><code>admin.sys</code></td>
                <td><code>admin123</code></td>
                <td>All Collections</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div className="security-note">
          <strong>🔒 Security Note:</strong> RBAC is enforced at the retrieval layer. Even with adversarial prompts, users cannot access documents outside their assigned collections.
        </div>
      </div>
    </div>
  );
}
