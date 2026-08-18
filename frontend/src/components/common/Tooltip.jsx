import React, { useState } from 'react';

const Tooltip = ({
    children,
    content,
    position = 'top' // top, bottom, left, right
}) => {
    const [active, setActive] = useState(false);

    const positionStyles = {
        top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
        bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
        left: 'right-full top-1/2 -translate-y-1/2 mr-2',
        right: 'left-full top-1/2 -translate-y-1/2 ml-2'
    };

    return (
        <div
            className="relative inline-block font-sans"
            onMouseEnter={() => setActive(true)}
            onMouseLeave={() => setActive(false)}
        >
            {children}
            {active && content && (
                <div className={`absolute z-60 bg-slate-900 text-white text-[11px] font-medium px-2 py-1.5 rounded-lg whitespace-nowrap shadow-md pointer-events-none ${positionStyles[position]}`}>
                    {content}
                </div>
            )}
        </div>
    );
};

export default Tooltip;
