import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import useAuth from '../../hooks/useAuth';
import Sidebar from './Sidebar';
import Navbar from './Navbar';
import Footer from './Footer';

const ProtectedLayout = () => {
    const { user } = useAuth();

    // Route check
    if (!user) {
        return <Navigate to="/login" replace />;
    }

    return (
        <div className="flex h-screen overflow-hidden bg-slate-50 dark:bg-[#08152e] transition-colors duration-300 font-sans">
            {/* Sidebar navigation */}
            <Sidebar />

            {/* Main Content Area */}
            <div className="flex-1 flex flex-col overflow-hidden">
                {/* Navbar */}
                <Navbar />

                {/* Dynamic Page Router Outlet */}
                <main className="flex-1 overflow-y-auto px-4 sm:px-5 py-4 sm:py-5 bg-slate-50 dark:bg-[#08152e] grid-pattern transition-colors duration-300">
                    <div className="max-w-[1440px] mx-auto space-y-5">
                        <Outlet />
                    </div>
                </main>

                {/* Footer */}
                <Footer />
            </div>
        </div>
    );
};

export default ProtectedLayout;
