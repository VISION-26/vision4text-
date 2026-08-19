import React, { createContext, useState } from 'react';
import api from '../services/api';
import { SYSTEM_ROLE_PERMISSIONS } from '../constants';

export const AuthContext = createContext();
const storageKey = 'visiontext_user';

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(() => {
        const token = localStorage.getItem('visiontext_access_token');
        if (!token) {
            localStorage.removeItem(storageKey);
            return null;
        }
        try { return JSON.parse(localStorage.getItem(storageKey) || 'null'); }
        catch { localStorage.removeItem(storageKey); return null; }
    });
    const [loading, setLoading] = useState(false);

    const normalize = (account) => ({ ...account, name: account.full_name || account.email });

    const persist = ({ access_token, refresh_token, user: account }) => {
        const normalized = normalize(account);
        localStorage.setItem('visiontext_access_token', access_token);
        localStorage.setItem('visiontext_refresh_token', refresh_token);
        localStorage.setItem(storageKey, JSON.stringify(normalized));
        setUser(normalized);
        return normalized;
    };

    const login = async (email, password) => {
        setLoading(true);
        try {
            const { data } = await api.post('/auth/login', { email, password });
            return persist(data);
        } finally {
            setLoading(false);
        }
    };

    const updateProfile = async ({ full_name, email }) => {
        setLoading(true);
        try {
            const { data } = await api.put('/auth/profile', { full_name, email });
            const normalized = normalize(data);
            localStorage.setItem(storageKey, JSON.stringify(normalized));
            setUser(normalized);
            return normalized;
        } finally {
            setLoading(false);
        }
    };

    const logout = () => {
        ['visiontext_access_token', 'visiontext_refresh_token', storageKey].forEach((key) => localStorage.removeItem(key));
        setUser(null);
    };

    const hasPermission = (permission) => Boolean(user && (SYSTEM_ROLE_PERMISSIONS[user.role] || []).includes(permission));

    return (
        <AuthContext.Provider value={{ user, login, updateProfile, logout, hasPermission, loading }}>
            {children}
        </AuthContext.Provider>
    );
};
