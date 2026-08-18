import React from 'react';

const ResponsiveLayout = ({ children, className = '' }) => {
    return (
        <div className={`grid grid-cols-1 lg:grid-cols-12 gap-5 w-full ${className}`}>
            {children}
        </div>
    );
};

export default ResponsiveLayout;
