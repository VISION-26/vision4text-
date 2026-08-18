import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import useAuth from '../hooks/useAuth';

import Overview from '../pages/Overview/Overview';
import Dashboard from '../pages/Dashboard/Dashboard';
import Detection from '../pages/Detection/Detection';
import Reports from '../pages/Reports/Reports';
import History from '../pages/History/History';
import Settings from '../pages/Settings/Settings';
import Admin from '../pages/Admin/Admin';
import About from '../pages/About/About';
import Login from '../pages/Login/Login';
import NotFound from '../pages/NotFound/NotFound';
import ProtectedLayout from '../components/layout/ProtectedLayout';

const AppRoutes = () => {
    const { user } = useAuth();

    return (
        <Routes>
            <Route path="/" element={<Overview />} />
            <Route path="/overview" element={<Overview />} />
            <Route path="/login" element={user ? <Navigate to="/dashboard" replace /> : <Login />} />

            <Route element={<ProtectedLayout />}>
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/detection" element={<Detection />} />
                <Route path="/reports" element={<Reports />} />
                <Route path="/history" element={<History />} />
                <Route path="/about" element={<About />} />
                <Route path="/settings" element={<Settings />} />
                <Route
                    path="/admin"
                    element={user && user.role === 'Admin' ? <Admin /> : <Navigate to="/dashboard" replace />}
                />
            </Route>

            <Route path="*" element={<NotFound />} />
        </Routes>
    );
};

export default AppRoutes;
