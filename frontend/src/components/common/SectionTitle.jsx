import React from 'react';

const SectionTitle = ({ title, subtitle, badge, actions, className = '' }) => (
    <div className={`flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 font-sans ${className}`}>
        <div>
            <div className="flex items-center gap-3">
                <h2 className="text-2xl sm:text-[30px] leading-tight font-medium text-slate-950 dark:text-white tracking-[-0.035em]">{title}</h2>
                {badge && <span className="bg-[#c8f6f9] text-[#010120] text-[10px] font-mono font-medium uppercase tracking-[0.08em] px-2 py-1 rounded-[3px] shrink-0">{badge}</span>}
            </div>
            {subtitle && <p className="text-[#73737d] dark:text-[#9999aa] text-sm mt-2 font-normal max-w-3xl leading-relaxed">{subtitle}</p>}
        </div>
        {actions && <div className="flex items-center gap-2 shrink-0">{actions}</div>}
    </div>
);
export default SectionTitle;
