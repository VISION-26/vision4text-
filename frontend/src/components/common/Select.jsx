import React from 'react';

const Select = ({
    label,
    id,
    value,
    onChange,
    options = [],
    error,
    disabled = false,
    className = '',
    required = false
}) => {
    return (
        <div className={`space-y-1.5 w-full font-sans ${className}`}>
            {label && (
                <label htmlFor={id} className="block text-xs font-semibold text-slate-500 dark:text-slate-400 capitalize">
                    {label} {required && <span className="text-rose-500">*</span>}
                </label>
            )}
            <select
                id={id}
                value={value}
                onChange={onChange}
                disabled={disabled}
                required={required}
                className={`w-full px-4 py-2.5 text-sm rounded-xl border bg-white dark:bg-[#08152e] text-slate-805 dark:text-slate-100 focus:outline-none focus:ring-2 disabled:opacity-50 disabled:bg-slate-50 dark:disabled:bg-slate-900 transition-all duration-200 ${error
                        ? 'border-rose-500 focus:border-rose-500 focus:ring-rose-500/20'
                        : 'border-slate-200 dark:border-slate-800 focus:border-primary-500 focus:ring-primary-500/20'
                    }`}
            >
                {options.map((opt) => (
                    <option key={opt.value} value={opt.value} className="bg-white dark:bg-[#0d1b38] text-slate-800 dark:text-slate-200">
                        {opt.label}
                    </option>
                ))}
            </select>
            {error && <p className="text-xs text-rose-500 font-medium">{error}</p>}
        </div>
    );
};

export default Select;
