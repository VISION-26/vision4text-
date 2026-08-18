import React, { useEffect, useState } from 'react';
import { Activity, Clock, Cpu, Database, Download, FileText, HardDrive, RefreshCw, Trash2, Users } from 'lucide-react';
import api from '../../services/api';
import Badge from '../../components/common/Badge';
import Button from '../../components/common/Button';
import Card from '../../components/common/Card';
import SectionTitle from '../../components/common/SectionTitle';
import Table from '../../components/common/Table';

const Admin = () => {
    const [users, setUsers] = useState([]);
    const [logs, setLogs] = useState([]);
    const [stats, setStats] = useState(null);
    const [health, setHealth] = useState(null);
    const [error, setError] = useState('');
    const [refreshing, setRefreshing] = useState(false);
    const [backupBusy, setBackupBusy] = useState(false);
    const [jobs, setJobs] = useState([]);
    const [notice, setNotice] = useState('');

    const load = async () => {
        setRefreshing(true);
        setError('');
        try {
            const [userResponse, logResponse, statsResponse, healthResponse, jobsResponse] = await Promise.all([
                api.get('/users'),
                api.get('/admin/logs'),
                api.get('/admin/statistics'),
                api.get('/admin/system-health'),
                api.get('/detect/jobs', { params: { limit: 25 } }),
            ]);
            setUsers(userResponse.data);
            setLogs(logResponse.data.items);
            setStats(statsResponse.data);
            setHealth(healthResponse.data);
            setJobs(jobsResponse.data?.items || []);
        } catch (err) {
            setError(err.message || 'Admin status could not be loaded.');
        } finally {
            setRefreshing(false);
        }
    };

    useEffect(() => { load(); }, []);

    const remove = async (id) => {
        if (!window.confirm('Delete this user account?')) return;
        try {
            await api.delete(`/users/${id}`);
            await load();
        } catch (err) {
            setError(err.message || 'User could not be deleted.');
        }
    };

    const downloadDatabaseBackup = async () => {
        setBackupBusy(true);
        setError('');
        setNotice('');
        try {
            const response = await api.get('/admin/backup/database', {
                responseType: 'blob',
                timeout: 120000,
            });
            const disposition = response.headers?.['content-disposition'] || '';
            const match = disposition.match(/filename=\"?([^\";]+)\"?/i);
            const fallback = `evt-clip-v2-database-${new Date().toISOString().replace(/[:.]/g, '-')}.sqlite3`;
            const filename = match?.[1] || fallback;
            const url = URL.createObjectURL(response.data);
            const link = document.createElement('a');
            link.href = url;
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            link.remove();
            URL.revokeObjectURL(url);
            setNotice('Database backup created and downloaded.');
        } catch (err) {
            setError(err.message || 'Database backup could not be created.');
        } finally {
            setBackupBusy(false);
        }
    };

    const columns = [
        { key: 'full_name', header: 'User', render: (row) => <div><b>{row.full_name || 'Unnamed user'}</b><div className="text-xs text-slate-400">{row.email}</div></div> },
        { key: 'role', header: 'Role', render: (row) => <Badge variant={row.role === 'Admin' ? 'info' : 'warning'}>{row.role}</Badge> },
        { key: 'is_active', header: 'Status', render: (row) => <Badge variant={row.is_active ? 'success' : 'danger'}>{row.is_active ? 'Active' : 'Inactive'}</Badge> },
        { key: 'actions', header: '', render: (row) => <Button variant="secondary" size="sm" disabled={row.role === 'Admin'} onClick={() => remove(row.id)}><Trash2 size={14} /></Button> },
    ];

    const healthy = String(health?.status || '').toLowerCase() === 'healthy';
    const uptimeHours = Number(health?.uptime_seconds || 0) / 3600;
    const activeJobs = jobs.filter((job) => ['queued','starting','running'].includes(job.status));
    const failedJobs = jobs.filter((job) => ['failed','timed_out'].includes(job.status));

    return (
        <div className="space-y-6">
            <SectionTitle
                title="Admin Control Center"
                subtitle="Real account, audit, database, storage and web-runtime diagnostics from the secured API."
                actions={
                    <div className="flex flex-wrap items-center gap-2">
                        <Button variant="secondary" onClick={downloadDatabaseBackup} disabled={backupBusy} icon={Download}>
                            {backupBusy ? 'Creating Backup…' : 'Download DB Backup'}
                        </Button>
                        <Button variant="secondary" onClick={load} disabled={refreshing} icon={RefreshCw}>
                            {refreshing ? 'Refreshing…' : 'Refresh'}
                        </Button>
                    </div>
                }
            />
            {error && <div className="p-3 rounded-md border border-rose-200 bg-rose-50 dark:bg-rose-950/20 text-sm text-rose-600 dark:text-rose-300">{error}</div>}
            {notice && <div role="status" className="p-3 rounded-md border border-emerald-200 bg-emerald-50 dark:bg-emerald-950/20 text-sm text-emerald-700 dark:text-emerald-300">{notice}</div>}

            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <Card><div className="flex items-center justify-between"><div><span className="text-[10px] uppercase font-bold text-slate-400">Users</span><b className="block text-2xl mt-1">{stats?.total_users ?? users.length}</b></div><Users className="text-blue-500" size={22}/></div></Card>
                <Card><div className="flex items-center justify-between"><div><span className="text-[10px] uppercase font-bold text-slate-400">Scans</span><b className="block text-2xl mt-1">{stats?.total_detections ?? '—'}</b></div><Activity className="text-fuchsia-500" size={22}/></div></Card>
                <Card><div className="flex items-center justify-between"><div><span className="text-[10px] uppercase font-bold text-slate-400">Reports</span><b className="block text-2xl mt-1">{stats?.total_reports ?? '—'}</b></div><FileText className="text-violet-500" size={22}/></div></Card>
                <Card><div className="flex items-center justify-between"><div><span className="text-[10px] uppercase font-bold text-slate-400">Active Jobs</span><b className="block text-2xl mt-1">{activeJobs.length}</b></div><Cpu className="text-emerald-500" size={22}/></div></Card>
            </div>

            <Card title="System Health" subtitle="Web/API container and persistent application storage">
                <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-3 text-xs">
                    <div className="p-3 rounded-md bg-slate-50 dark:bg-[#08152e]"><span className="flex items-center gap-2 text-slate-400"><Database size={14}/>Database</span><Badge variant={health?.database_connected ? 'success' : 'danger'}>{health?.database_connected ? 'CONNECTED' : 'UNAVAILABLE'}</Badge></div>
                    <div className="p-3 rounded-md bg-slate-50 dark:bg-[#08152e]"><span className="flex items-center gap-2 text-slate-400"><HardDrive size={14}/>Storage</span><Badge variant={health?.upload_dir_writable && health?.report_dir_writable ? 'success' : 'danger'}>{health?.upload_dir_writable && health?.report_dir_writable ? 'WRITABLE' : 'DEGRADED'}</Badge></div>
                    <div className="p-3 rounded-md bg-slate-50 dark:bg-[#08152e]"><span className="flex items-center gap-2 text-slate-400"><Cpu size={14}/>Runtime</span><b className="block mt-2">CPU · {Number(health?.memory_usage_mb || 0).toFixed(0)} MB web RAM</b></div>
                    <div className="p-3 rounded-md bg-slate-50 dark:bg-[#08152e]"><span className="flex items-center gap-2 text-slate-400"><Clock size={14}/>Uptime</span><b className="block mt-2">{uptimeHours.toFixed(2)} h</b></div>
                    <div className="p-3 rounded-md bg-slate-50 dark:bg-[#08152e]"><span className="text-slate-400">Overall</span><Badge variant={healthy ? 'success' : 'warning'}>{health?.status || 'CHECKING'}</Badge><p className="mt-2 text-[9px] text-slate-400">Inference worker readiness is proven by queued scan jobs; this health card does not wake the heavy model container.</p></div>
                </div>
            </Card>

            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                <Card title="Inference Jobs" subtitle="Persistent queue records from the CPU inference path.">
                    <div className="grid grid-cols-2 gap-3 text-xs">
                        <div className="rounded-lg border border-violet-200 bg-violet-50 p-3 dark:border-violet-900/40 dark:bg-violet-950/20"><span className="text-slate-400">Active</span><b className="mt-1 block text-2xl">{activeJobs.length}</b></div>
                        <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 dark:border-amber-900/40 dark:bg-amber-950/20"><span className="text-slate-400">Failed / timed out</span><b className="mt-1 block text-2xl">{failedJobs.length}</b></div>
                    </div>
                    <div className="mt-3 space-y-2">{jobs.slice(0,5).map((job) => <div key={job.job_id} className="flex items-center justify-between gap-2 rounded-lg border border-slate-200 px-3 py-2 text-[10px] dark:border-slate-800"><span>Scan #{job.job_id} · <span className="capitalize">{String(job.category || '').replace('_',' ')}</span></span><Badge variant={['failed','timed_out'].includes(job.status) ? 'warning' : ['queued','starting','running'].includes(job.status) ? 'info' : 'success'}>{String(job.status).replace('_',' ').toUpperCase()}</Badge></div>)}</div>
                </Card>
                <Card title="Backup & Recovery" subtitle="The database backup is created from a consistent SQLite snapshot.">
                    <p className="text-xs leading-5 text-slate-500">Use the backup before major schema changes or final submission. Visual evidence files remain exportable per inspection through the signed Evidence ZIP.</p>
                    <Button className="mt-4 w-full" variant="secondary" onClick={downloadDatabaseBackup} disabled={backupBusy} icon={Download}>{backupBusy ? 'Creating Backup…' : 'Download Verified DB Backup'}</Button>
                </Card>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <Card title="Users" subtitle="Authenticated user directory" className="lg:col-span-2" padding={false}><Table columns={columns} data={users} /></Card>
                <Card title="Audit Trail" subtitle="Latest server events" padding={false}>
                    <div className="divide-y divide-slate-100 dark:divide-slate-800 max-h-[520px] overflow-auto">
                        {logs.map((log) => <div className="p-4 text-xs" key={log.id}><b>{log.action}</b><p className="text-slate-500 mt-1 line-clamp-2">{log.details || log.description || ''}</p><p className="text-slate-400 mt-1">{log.timestamp}</p></div>)}
                        {!logs.length && <p className="p-4 text-sm text-slate-400">No audit events yet.</p>}
                    </div>
                </Card>
            </div>
        </div>
    );
};

export default Admin;
