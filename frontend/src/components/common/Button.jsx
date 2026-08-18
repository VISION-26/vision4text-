import React from 'react';

const Button = ({ children, variant = 'primary', size = 'md', type = 'button', onClick, disabled = false, className = '', icon: Icon }) => {
    const baseStyles = 'inline-flex items-center justify-center font-medium rounded-[4px] transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 active:translate-y-px disabled:opacity-50 disabled:cursor-not-allowed';
    const sizeStyles = { sm: 'px-3 py-1.5 text-xs gap-1.5', md: 'px-4 py-2.5 text-sm gap-2', lg: 'px-6 py-3.5 text-base gap-2.5' };
    const variantStyles = {
        primary: 'bg-black hover:bg-[#27273d] dark:bg-white dark:hover:bg-slate-100 text-white dark:text-black focus:ring-primary-500',
        secondary: 'bg-white dark:bg-[#10102d] text-slate-800 dark:text-slate-100 border border-black/10 dark:border-white/15 hover:border-primary-500 focus:ring-primary-400',
        danger: 'bg-rose-600 hover:bg-rose-700 text-white focus:ring-rose-500',
        success: 'bg-emerald-600 hover:bg-emerald-700 text-white focus:ring-emerald-500',
        gradient: 'evt-gradient text-white hover:brightness-105 shadow-[0_10px_28px_rgba(239,44,193,0.18)] focus:ring-primary-500',
    };
    return (
        <button type={type} onClick={onClick} disabled={disabled} className={`${baseStyles} ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}>
            {Icon && <Icon size={size === 'sm' ? 14 : size === 'lg' ? 20 : 17} className="shrink-0" />}
            {children}
        </button>
    );
};
export default Button;
