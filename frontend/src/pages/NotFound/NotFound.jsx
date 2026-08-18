import React from 'react';
import { useNavigate } from 'react-router-dom';
import Button from '../../components/common/Button';
import { ShieldAlert, ArrowLeft } from 'lucide-react';

const NotFound = () => {
    const navigate = useNavigate();

    return (
        <div className="min-h-screen flex flex-col items-center justify-center bg-[#08152E] px-4 font-sans text-center relative overflow-hidden">
            {/* Background radial glows */}
            <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary-650/10 rounded-full blur-3xl pointer-events-none" />
            <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-indigo-650/10 rounded-full blur-3xl pointer-events-none" />

            <div className="z-10 space-y-6 max-w-md">
                <div className="mx-auto bg-rose-950/20 text-rose-500 border border-rose-900/30 p-4.5 rounded-2xl w-16 h-16 flex items-center justify-center shadow-lg shadow-rose-950/20">
                    <ShieldAlert size={32} className="animate-bounce" />
                </div>

                <div className="space-y-2 select-none">
                    <h1 className="text-7xl font-extrabold text-white tracking-tight">404</h1>
                    <h2 className="text-xl font-bold text-slate-205">Page Not Found</h2>
                    <p className="text-xs text-slate-400 font-semibold leading-relaxed">
                        The path you are trying to access does not exist on this inspection node. Check route credentials.
                    </p>
                </div>

                <Button
                    variant="gradient"
                    onClick={() => navigate('/dashboard')}
                    icon={ArrowLeft}
                    className="px-6 py-3"
                >
                    Return to Dashboard
                </Button>
            </div>
        </div>
    );
};

export default NotFound;
