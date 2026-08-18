import React, { useContext, useEffect, useState } from 'react';
import { DetectionContext } from '../../context/DetectionContext';
import { ThemeContext } from '../../context/ThemeContext';
import useAuth from '../../hooks/useAuth';
import Card from '../../components/common/Card';
import Input from '../../components/common/Input';
import Button from '../../components/common/Button';
import SectionTitle from '../../components/common/SectionTitle';
import Badge from '../../components/common/Badge';
import { Moon, Sun, CheckCircle, RefreshCw, Cpu, Database, ShieldCheck } from 'lucide-react';

const notifyKey = 'evtclip_notification_preferences';

const Settings = () => {
    const { user, updateProfile, loading: authLoading } = useAuth();
    const { theme, toggleTheme } = useContext(ThemeContext);
    const { apiUrl, mlServerUrl } = useContext(DetectionContext);

    const [profileName, setProfileName] = useState(user?.name || '');
    const [profileEmail, setProfileEmail] = useState(user?.email || '');
    const [pingStatus, setPingStatus] = useState('idle');
    const [health, setHealth] = useState(null);
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');
    const [prefs, setPrefs] = useState(() => {
        try { return JSON.parse(localStorage.getItem(notifyKey)) || { notifyDefects: true, notifyServers: false }; }
        catch { return { notifyDefects: true, notifyServers: false }; }
    });

    useEffect(() => {
        setProfileName(user?.name || '');
        setProfileEmail(user?.email || '');
    }, [user?.name, user?.email]);

    const flash = (text) => {
        setMessage(text);
        window.setTimeout(() => setMessage(''), 3000);
    };

    const handleProfileSave = async () => {
        setError('');
        try {
            await updateProfile({ full_name: profileName.trim() || null, email: profileEmail.trim() });
            flash('Profile updated on the backend.');
        } catch (err) {
            setError(err.message || 'Profile update failed.');
        }
    };

    const handleTestConnection = async () => {
        setPingStatus('testing');
        setError('');
        const started = performance.now();
        try {
            const response = await fetch('/health', { headers: { Accept: 'application/json' } });
            if (!response.ok) throw new Error(`Health endpoint returned HTTP ${response.status}`);
            const data = await response.json();
            setHealth({ ...data, latencyMs: Math.round(performance.now() - started) });
            setPingStatus('success');
        } catch (err) {
            setHealth(null);
            setPingStatus('error');
            setError(err.message || 'Health check failed.');
        }
    };

    const updatePref = (key) => {
        const next = { ...prefs, [key]: !prefs[key] };
        setPrefs(next);
        localStorage.setItem(notifyKey, JSON.stringify(next));
    };

    return (
        <div className="space-y-6 font-sans">
            <SectionTitle title="System Settings" subtitle="Manage your account, appearance, and the deployed EVT-CLIP CPU service." />

            {message && (
                <div className="p-3 bg-emerald-50 dark:bg-emerald-950/20 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-900/30 rounded-md text-xs font-semibold flex items-center gap-2">
                    <CheckCircle size={16} /> {message}
                </div>
            )}
            {error && <div className="p-3 bg-rose-50 dark:bg-rose-950/20 text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-900/30 rounded-md text-xs">{error}</div>}

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="space-y-6 lg:col-span-2">
                    <Card title="User Profile" subtitle="Saved to the authenticated FastAPI account">
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            <Input label="Full Name" id="prof_name" value={profileName} onChange={(e) => setProfileName(e.target.value)} />
                            <Input label="Email Address" id="prof_email" type="email" value={profileEmail} onChange={(e) => setProfileEmail(e.target.value)} />
                        </div>
                        <div className="flex justify-end mt-4">
                            <Button variant="primary" size="sm" onClick={handleProfileSave} disabled={authLoading}>Update Profile</Button>
                        </div>
                    </Card>

                    <Card title="Deployment Connection" subtitle="Read-only production routing; URLs are configured at build/deploy time">
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            <div className="p-4 border border-slate-200 dark:border-slate-800 rounded-md bg-slate-50 dark:bg-together-night/40">
                                <div className="flex items-center gap-2 text-xs font-bold text-slate-700 dark:text-slate-200"><Database size={15} /> API Gateway</div>
                                <p className="mt-2 text-[11px] font-mono text-slate-500 break-all">{apiUrl}</p>
                            </div>
                            <div className="p-4 border border-slate-200 dark:border-slate-800 rounded-md bg-slate-50 dark:bg-together-night/40">
                                <div className="flex items-center gap-2 text-xs font-bold text-slate-700 dark:text-slate-200"><Cpu size={15} /> Inference Runtime</div>
                                <p className="mt-2 text-[11px] font-mono text-slate-500">{mlServerUrl}</p>
                            </div>
                        </div>

                        <div className="mt-4 flex flex-wrap items-center gap-3 border-t border-slate-100 dark:border-slate-800 pt-4">
                            <Button variant="secondary" size="sm" onClick={handleTestConnection} disabled={pingStatus === 'testing'} icon={RefreshCw}>
                                {pingStatus === 'testing' ? 'Checking…' : 'Test Live Health'}
                            </Button>
                            {pingStatus === 'success' && <Badge variant="success">Ready · {health?.latencyMs} ms HTTP</Badge>}
                            {pingStatus === 'error' && <Badge variant="danger">Health check failed</Badge>}
                        </div>

                        {health && (
                            <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3 text-[11px]">
                                <div><span className="text-slate-400 block">Status</span><b>{health.status || 'unknown'}</b></div>
                                <div><span className="text-slate-400 block">Device</span><b>{health.device || 'cpu'}</b></div>
                                <div><span className="text-slate-400 block">Inference</span><b>{health.inference_mode || 'queued'}</b></div>
                                <div><span className="text-slate-400 block">Database</span><b>{health.database || 'configured'}</b></div>
                            </div>
                        )}
                    </Card>
                </div>

                <div className="space-y-6">
                    <Card title="Appearance" subtitle="Together-inspired light and dark presentation">
                        <button onClick={toggleTheme} className="w-full flex items-center justify-between p-3 border border-slate-200 dark:border-slate-800 rounded-md bg-slate-50 dark:bg-together-night/40 text-xs font-semibold">
                            <span>Current theme</span>
                            <span className="flex items-center gap-2">{theme === 'dark' ? <Moon size={14} /> : <Sun size={14} />}{theme === 'dark' ? 'Dark' : 'Light'}</span>
                        </button>
                    </Card>

                    <Card title="Local UI Alerts" subtitle="Preferences are stored in this browser">
                        <div className="space-y-4 text-xs font-semibold">
                            {[['notifyDefects', 'Inspection / anomaly alerts'], ['notifyServers', 'Service health warnings']].map(([key, label]) => (
                                <label key={key} className="flex items-center justify-between gap-3 cursor-pointer">
                                    <span>{label}</span>
                                    <input type="checkbox" checked={Boolean(prefs[key])} onChange={() => updatePref(key)} className="h-4 w-4 accent-fuchsia-600" />
                                </label>
                            ))}
                        </div>
                    </Card>

                    <Card title="Runtime Policy" subtitle="Deployment safeguards">
                        <div className="flex gap-3 text-xs leading-relaxed text-slate-500 dark:text-slate-400">
                            <ShieldCheck size={18} className="shrink-0 text-emerald-500" />
                            <p>CPU only. Production calibration is locked. Long inspections run as queued jobs so the browser does not hold one long HTTP request open.</p>
                        </div>
                    </Card>
                </div>
            </div>
        </div>
    );
};

export default Settings;
