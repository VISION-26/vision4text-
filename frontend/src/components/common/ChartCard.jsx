import React from 'react';
import Card from './Card';

const ChartCard = ({
    title,
    subtitle,
    children,
    actions,
    className = ''
}) => {
    return (
        <Card
            title={title}
            subtitle={subtitle}
            actions={actions}
            className={`relative flex flex-col justify-between ${className}`}
        >
            <div className="w-full h-80 min-h-[300px] mt-2 relative">
                {children}
            </div>
        </Card>
    );
};

export default ChartCard;
