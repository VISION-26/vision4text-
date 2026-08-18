import React from 'react';

const Input = ({
    type = 'text',
    label,
    id,
    value,
    onChange,
    placeholder,
    helperText,
    error,
    disabled = false,
    className = '',
    inputClassName = '',
    required = false,
    leadingIcon: LeadingIcon = null,
    autoComplete,
}) => {
    const helperId = id ? `${id}-help` : undefined;

    return (
        <div className={`w-full space-y-1.5 font-sans ${className}`}>
            {label && (
                <label htmlFor={id} className="block text-xs font-semibold text-slate-500 dark:text-slate-400">
                    {label} {required && <span className="text-rose-500">*</span>}
                </label>
            )}
            <div className="relative">
                {LeadingIcon && (
                    <span
                        aria-hidden="true"
                        className="pointer-events-none absolute inset-y-0 left-0 z-10 flex w-11 items-center justify-center text-slate-400"
                    >
                        <LeadingIcon size={17} strokeWidth={1.9} />
                    </span>
                )}
                <input
                    type={type}
                    id={id}
                    value={value}
                    onChange={onChange}
                    placeholder={placeholder}
                    disabled={disabled}
                    required={required}
                    autoComplete={autoComplete}
                    aria-invalid={Boolean(error)}
                    aria-describedby={(error || helperText) ? helperId : undefined}
                    className={`w-full ${LeadingIcon ? 'pl-11 pr-4' : 'px-4'} h-11 text-sm rounded-lg border bg-white dark:bg-[#08152e] text-slate-800 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 disabled:opacity-50 disabled:bg-slate-50 dark:disabled:bg-slate-900 transition-all duration-200 ${error
                        ? 'border-rose-500 focus:border-rose-500 focus:ring-rose-500/20'
                        : 'border-slate-200 dark:border-slate-800 focus:border-fuchsia-500 focus:ring-fuchsia-500/20'
                    } ${inputClassName}`}
                />
            </div>
            {error ? (
                <p id={helperId} className="text-xs font-medium text-rose-500">{error}</p>
            ) : helperText ? (
                <p id={helperId} className="text-xs text-slate-400">{helperText}</p>
            ) : null}
        </div>
    );
};

export default Input;
