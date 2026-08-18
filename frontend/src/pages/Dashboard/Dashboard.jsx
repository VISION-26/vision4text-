import React, { useContext, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Activity, AlertTriangle, ArrowUpRight, CheckCircle2, Clock, Cpu,
    Download, Plus, RefreshCw, ShieldAlert, ShieldCheck
} from 'lucide-react';
import {
    Bar, BarChart, CartesianGrid, Legend, Line, LineChart,
    ResponsiveContainer, Tooltip as ChartTooltip, XAxis, YAxis
} from 'recharts';
import { DetectionContext } from '../../context/DetectionContext';
import api from '../../services/api';
import Badge from '../../components/common/Badge';
import Button from '../../components/common/Button';
import Card from '../../components/common/Card';
import ChartCard from '../../components/common/ChartCard';
import SectionTitle from '../../components/common/SectionTitle';

const RANGE_OPTIONS = [
    ['day', 'Today'], ['week', '7 Days'], ['month', '30 Days'], ['year', '1 Year'], ['all', 'All Time'],
];

const emptyAnalytics = {
    totals: { total: 0, valid: 0, invalid: 0, review: 0, anomalies: 0, normal: 0, anomaly_rate: 0, avg_inference_seconds: 0, max_inference_seconds: 0 },
    trend: [], categories: [],
};

const statusFor = (record) => {
    if (record.prediction === 'Invalid Input' || record.rejectionCode) return { text: 'INPUT REJECTED', variant: 'warning' };
    if (record.resultValid === false) return { text: 'INPUT REJECTED', variant: 'warning' };
    if (record.prediction === 'Anomalous') return { text: 'ANOMALY', variant: 'danger' };
    return { text: 'NORMAL', variant: 'success' };
};

