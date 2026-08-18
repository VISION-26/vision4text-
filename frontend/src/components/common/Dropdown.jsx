import React, { useState, useEffect, useRef } from 'react';
import { ChevronDown } from 'lucide-react';

const Dropdown = ({
    trigger,
    label,
    items = [],
    className = '',
    align = 'right'
}) => {
    const [isOpen, setIsOpen] = useState(false);
    const dropdownRef = useRef(null);

    useEffect(() => {
        const handleClickOutside = (event) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const alignStyles = {
        left: 'left-0',
        right: 'right-0'
    };

    return (
        <div className={`relative inline-block text-left font-sans ${className}`} ref={dropdownRef}>
            <div onClick={() => setIsOpen(!isOpen)} className="cursor-pointer">
                {trigger ? (
                    trigger
                ) : (
                    <button className="flex items-center gap-1 text-slate-650 hover:text-slate-800 dark:text-slate-300 dark:hover:text-slate-100 text-sm font-semibold py-2 px-3 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl transition-all">
                        {label}
                        <ChevronDown size={14} />
                    </button>
                )}
            </div>

            {isOpen && (
                <div className={`absolute ${alignStyles[align]} mt-2 w-48 bg-white dark:bg-[#0d1b38] border border-slate-200 dark:border-slate-800 rounded-2xl shadow-soft-lg z-50 overflow-hidden py-1`}>
                    {items.map((item, idx) => (
                        <button
                            key={idx}
                            onClick={() => {
                                if (item.onClick) item.onClick();
                                setIsOpen(false);
                            }}
                            className="w-full text-left px-4 py-2.5 text-xs font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800/80 transition-colors flex items-center gap-2"
                        >
                            {item.icon && <item.icon size={15} className="text-slate-400 shrink-0" />}
                            {item.label}
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
};

export default Dropdown;
