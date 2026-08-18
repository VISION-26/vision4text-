import React from 'react';
import { useLocation, Link } from 'react-router-dom';
import { ChevronRight } from 'lucide-react';

const Breadcrumb = () => {
    const location = useLocation();
    const pathnames = location.pathname.split('/').filter((x) => x);

    // Return empty if we are on login screen
    if (location.pathname === '/login') return null;

    return (
        <nav className="flex items-center text-xs sm:text-sm font-medium text-slate-500 dark:text-slate-400 font-sans">
            <Link
                to="/dashboard"
                className="hover:text-primary-600 dark:hover:text-primary-400 capitalize transition-colors"
            >
                Home
            </Link>

            {pathnames.map((name, index) => {
                const routeTo = `/${pathnames.slice(0, index + 1).join('/')}`;
                const isLast = index === pathnames.length - 1;

                return (
                    <div key={name} className="flex items-center">
                        <ChevronRight size={14} className="mx-2 text-slate-400 shrink-0" />
                        {isLast ? (
                            <span className="font-semibold text-slate-800 dark:text-slate-100 capitalize">
                                {name.replace('-', ' ')}
                            </span>
                        ) : (
                            <Link
                                to={routeTo}
                                className="hover:text-primary-600 dark:hover:text-primary-400 capitalize transition-colors"
                            >
                                {name.replace('-', ' ')}
                            </Link>
                        )}
                    </div>
                );
            })}
        </nav>
    );
};

export default Breadcrumb;
