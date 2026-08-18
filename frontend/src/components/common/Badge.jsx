import React from 'react';

const Badge = ({
    children,
    variant = 'info', // info, success, warning, danger, neutral
    className = ''
}) => {
    const baseStyles = 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold select-none font-sans';

    const variantStyles = {
        info: 'bg-blue-50 dark:bg-blue-950/30 text-blue-650 dark:text-blue-400',
        success: 'bg-emerald-50 dark:bg-emerald-950/30 text-emerald-650 dark:text-emerald-400',
        warning: 'bg-amber-50 dark:bg-amber-950/30 text-amber-650 dark:text-amber-400',
        danger: 'bg-rose-50 dark:bg-rose-950/30 text-rose-650 dark:text-rose-450',
        neutral: 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300'
    };

    return (
        <span className={`${baseStyles} ${variantStyles[variant]} ${className}`}>
            {children}
        </span>
    );
};

export default Badge;
