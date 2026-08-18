import React, { useContext, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import useAuth from '../../hooks/useAuth';
import { DetectionContext } from '../../context/DetectionContext';
import { Bell, Search, ChevronDown, User, Shield, AlertTriangle, CheckCircle2 } from 'lucide-react';
import Breadcrumb from './Breadcrumb';

const Navbar = () => {
    const { user } = useAuth();
    const { history } = useContext(DetectionContext);
    const navigate = useNavigate();
    const [showProfileDropdown, setShowProfileDropdown] = useState(false);
    const [showNotifications, setShowNotifications] = useState(false);
    const [search, setSearch] = useState('');

    const notifications = useMemo(() => history.slice(0, 6).map((item) => ({
        id: item.id,
        text: `${item.prediction} · ${item.category.replace('_', ' ')} · ${item.imageName}`,
        type: !item.resultValid || item.rejectionCode ? 'warning' : (item.prediction === 'Anomalous' ? 'error' : 'ok'),
    })), [history]);

    const submitSearch = (event) => {
        if (event.key === 'Enter' && search.trim()) navigate(`/history?search=${encodeURIComponent(search.trim())}`);
    };

    return (
        <header className="h-16 bg-white dark:bg-[#010120] border-b border-black/10 dark:border-white/10 flex items-center justify-between px-6 z-20 transition-colors duration-300">
            <Breadcrumb />
            <div className="flex items-center gap-4">
                <div className="relative hidden md:block w-64">
                    <span className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none text-slate-400"><Search size={17} /></span>
                    <input value={search} onChange={(e) => setSearch(e.target.value)} onKeyDown={submitSearch} type="text" placeholder="Search inspection history…" className="w-full pl-10 pr-4 py-2 text-sm rounded-[4px] border border-black/10 dark:border-white/15 bg-slate-50 dark:bg-[#10102d] text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:border-primary-500" />
                </div>

                <div className="relative">
                    <button onClick={() => { setShowNotifications(!showNotifications); setShowProfileDropdown(false); }} className="p-2 rounded-[4px] text-slate-500 dark:text-[#b8b8c8] hover:bg-slate-100 dark:hover:bg-white/10 transition-colors relative">
                        <Bell size={19} />
                        {notifications.some((n) => n.type === 'error' || n.type === 'warning') && <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-[#ef2cc1] rounded-full ring-2 ring-white dark:ring-[#010120]" />}
                    </button>
                    {showNotifications && (
                        <div className="absolute right-0 mt-2 w-96 bg-white dark:bg-[#10102d] border border-black/10 dark:border-white/10 rounded-[6px] shadow-soft-lg z-50 overflow-hidden">
                            <div className="px-4 py-3 border-b border-black/10 dark:border-white/10"><span className="font-medium text-sm text-slate-900 dark:text-white">Recent inspection results</span></div>
                            <div className="max-h-72 overflow-y-auto divide-y divide-black/5 dark:divide-white/10">
                                {notifications.length === 0 ? <div className="p-5 text-center text-slate-400 text-xs">No completed inspections yet.</div> : notifications.map((n) => (
                                    <button key={n.id} onClick={() => { setShowNotifications(false); sessionStorage.setItem('active_report_id', n.id); navigate('/reports'); }} className="w-full p-3.5 flex gap-3 text-xs leading-5 hover:bg-slate-50 dark:hover:bg-white/5 transition-colors text-left">
                                        <span className={`p-1.5 rounded-full shrink-0 h-7 w-7 flex items-center justify-center ${n.type === 'error' ? 'bg-rose-50 text-rose-500 dark:bg-rose-950/30' : n.type === 'warning' ? 'bg-amber-50 text-amber-500 dark:bg-amber-950/30' : 'bg-emerald-50 text-emerald-600 dark:bg-emerald-950/30'}`}>
                                            {n.type === 'ok' ? <CheckCircle2 size={14} /> : <AlertTriangle size={14} />}
                                        </span>
                                        <span className="text-slate-700 dark:text-slate-300">{n.text}</span>
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}
                </div>

                <span className="w-px h-6 bg-black/10 dark:bg-white/10 block" />
                <div className="relative">
                    <button onClick={() => { setShowProfileDropdown(!showProfileDropdown); setShowNotifications(false); }} className="flex items-center gap-2.5 p-1.5 pr-2.5 rounded-[4px] hover:bg-slate-100 dark:hover:bg-white/10 transition-colors">
                        <div className="w-8 h-8 rounded-full evt-gradient text-white font-medium flex items-center justify-center uppercase">{user?.name ? user.name[0] : 'U'}</div>
                        <div className="hidden sm:block text-left text-xs"><span className="font-medium text-slate-900 dark:text-white block truncate w-28">{user?.name || 'User'}</span><span className="text-slate-400 text-[10px] tracking-wide block leading-none mt-0.5">{user?.role || 'Guest'}</span></div>
                        <ChevronDown size={14} className="text-slate-400" />
                    </button>
                    {showProfileDropdown && (
                        <div className="absolute right-0 mt-2 w-56 bg-white dark:bg-[#10102d] border border-black/10 dark:border-white/10 rounded-[6px] shadow-soft-lg z-50 overflow-hidden py-1">
                            <div className="px-4 py-2 border-b border-black/10 dark:border-white/10"><span className="text-[10px] uppercase tracking-wider text-slate-400 block">Logged in as</span><span className="text-xs font-medium text-slate-700 dark:text-slate-200 truncate block mt-1">{user?.email || 'user'}</span></div>
                            <button onClick={() => { setShowProfileDropdown(false); navigate('/settings'); }} className="w-full flex items-center gap-2.5 px-4 py-2.5 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-white/5 text-xs font-medium"><User size={15} />My Profile</button>
                            <div className="w-full flex items-center gap-2.5 px-4 py-2.5 text-slate-500 dark:text-slate-400 text-xs"><Shield size={15} />{user?.role || 'Guest'} permissions</div>
                        </div>
                    )}
                </div>
            </div>
        </header>
    );
};
export default Navbar;