const Dashboard = () => {
    const { history, jobs, reloadJobs, retryJob } = useContext(DetectionContext);
    const navigate = useNavigate();
    const [range, setRange] = useState('week');
    const [analytics, setAnalytics] = useState(emptyAnalytics);
    const [analyticsLoading, setAnalyticsLoading] = useState(true);
    const [analyticsError, setAnalyticsError] = useState('');
    const [health, setHealth] = useState({ status: 'checking', device: 'cpu', inference_mode: 'modal_cpu_queue' });
    const [now, setNow] = useState(Date.now());

    const loadAnalytics = async (selectedRange = range) => {
        setAnalyticsLoading(true);
        setAnalyticsError('');
        try {
            const { data } = await api.get('/analytics/overview', { params: { range: selectedRange } });
            setAnalytics(data || emptyAnalytics);
        } catch (error) {
            setAnalyticsError(error.message || 'Analytics unavailable.');
        } finally {
            setAnalyticsLoading(false);
        }
    };

    useEffect(() => { loadAnalytics(range); }, [range]); // eslint-disable-line react-hooks/exhaustive-deps

    useEffect(() => {
        let active = true;
        fetch('/health', { cache: 'no-store' })
            .then((response) => response.ok ? response.json() : Promise.reject(new Error('Health check failed')))
            .then((data) => { if (active) setHealth(data); })
            .catch(() => { if (active) setHealth({ status: 'unavailable', device: 'cpu', inference_mode: 'modal_cpu_queue' }); });
        return () => { active = false; };
    }, []);

    useEffect(() => {
        const timer = window.setInterval(() => setNow(Date.now()), 1000);
        return () => window.clearInterval(timer);
    }, []);

    const totals = analytics?.totals || emptyAnalytics.totals;
    const rangeLabel = RANGE_OPTIONS.find(([key]) => key === range)?.[1] || '7 Days';
    const trendData = useMemo(() => (analytics?.trend || []).map((row) => ({
        ...row,
        label: range === 'day' ? String(row.bucket || '').slice(11, 16) : String(row.bucket || '').slice(5),
    })), [analytics, range]);
    const categoryData = useMemo(() => (analytics?.categories || []).map((row) => ({
        ...row,
        name: String(row.category || 'unknown').replace('_', ' ').toUpperCase(),
    })), [analytics]);

    const openReport = (id) => {
        sessionStorage.setItem('active_report_id', String(id));
        navigate('/reports');
    };

    const exportAnalyticsCsv = async () => {
        try {
            const response = await api.get('/analytics/export.csv', { params: { range }, responseType: 'blob', timeout: 120000 });
            const url = URL.createObjectURL(response.data);
            const anchor = document.createElement('a');
            anchor.href = url;
            anchor.download = `evt-clip-v2-analytics-${range}.csv`;
            document.body.appendChild(anchor);
            anchor.click();
            anchor.remove();
            window.setTimeout(() => URL.revokeObjectURL(url), 1500);
        } catch (error) {
            setAnalyticsError(error.message || 'Analytics export failed.');
        }
    };

    const healthReady = String(health?.status || '').toLowerCase() === 'ready';
    const queueConfigured = Boolean(health?.worker_configured || health?.inference_mode === 'modal_cpu_queue');
    const activeJobs = (jobs || []).filter((job) => ['queued', 'starting', 'running'].includes(job.status));
    const recentJobIssues = (jobs || []).filter((job) => ['failed', 'timed_out', 'cancelled'].includes(job.status)).slice(0, 3);
    const ageOf = (job) => job.createdAt ? Math.max(0, Math.floor((now - new Date(job.createdAt).getTime()) / 1000)) : 0;

    return (
        <div className="space-y-6 font-sans">
            <SectionTitle
                title="AI Anomaly Overview"
                subtitle="EVT-CLIP inspection activity: throughput, anomalies, input rejections, and CPU latency."
                actions={<Button variant="gradient" onClick={() => navigate('/detection')} icon={Plus}>Run New Inspection</Button>}
            />

            <Card padding={false}>
                <div className="p-3 flex flex-wrap items-center justify-between gap-3">
                    <div className="flex flex-wrap gap-2">
                        {RANGE_OPTIONS.map(([key, label]) => (
                            <button
                                key={key}
                                onClick={() => setRange(key)}
                                className={`px-3 py-2 rounded-md text-[11px] font-bold border transition-colors ${range === key ? 'border-together-magenta text-together-magenta bg-fuchsia-50 dark:bg-fuchsia-950/15' : 'border-slate-200 dark:border-slate-800 text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'}`}
                            >{label}</button>
                        ))}
                    </div>
                    <div className="flex flex-wrap items-center gap-2 text-[11px] text-slate-500">
                        <span>Analytics window: <b>{rangeLabel}</b></span>
                        <Button variant="secondary" size="sm" onClick={exportAnalyticsCsv} icon={Download}>Export CSV</Button>
                        <Button variant="secondary" size="sm" onClick={() => loadAnalytics(range)} icon={RefreshCw} disabled={analyticsLoading}>Refresh</Button>
                    </div>
                </div>
            </Card>

            {analyticsError && (
                <div className="p-3 rounded-md border border-rose-200 bg-rose-50 dark:bg-rose-950/20 text-rose-700 dark:text-rose-300 text-xs flex gap-2 items-center">
                    <AlertTriangle size={16} /> {analyticsError}
                </div>
            )}

            <div className="grid grid-cols-1 gap-4 xl:grid-cols-[.9fr_1.5fr_.9fr]">
                <Card title="System Availability" subtitle="Web API and inference queue are reported separately.">
                    <div className="space-y-2 text-xs">
                        <div className="flex items-center justify-between rounded-lg border border-slate-200 px-3 py-2 dark:border-slate-800"><span>API</span><Badge variant={healthReady ? 'success' : 'warning'}>{healthReady ? 'AVAILABLE' : 'UNAVAILABLE'}</Badge></div>
                        <div className="flex items-center justify-between rounded-lg border border-slate-200 px-3 py-2 dark:border-slate-800"><span>Inference queue</span><Badge variant={queueConfigured ? 'info' : 'warning'}>{queueConfigured ? 'CONFIGURED' : 'UNAVAILABLE'}</Badge></div>
                        <div className="flex items-center justify-between rounded-lg border border-slate-200 px-3 py-2 dark:border-slate-800"><span>Worker state</span><b className="text-[10px]">{activeJobs.length ? 'ACTIVE / STARTING' : 'SCALE-TO-ZERO'}</b></div>
                    </div>
                </Card>
                <Card title="Active Inspection Jobs" subtitle="Jobs remain visible while the CPU worker starts or runs.">
                    {activeJobs.length === 0 ? (
                        <div className="flex min-h-24 items-center justify-center rounded-lg border border-dashed border-slate-200 text-xs text-slate-400 dark:border-slate-800">No queued or running inspections.</div>
                    ) : (
                        <div className="space-y-2">
                            {activeJobs.slice(0, 4).map((job) => (
                                <div key={job.id} className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-slate-200 px-3 py-2 text-xs dark:border-slate-800">
                                    <div><b>Scan #{job.id}</b><span className="ml-2 capitalize text-slate-500">{String(job.category || '').replace('_', ' ')}</span></div>
                                    <div className="flex items-center gap-3"><Badge variant="info">{String(job.status).replace('_', ' ').toUpperCase()}</Badge><span className="font-mono text-[10px] text-slate-400">{ageOf(job)}s</span></div>
                                </div>
                            ))}
                        </div>
                    )}
                    <div className="mt-3 flex justify-end"><Button variant="secondary" size="sm" onClick={() => reloadJobs?.()} icon={RefreshCw}>Refresh Jobs</Button></div>
                </Card>
                <Card title="Recent Job Issues" subtitle="Failures and timeouts stay visible for diagnosis.">
                    {recentJobIssues.length === 0 ? <div className="flex min-h-24 items-center justify-center text-xs text-slate-400">No recent job failures.</div> : (
                        <div className="space-y-2 text-[10px]">{recentJobIssues.map((job) => <div key={job.id} className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 dark:border-amber-900/40 dark:bg-amber-950/20"><div className="flex items-center justify-between gap-2"><b>#{job.id} · {job.status.replace('_', ' ')}</b><button className="font-bold text-fuchsia-600 hover:text-fuchsia-700 dark:text-fuchsia-300" onClick={() => retryJob?.(job.id).catch((error) => setAnalyticsError(error.message || 'Retry failed.'))}>Retry</button></div><p className="mt-1 line-clamp-2 text-slate-500">{job.error || 'No diagnostic message recorded.'}</p></div>)}</div>
                    )}
                </Card>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-6 gap-4">
                <Card><p className="text-[10px] font-bold tracking-wider uppercase text-slate-400">Inspections</p><div className="mt-2 flex items-center justify-between"><b className="text-2xl">{totals.total}</b><Activity size={21} className="text-blue-500"/></div><p className="text-[10px] text-slate-400 mt-3">{totals.valid} valid decisions</p></Card>
                <Card><p className="text-[10px] font-bold tracking-wider uppercase text-slate-400">Anomalies</p><div className="mt-2 flex items-center justify-between"><b className="text-2xl">{totals.anomalies}</b><ShieldAlert size={21} className="text-rose-500"/></div><p className="text-[10px] text-rose-500 mt-3">{Number(totals.anomaly_rate || 0).toFixed(1)}% of valid scans</p></Card>
                <Card><p className="text-[10px] font-bold tracking-wider uppercase text-slate-400">Input Rejections</p><div className="mt-2 flex items-center justify-between"><b className="text-2xl">{totals.invalid}</b><ShieldCheck size={21} className="text-amber-500"/></div><p className="text-[10px] text-slate-400 mt-3">Wrong / unsupported category gate</p></Card>
                <Card><p className="text-[10px] font-bold tracking-wider uppercase text-slate-400">Normal Results</p><div className="mt-2 flex items-center justify-between"><b className="text-2xl">{totals.normal}</b><CheckCircle2 size={21} className="text-sky-500"/></div><p className="text-[10px] text-slate-400 mt-3">Accepted non-anomalous scans</p></Card>
                <Card><p className="text-[10px] font-bold tracking-wider uppercase text-slate-400">Avg CPU Time</p><div className="mt-2 flex items-center justify-between"><b className="text-2xl">{Number(totals.avg_inference_seconds || 0).toFixed(1)}s</b><Clock size={21} className="text-violet-500"/></div><p className="text-[10px] text-slate-400 mt-3">Max {Number(totals.max_inference_seconds || 0).toFixed(1)}s</p></Card>
                <Card><p className="text-[10px] font-bold tracking-wider uppercase text-slate-400">System</p><div className="mt-2 flex items-center justify-between"><b className={`text-sm ${healthReady ? 'text-emerald-500' : 'text-amber-500'}`}>{healthReady ? 'READY' : String(health.status || 'CHECKING').toUpperCase()}</b><Cpu size={21} className="text-together-periwinkle"/></div><p className="text-[10px] text-slate-400 mt-3">API status only · queue shown above</p></Card>
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
                <ChartCard title="Inspection Trend" subtitle={`${rangeLabel}: valid throughput plus anomaly and rejected-input activity`} className="xl:col-span-2">
                    {trendData.length === 0 ? <div className="absolute inset-0 flex items-center justify-center text-xs text-slate-400">No scans in this time range.</div> : (
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={trendData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                                <XAxis dataKey="label" stroke="#94A3B8" fontSize={10} tickLine={false}/>
                                <YAxis stroke="#94A3B8" fontSize={10} tickLine={false} allowDecimals={false}/>
                                <ChartTooltip contentStyle={{ borderRadius: '8px', border: '1px solid #E2E8F0' }}/>
                                <Legend verticalAlign="top" height={34} iconType="circle" />
                                <Line type="monotone" dataKey="detections" name="Inspections" stroke="#6366F1" strokeWidth={3} dot={false}/>
                                <Line type="monotone" dataKey="anomalies" name="Anomalies" stroke="#EF4444" strokeWidth={2} dot={false}/>
                                <Line type="monotone" dataKey="invalid" name="Rejected" stroke="#64748B" strokeWidth={2} strokeDasharray="4 4" dot={false}/>
                            </LineChart>
                        </ResponsiveContainer>
                    )}
                </ChartCard>

                <ChartCard title="Category Workload" subtitle="Scan volume by trained category, with valid anomalies and rejected inputs">
                    {categoryData.length === 0 ? <div className="absolute inset-0 flex items-center justify-center text-xs text-slate-400">No category activity in this range.</div> : (
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={categoryData} layout="vertical" margin={{ left: 18, right: 8, top: 8, bottom: 8 }}>
                                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#E2E8F0" />
                                <XAxis type="number" allowDecimals={false} fontSize={10} stroke="#94A3B8"/>
                                <YAxis type="category" dataKey="name" width={82} fontSize={9} stroke="#94A3B8"/>
                                <ChartTooltip contentStyle={{ borderRadius: '8px', border: '1px solid #E2E8F0' }}/>
                                <Legend iconType="circle" />
                                <Bar dataKey="count" name="Scans" fill="#6366F1" radius={[0, 4, 4, 0]}/>
                                <Bar dataKey="anomalies" name="Anomalies" fill="#EF4444" radius={[0, 4, 4, 0]}/>
                                <Bar dataKey="invalid" name="Rejected" fill="#94A3B8" radius={[0, 4, 4, 0]}/>
                            </BarChart>
                        </ResponsiveContainer>
                    )}
                </ChartCard>
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
                <Card title="Recent Inspection Log" subtitle="Latest stored scans; visual assets load only when opened" className="xl:col-span-2" padding={false} actions={<Button variant="secondary" size="sm" onClick={() => navigate('/history')}>View History</Button>}>
                    <div className="overflow-x-auto">
                        <table className="w-full text-left text-xs">
                            <thead><tr className="border-b border-slate-100 dark:border-slate-800 bg-slate-50/60 dark:bg-slate-900/10 text-slate-500"><th className="py-3 px-5">Time</th><th className="py-3 px-5">Image</th><th className="py-3 px-5">Category</th><th className="py-3 px-5">Score</th><th className="py-3 px-5">Status</th></tr></thead>
                            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                                {history.slice(0, 5).map((record) => { const state = statusFor(record); return (
                                    <tr key={record.id} onClick={() => openReport(record.id)} className="cursor-pointer hover:bg-slate-50/70 dark:hover:bg-slate-800/20">
                                        <td className="py-3 px-5 font-mono text-[10px] text-slate-400">{record.timestamp}</td>
                                        <td className="py-3 px-5 font-semibold max-w-52 truncate">{record.imageName}</td>
                                        <td className="py-3 px-5 capitalize text-slate-500">{record.category?.replace('_', ' ')}</td>
                                        <td className="py-3 px-5 font-mono font-bold">{Number(record.anomalyScore || 0).toFixed(3)}</td>
                                        <td className="py-3 px-5"><Badge variant={state.variant}>{state.text}</Badge></td>
                                    </tr>
                                ); })}
                                {history.length === 0 && <tr><td colSpan="5" className="py-10 text-center text-slate-400">No inspections stored yet.</td></tr>}
                            </tbody>
                        </table>
                    </div>
                </Card>

                <Card title="Production Diagnostics" subtitle="Reliability controls in the deployed architecture">
                    <div className="space-y-3 text-xs">
                        <div className="flex items-center justify-between p-3 bg-slate-50 dark:bg-[#08152e] rounded-md"><span className="flex items-center gap-2"><Cpu size={15}/>Inference</span><Badge variant="success">8-core CPU</Badge></div>
                        <div className="flex items-center justify-between p-3 bg-slate-50 dark:bg-[#08152e] rounded-md"><span className="flex items-center gap-2"><Clock size={15}/>Warm model cache</span><Badge variant="info">Enabled</Badge></div>
                        <div className="flex items-center justify-between p-3 bg-slate-50 dark:bg-[#08152e] rounded-md"><span className="flex items-center gap-2"><ShieldCheck size={15}/>Wrong-category gate</span><Badge variant="success">Fail closed</Badge></div>
                        <div className="p-3 bg-amber-50/60 dark:bg-amber-950/10 rounded-md border border-amber-100 dark:border-amber-900/30 text-[11px] text-amber-700 dark:text-amber-300 leading-relaxed">
                            {totals.invalid ? `${totals.invalid} input rejection(s) in ${rangeLabel}. Rejected inputs remain visible instead of being counted as normal inspections.` : `No rejected inputs in ${rangeLabel}.`}
                        </div>
                        <Button variant="secondary" className="w-full" icon={ArrowUpRight} onClick={() => navigate('/settings')}>Open System Settings</Button>
                    </div>
                </Card>
            </div>
        </div>
    );
};

export default Dashboard;
