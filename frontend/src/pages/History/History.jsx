import React, { useContext, useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { DetectionContext } from '../../context/DetectionContext';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import SectionTitle from '../../components/common/SectionTitle';
import Badge from '../../components/common/Badge';
import Table from '../../components/common/Table';
import { Search, ArrowUpDown, Trash2, Eye, ChevronLeft, ChevronRight, RefreshCw, Calendar, Image as ImageIcon, FileText } from 'lucide-react';

const statusFor = (row) => {
    if (row.prediction === 'Invalid Input' || row.rejectionCode) return { text: 'INPUT REJECTED', variant: 'warning' };
    if (row.resultValid === false) return { text: 'NOT VALID', variant: 'warning' };
    if (row.prediction === 'Anomalous') return { text: 'ANOMALOUS', variant: 'danger' };
    return { text: 'NORMAL', variant: 'success' };
};

const History = () => {
    const { history, historyTotal, jobs, loadOlderHistory, deleteReport, generateAndDownloadReport } = useContext(DetectionContext);
    const navigate = useNavigate();
    const [params, setParams] = useSearchParams();
    const [searchTerm, setSearchTerm] = useState(params.get('search') || '');
    const [sortField, setSortField] = useState('timestamp');
    const [sortOrder, setSortOrder] = useState('desc');
    const [currentPage, setCurrentPage] = useState(1);
    const [categoryFilter, setCategoryFilter] = useState('all');
    const [statusFilter, setStatusFilter] = useState('all');
    const [actionError, setActionError] = useState('');
    const itemsPerPage = 10;

    useEffect(() => setSearchTerm(params.get('search') || ''), [params]);

    const updateSearch = (value) => {
        setSearchTerm(value); setCurrentPage(1);
        if (value) setParams({ search: value }); else setParams({});
    };

    const handleSort = (field) => {
        if (sortField === field) setSortOrder((prev) => prev === 'asc' ? 'desc' : 'asc');
        else { setSortField(field); setSortOrder('desc'); }
        setCurrentPage(1);
    };

    const handleDelete = async (id, event) => {
        event?.stopPropagation();
        if (window.confirm('Delete this inspection and its stored visual/report assets?')) await deleteReport(id);
    };

    const handleViewReport = (id) => {
        sessionStorage.setItem('active_report_id', String(id));
        navigate('/reports');
    };

    const handlePdf = async (id, event) => {
        event?.stopPropagation();
        setActionError('');
        try { await generateAndDownloadReport(id); }
        catch (error) { setActionError(error.message || 'PDF export failed.'); }
    };

    const sortedData = useMemo(() => {
        const q = searchTerm.trim().toLowerCase();
        const searched = history.filter((item) => {
            const textMatch = !q || [
                item.imageName, item.prediction, item.category,
                item.predictedCategory, item.reviewReason, item.rejectionCode,
                item.imageQualityState, item.imageQualityMessage, item.notes,
            ].some((value) => String(value || '').toLowerCase().includes(q));
            const categoryMatch = categoryFilter === 'all' || item.category === categoryFilter;
            const state = statusFor(item).text;
            const statusMatch = statusFilter === 'all' || state === statusFilter;
            return textMatch && categoryMatch && statusMatch;
        });
        return [...searched].sort((a, b) => {
            let rawA = a[sortField]; let rawB = b[sortField];
            if (sortField === 'timestamp') { rawA = new Date(rawA).getTime(); rawB = new Date(rawB).getTime(); }
            if (rawA < rawB) return sortOrder === 'asc' ? -1 : 1;
            if (rawA > rawB) return sortOrder === 'asc' ? 1 : -1;
            return 0;
        });
    }, [history, searchTerm, sortField, sortOrder, categoryFilter, statusFilter]);

    const totalPages = Math.max(1, Math.ceil(sortedData.length / itemsPerPage));
    useEffect(() => { if (currentPage > totalPages) setCurrentPage(totalPages); }, [currentPage, totalPages]);
    const paginatedData = sortedData.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage);

    const columns = [
        { key: 'timestamp', header: 'Inspection Date', render: (row) => <div className="flex items-center gap-2"><Calendar size={13} className="text-slate-400"/><span className="font-mono text-[10px] text-slate-400">{row.timestamp}</span></div> },
        { key: 'imageName', header: 'Image', render: (row) => <div className="flex items-center gap-3"><div className="w-10 h-8 rounded bg-together-night flex items-center justify-center border border-slate-200 dark:border-slate-800"><ImageIcon size={14} className="text-slate-500"/></div><span className="font-semibold text-xs truncate max-w-44">{row.imageName}</span></div> },
        { key: 'category', header: 'Selected / Detected', render: (row) => <div className="text-[11px]"><span className="capitalize font-semibold">{row.category?.replace('_', ' ')}</span>{row.predictedCategory && row.predictedCategory !== row.category && <span className="block text-amber-500 capitalize">→ {row.predictedCategory.replace('_', ' ')}</span>}</div> },
        { key: 'anomalyScore', header: 'Score', render: (row) => <span className="font-mono text-xs font-bold">{Number(row.anomalyScore || 0).toFixed(3)}</span> },
        { key: 'prediction', header: 'Decision', render: (row) => { const state = statusFor(row); return <div><Badge variant={state.variant}>{state.text}</Badge>{row.rejectionCode && <span className="block text-[9px] text-slate-400 mt-1">{row.rejectionCode.replaceAll('_', ' ')}</span>}</div>; } },
        { key: 'inferenceTime', header: 'CPU Time', render: (row) => <div className="font-mono text-[10px]"><span>{Number(row.inferenceSeconds || (row.inferenceTime || 0) / 1000).toFixed(2)} s</span>{row.workerCache && <span className="block text-slate-400">{row.workerCache}</span>}{row.imageQualityState && row.imageQualityState !== 'ok' && <span className="block text-amber-500">quality: {row.imageQualityState}</span>}</div> },
        { key: 'actions', header: 'Actions', render: (row) => <div className="flex flex-wrap gap-1"><Button variant="secondary" size="sm" onClick={() => handleViewReport(row.id)} icon={Eye}>Open</Button><Button variant="secondary" size="sm" onClick={(e) => handlePdf(row.id, e)} icon={FileText}>PDF</Button><Button variant="secondary" size="sm" onClick={(e) => { e.stopPropagation(); navigate('/detection', { state: { category: row.category } }); }} icon={RefreshCw}>Reinspect</Button><Button variant="secondary" size="sm" onClick={(e) => handleDelete(row.id, e)} icon={Trash2}>Delete</Button></div> },
    ];

    const rejected = history.filter((item) => item.prediction === 'Invalid Input' || item.rejectionCode).length;
    const normal = history.filter((item) => !item.rejectionCode && item.resultValid !== false && item.prediction === 'Normal').length;
    const categories = Array.from(new Set(history.map((item) => item.category).filter(Boolean))).sort();
    const activeJobs = (jobs || []).filter((job) => ['queued', 'starting', 'running'].includes(job.status));

    return (
        <div className="space-y-6 font-sans">
            <SectionTitle title="Detection History" subtitle="Stored results plus persistent CPU job status. Visual evidence is fetched only when a report is opened." badge={`${history.length} / ${historyTotal || history.length} Loaded`} />
            {actionError && <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700 dark:border-rose-900/40 dark:bg-rose-950/20 dark:text-rose-300">{actionError}</div>}
            {activeJobs.length > 0 && (
                <Card title="Inspections in progress" subtitle="These scans have been submitted but do not have a completed detection record yet.">
                    <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
                        {activeJobs.map((job) => <div key={job.id} className="rounded-lg border border-violet-200 bg-violet-50 p-3 text-xs dark:border-violet-900/40 dark:bg-violet-950/20"><div className="flex items-center justify-between gap-2"><b>Scan #{job.id}</b><Badge variant="info">{job.status.toUpperCase()}</Badge></div><p className="mt-2 capitalize text-slate-500">{String(job.category || '').replace('_',' ')}</p></div>)}
                    </div>
                </Card>
            )}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <Card><span className="text-[10px] uppercase font-bold text-slate-400">Loaded history</span><b className="block text-xl mt-1">{history.length}</b></Card>
                <Card><span className="text-[10px] uppercase font-bold text-slate-400">Rejected inputs</span><b className="block text-xl mt-1 text-amber-500">{rejected}</b></Card>
                <Card><span className="text-[10px] uppercase font-bold text-slate-400">Normal results</span><b className="block text-xl mt-1 text-sky-500">{normal}</b></Card>
            </div>
            <Card>
                <div className="grid gap-3 xl:grid-cols-[1.5fr_.55fr_.65fr_auto]">
                    <div className="relative"><Search size={18} className="absolute left-3 top-3 text-slate-400"/><input value={searchTerm} onChange={(e) => updateSearch(e.target.value)} placeholder="Search file, decision, category or rejection…" className="w-full pl-10 pr-4 py-2.5 text-xs rounded-md border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-together-night/40 focus:outline-none"/></div>
                    <select value={categoryFilter} onChange={(e) => { setCategoryFilter(e.target.value); setCurrentPage(1); }} className="rounded-md border border-slate-200 bg-white px-3 py-2.5 text-xs dark:border-slate-800 dark:bg-together-night/40"><option value="all">All categories</option>{categories.map((cat) => <option key={cat} value={cat}>{cat.replace('_',' ')}</option>)}</select>
                    <select value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setCurrentPage(1); }} className="rounded-md border border-slate-200 bg-white px-3 py-2.5 text-xs dark:border-slate-800 dark:bg-together-night/40"><option value="all">All decisions</option><option value="NORMAL">Normal</option><option value="ANOMALOUS">Anomalous</option><option value="INPUT REJECTED">Input rejected</option><option value="NOT VALID">Not valid</option></select>
                    <div className="flex flex-wrap gap-1 text-[10px] font-bold">{[["timestamp","Date"],["anomalyScore","Score"],["inferenceTime","CPU"]].map(([field,label]) => <button key={field} onClick={() => handleSort(field)} className={`flex items-center gap-1 px-2.5 py-2 border rounded-md ${sortField === field ? 'border-together-magenta text-together-magenta' : 'border-slate-200 dark:border-slate-800 text-slate-500'}`}>{label}{sortField === field && <ArrowUpDown size={11}/>}</button>)}</div>
                </div>
            </Card>
            <Table columns={columns} data={paginatedData} emptyMessage="No stored inspections match the current search." />
            <div className="flex flex-wrap items-center justify-between gap-3 text-xs text-slate-500">
                <span>Page {currentPage} of {totalPages} · {sortedData.length} loaded records · {historyTotal || history.length} total stored</span>
                <div className="flex flex-wrap gap-2">
                    {history.length < historyTotal && <Button variant="secondary" size="sm" onClick={() => loadOlderHistory()}>Load Older 100</Button>}
                    <Button variant="secondary" size="sm" disabled={currentPage === 1} onClick={() => setCurrentPage((p) => Math.max(1,p-1))} icon={ChevronLeft}/>
                    <Button variant="secondary" size="sm" disabled={currentPage === totalPages} onClick={() => setCurrentPage((p) => Math.min(totalPages,p+1))} icon={ChevronRight}/>
                </div>
            </div>
        </div>
    );
};

export default History;
