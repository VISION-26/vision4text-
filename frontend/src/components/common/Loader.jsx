import React from 'react';

const Loader = ({
    size = 'md', // sm, md, lg
    backdrop = false,
    text = 'Processing...'
}) => {
    const sizeStyles = {
        sm: 'w-6 h-6 border-2',
        md: 'w-10 h-10 border-3',
        lg: 'w-16 h-16 border-4'
    };

    const spinner = (
        <div className="flex flex-col items-center justify-center gap-3 font-sans">
            <div
                className={`rounded-full border-primary-500 border-t-transparent animate-spin ${sizeStyles[size]}`}
            />
            {text && <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">{text}</span>}
        </div>
    );

    if (backdrop) {
        return (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs">
                <div className="bg-white dark:bg-[#0d1b38] px-8 py-6 rounded-2xl shadow-soft border border-slate-100 dark:border-slate-800">
                    {spinner}
                </div>
            </div>
        );
    }

    return spinner;
};

export default Loader;
