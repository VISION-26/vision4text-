import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { DetectionProvider } from './context/DetectionContext';
import AppRoutes from './routes';

function App() {
    return (
        <ThemeProvider>
            <AuthProvider>
                <DetectionProvider>
                    <BrowserRouter>
                        <div className="min-h-screen">
                            <AppRoutes />
                        </div>
                    </BrowserRouter>
                </DetectionProvider>
            </AuthProvider>
        </ThemeProvider>
    );
}

export default App;
