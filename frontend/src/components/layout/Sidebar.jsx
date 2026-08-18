import React, { useContext, useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { ThemeContext } from '../../context/ThemeContext';
import useAuth from '../../hooks/useAuth';
import {
    LayoutDashboard, ScanEye, FileSpreadsheet, History, Settings,
    UserCog, LogOut, Sun, Moon, ChevronLeft, ChevronRight,
    Home, Info,
} from 'lucide-react';

const BrandMark = () => (
    <span className="flex h-6 shrink-0 items-end gap-[3px]" aria-hidden="true">
        <i className="block h-3 w-1.5 bg-[#fc4c02]" />
        <i className="block h-6 w-1.5 bg-[#ef2cc1]" />
        <i className="block h-4 w-1.5 bg-[#bdbbff]" />
    </span>
);

const Sidebar = () => {
    const [collapsed, setCollapsed] = useState(false);
    const { theme, toggleTheme } = useContext(ThemeContext);
    const { user, logout } = useAuth();
    const navigate = useNavigate();

    const groups = [
        {
            label: 'Workspace',
            items: [
                { name: 'Overview', icon: Home, path: '/overview' },
                { name: 'About', icon: Info, path: '/about' },
            ],
        },
        {
            label: 'Inspection',
            items: [
                { name: 'Dashboard', icon: LayoutDashboard, path: '/dashboard' },
                { name: 'New Inspection', icon: ScanEye, path: '/detection' },
            ],
        },
        {
            label: 'Evidence',
            items: [
                { name: 'Reports', icon: FileSpreadsheet, path: '/reports' },
                { name: 'History', icon: History, path: '/history' },
            ],
        },
        {
            label: 'System',
            items: [
                { name: 'Settings', icon: Settings, path: '/settings' },
                ...(user?.role === 'Admin' ? [{ name: 'Admin', icon: UserCog, path: '/admin' }] : []),
            ],
        },
    ];

    const handleLogout = () => { logout(); navigate('/login'); };

    return (
        <aside className={`relative z-30 flex h-screen flex-col justify-between border-r border-white/10 bg-[#010120] text-[#b8b8c8] transition-all duration-300 ${collapsed ? 'w-20' : 'w-64'}`}>
            <div className="min-h-0">
                <div className="flex h-16 items-center border-b border-white/10 px-5">
                    <button className="flex items-center gap-3 overflow-hidden text-left" onClick={() => navigate('/dashboard')} aria-label="Open dashboard">
                        <BrandMark />
                        {!collapsed && <span className="whitespace-nowrap text-[17px] font-medium tracking-[-0.02em] text-white">EVT-CLIP</span>}
                    </button>
                </div>
                <button onClick={() => setCollapsed(!collapsed)} aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'} className="absolute -right-3 top-14 z-40 rounded-full border border-white/20 bg-[#010120] p-1 text-white transition-colors hover:bg-[#27273d]">
                    {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
                </button>
                <nav className="mt-3 max-h-[calc(100vh-152px)] overflow-y-auto px-3 pb-3" aria-label="Main navigation">
                    {groups.map((group) => (
                        <div key={group.label} className="mb-3">
                            {!collapsed && <p className="mb-1 px-3 text-[8px] font-bold uppercase tracking-[.18em] text-white/35">{group.label}</p>}
                            <div className="space-y-0.5">
                                {group.items.map((item) => (
                                    <NavLink
                                        key={item.name}
                                        to={item.path}
                                        aria-label={item.name}
                                        title={collapsed ? item.name : undefined}
                                        className={({ isActive }) => `group flex items-center gap-3 rounded-md px-4 py-2.5 text-[13px] font-medium transition-all duration-150 ${isActive ? 'bg-white text-[#010120]' : 'hover:bg-white/10 hover:text-white'}`}
                                    >
                                        <item.icon size={18} className="shrink-0" />
                                        {!collapsed && <span className="min-w-0 flex-1 truncate">{item.name}</span>}
                                        {!collapsed && item.badge && <span className="rounded-full border border-amber-400/25 bg-amber-400/10 px-1.5 py-0.5 text-[7px] font-bold uppercase tracking-wide text-amber-300">{item.badge}</span>}
                                    </NavLink>
                                ))}
                            </div>
                        </div>
                    ))}
                </nav>
            </div>
            <div className="space-y-1 border-t border-white/10 p-3">
                <button onClick={toggleTheme} className="flex w-full items-center gap-3 rounded-md px-4 py-2.5 text-[13px] font-medium text-[#9b9baa] transition-colors hover:bg-white/10 hover:text-white" aria-label="Toggle color theme">
                    {theme === 'dark' ? <Sun size={18} className="shrink-0 text-[#ffbd59]" /> : <Moon size={18} className="shrink-0 text-[#bdbbff]" />}
                    {!collapsed && <span>{theme === 'dark' ? 'Light Mode' : 'Dark Mode'}</span>}
                </button>
                <button onClick={handleLogout} className="flex w-full items-center gap-3 rounded-md px-4 py-2.5 text-[13px] font-medium text-rose-400 transition-colors hover:bg-rose-500/10" aria-label="Sign out">
                    <LogOut size={18} className="shrink-0" />{!collapsed && <span>Logout</span>}
                </button>
            </div>
        </aside>
    );
};
export default Sidebar;
