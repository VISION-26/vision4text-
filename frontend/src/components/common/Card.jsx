import React from 'react';

const Card = ({ children, title, subtitle, actions, className = '', padding = true }) => (
    <div className={`bg-white dark:bg-[#10102d] rounded-[6px] border border-black/10 dark:border-white/10 shadow-none hover:border-black/20 dark:hover:border-white/20 transition-colors duration-200 ${className}`}>
        {(title || subtitle || actions) && (
            <div className="px-5 py-3.5 border-b border-black/10 dark:border-white/10 flex items-center justify-between gap-4">
                <div>
                    {title && <h3 className="font-medium text-slate-950 dark:text-white text-base tracking-[-0.015em]">{title}</h3>}
                    {subtitle && <p className="text-[#73737d] dark:text-[#9b9baa] text-xs mt-1 leading-relaxed">{subtitle}</p>}
                </div>
                {actions && <div className="flex items-center gap-2">{actions}</div>}
            </div>
        )}
        <div className={padding ? 'p-5' : ''}>{children}</div>
    </div>
);
export default Card;
