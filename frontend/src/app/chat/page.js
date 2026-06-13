'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import ChatInterface from '@/components/ChatInterface';
import RoleBadge from '@/components/RoleBadge';
import './chat.css';

export default function ChatPage() {
  const [userInfo, setUserInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [mounted, setMounted] = useState(false);
  const router = useRouter();

  useEffect(() => {
    setMounted(true);
    
    // Check if user is logged in
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/');
      return;
    }

    // Load user info from localStorage
    const role = localStorage.getItem('role');
    const username = localStorage.getItem('username');
    const displayName = localStorage.getItem('displayName');
    const collections = JSON.parse(localStorage.getItem('collections') || '[]');

    setUserInfo({
      username,
      role,
      displayName,
      collections,
    });

    setLoading(false);
  }, [router]);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('role');
    localStorage.removeItem('username');
    localStorage.removeItem('displayName');
    localStorage.removeItem('collections');
    router.push('/');
  };

  if (!mounted || loading) {
    return (
      <div className="chat-page loading">
        <div className="spinner"></div>
        <p>Loading...</p>
      </div>
    );
  }

  if (!userInfo) {
    return null;
  }

  return (
    <div className="chat-page">
      <header className="chat-header">
        <div className="header-left">
          <h1>🏥 MediBot</h1>
          <p className="subtitle">Medical Assistant for MediAssist</p>
        </div>
        <div className="header-right">
          <RoleBadge role={userInfo.role} displayName={userInfo.displayName} />
          <button onClick={handleLogout} className="logout-btn">
            Logout
          </button>
        </div>
      </header>

      <div className="chat-wrapper">
        <aside className="chat-sidebar">
          <div className="sidebar-section">
            <h3>Your Access</h3>
            <div className="collections-list">
              {userInfo.collections.length > 0 ? (
                userInfo.collections.map((collection) => (
                  <div key={collection} className="collection-badge">
                    📄 {collection.charAt(0).toUpperCase() + collection.slice(1)}
                  </div>
                ))
              ) : (
                <p className="no-collections">No collections available</p>
              )}
            </div>
          </div>

          <div className="sidebar-section">
            <h3>How It Works</h3>
            <ul className="how-it-works">
              <li>
                <strong>Natural Questions:</strong> Ask anything about medical procedures, policies, or billing.
              </li>
              <li>
                <strong>RBAC Protected:</strong> Only see documents your role allows.
              </li>
              <li>
                <strong>Source Citations:</strong> Every answer shows its sources.
              </li>
              <li>
                <strong>Hybrid Search:</strong> Semantic + keyword retrieval.
              </li>
            </ul>
          </div>
        </aside>

        <main className="chat-main">
          <ChatInterface userRole={userInfo.role} />
        </main>
      </div>
    </div>
  );
}
