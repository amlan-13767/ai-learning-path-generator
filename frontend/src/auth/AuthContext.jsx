/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext, useEffect, useState } from 'react';
import { getCurrentUser } from '../lib/api';
import { loginWithPassword, logoutFromFlask, registerWithPassword } from './authApi';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const refreshUser = async () => {
    try {
      const response = await getCurrentUser();
      const nextUser = response.authenticated ? response.user : null;
      setUser(nextUser);
      return nextUser;
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { refreshUser().catch(() => setLoading(false)); }, []);

  // loginWithPassword/registerWithPassword resolve to the user object itself,
  // taken from the JSON auth API response.
  const login = async (credentials) => {
    const nextUser = await loginWithPassword(credentials);
    setUser(nextUser);
    return nextUser;
  };

  const register = async (details) => {
    const nextUser = await registerWithPassword(details);
    setUser(nextUser);
    return nextUser;
  };

  const logout = async () => {
    // Clear local state even if the network call fails, so the UI never shows a
    // signed-in shell for a session the user asked to end.
    try {
      await logoutFromFlask();
    } finally {
      setUser(null);
    }
  };

  return <AuthContext.Provider value={{ user, loading, login, register, logout, refreshUser }}>
    {children}
  </AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used inside AuthProvider');
  return context;
}
