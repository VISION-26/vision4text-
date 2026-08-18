import React, { useContext, useEffect, useMemo, useState } from 'react';
import { DetectionContext } from '../../context/DetectionContext';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import SectionTitle from '../../components/common/SectionTitle';
import Badge from '../../components/common/Badge';
import PDFButton from '../../components/common/PDFButton';
import ImageViewer from '../../components/common/ImageViewer';
import {
    Search, Trash2, ArrowLeft, AlertTriangle, User, Calendar, Cpu, Activity,
    ShieldCheck, Archive, Loader2, Image as ImageIcon, Ban
} from 'lucide-react';

const reportStatus = (report) => {
    if (report.prediction === 'Invalid Input' || report.rejectionCode) return { label: 'INPUT REJECTED', variant: 'warning', invalid: true };
    if (report.resultValid === false) return { label: 'NOT VALID', variant: 'warning', invalid: true };
    if (report.prediction === 'Anomalous') return { label: 'ANOMALOUS', variant: 'danger', invalid: false };
    return { label: 'NORMAL', variant: 'success', invalid: false };
};

const friendlyRoute = (value) => ({ stage3_stable: 'Stable Stage-3 refinement', stage2_fallback: 'Stage-2 fallback', specialist_only: 'Specialist-only route' }[value] || 'Recorded route');
const friendlyDecision = (value) => value?.includes('patchcore') ? 'PatchCore specialist decision' : value?.includes('efficientad') ? 'EfficientAD specialist decision' : value === 'localization_area_fallback' ? 'Localization fallback decision' : 'Recorded backend decision';
const friendlyLocalization = (value) => value?.includes('stage3') ? 'EVT-CLIP Stage-3 localization' : value?.includes('stage2') ? 'Stage-2 fused localization' : 'Recorded localization path';

const Reports = () => {
    const {
        history, historyTotal, jobs, loadOlderHistory, deleteReport, generateAndDownloadReport,
        downloadEvidenceBundle, loadAssetsForDetection,
    } = useContext(DetectionContext);
    const [selectedReportId, setSelectedReportId] = useState(() => sessionStorage.getItem('active_report_id') || null);
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedCategory, setSelectedCategory] = useState('all');
    const [downloading, setDownloading] = useState(false);
    const [bundleDownloading, setBundleDownloading] = useState(false);
    const [hydrating, setHydrating] = useState(false);
    const [error, setError] = useState('');
    const [notice, setNotice] = useState('');

    const selectedReport = useMemo(
        () => history.find((item) => String(item.id) === String(selectedReportId)) || null,
        [history, selectedReportId]
    );

    useEffect(() => {
        if (selectedReportId) sessionStorage.setItem('active_report_id', String(selectedReportId));
    }, [selectedReportId]);

    useEffect(() => {
        if (!selectedReportId || !selectedReport || selectedReport.originalImage) return;
        let active = true;
        setHydrating(true);
        setError('');
        loadAssetsForDetection(selectedReportId)
            .catch((err) => { if (active) setError(err.message || 'Unable to load stored visual evidence.'); })
            .finally(() => { if (active) setHydrating(false); });
        return () => { active = false; };
    }, [selectedReportId, selectedReport?.id, selectedReport?.originalImage, loadAssetsForDetection]);

    const handleBack = () => {
        setSelectedReportId(null);
        sessionStorage.removeItem('active_report_id');
        setError('');
    };

    const removeInspection = async (id, event) => {
        event?.stopPropagation();
        if (!window.confirm('Delete this inspection and all stored reports/visual assets?')) return;
        try {
            await deleteReport(id);
            if (String(selectedReportId) === String(id)) handleBack();
        } catch (err) {
            setError(err.message || 'Delete failed.');
        }
    };

    const downloadPdf = async (id) => {
        setDownloading(true); setError(''); setNotice('');
        try { await generateAndDownloadReport(id); setNotice('PDF report downloaded.'); }
        catch (err) { setError(err.message || 'PDF generation failed.'); }
        finally { setDownloading(false); }
    };

    const downloadBundle = async (id) => {
        setBundleDownloading(true); setError(''); setNotice('');
        try { await downloadEvidenceBundle(id); setNotice('Evidence ZIP downloaded.'); }
        catch (err) { setError(err.message || 'Evidence ZIP generation failed.'); }
        finally { setBundleDownloading(false); }
    };

    const categories = Array.from(new Set(history.map((item) => item.category).filter(Boolean)));
    const filtered = history.filter((item) => {
        const q = searchTerm.trim().toLowerCase();
        const matchesText = !q || [item.imageName, item.prediction, item.category, item.reviewReason, item.rejectionCode]
            .some((value) => String(value || '').toLowerCase().includes(q));
        return matchesText && (selectedCategory === 'all' || item.category === selectedCategory);
    });

    if (selectedReport) {
        const status = reportStatus(selectedReport);
        const valid = selectedReport.resultValid !== false && !status.invalid;
        const inferenceSeconds = Number(selectedReport.inferenceSeconds ?? (selectedReport.inferenceTime || 0) / 1000);
        return (
            <div className="space-y-6 font-sans">
                <div className="flex flex-wrap items-center justify-between gap-3">
                    <Button variant="secondary" size="sm" onClick={handleBack} icon={ArrowLeft}>Back to Reports</Button>
                    <div className="flex flex-wrap gap-2">
                        <PDFButton onClick={() => downloadPdf(selectedReport.id)} loading={downloading}/>
                        <Button variant="secondary" onClick={() => downloadBundle(selectedReport.id)} disabled={bundleDownloading} icon={Archive}>{bundleDownloading ? 'Building Evidence ZIP…' : 'Download Evidence ZIP'}</Button>
                        <Button variant="danger" size="sm" onClick={(e) => removeInspection(selectedReport.id, e)} icon={Trash2}>Delete Inspection</Button>
                    </div>
                </div>

                <SectionTitle title={`Report: ${selectedReport.imageName}`} subtitle="Stored EVT-CLIP inspection" />
                {error && <div className="p-3 rounded-md border border-rose-200 bg-rose-50 dark:bg-rose-950/20 text-rose-700 dark:text-rose-300 text-xs">{error}</div>}
                {notice && <div role="status" className="p-3 rounded-md border border-emerald-200 bg-emerald-50 dark:bg-emerald-950/20 text-emerald-700 dark:text-emerald-300 text-xs">{notice}</div>}

                {status.invalid && (
                    <div className="p-5 rounded-md border border-amber-300 bg-amber-50 dark:bg-amber-950/20 text-amber-900 dark:text-amber-200 flex gap-3">
                        <Ban size={22} className="shrink-0" />
                        <div>
                            <b>{selectedReport.rejectionCode === 'invalid_category' ? 'Incorrect product category — model evidence blocked.' : selectedReport.rejectionCode === 'unsupported_input' ? 'Unsupported image — model evidence blocked.' : 'Inspection is not valid for automated acceptance.'}</b>
                            <p className="text-xs mt-1 leading-relaxed">{selectedReport.notes || selectedReport.reviewReason || 'The safety gate did not validate this input.'}</p>
                            <p className="text-[11px] mt-2 opacity-75">For safety, heatmaps, masks and overlays are not displayed for rejected/invalid inputs. The export still records the rejection metadata for auditability.</p>
                        </div>
                    </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
                    <Card><div className="flex items-center gap-3"><User size={18} className="text-together-magenta"/><div><span className="text-[10px] text-slate-400 font-bold block">OPERATOR</span><b className="text-xs">{selectedReport.operator || 'Authenticated user'}</b></div></div></Card>
                    <Card><div className="flex items-center gap-3"><Calendar size={18} className="text-together-orange"/><div><span className="text-[10px] text-slate-400 font-bold block">DATE</span><b className="text-xs">{selectedReport.timestamp}</b></div></div></Card>
                    <Card><div className="flex items-center gap-3"><Cpu size={18} className="text-together-periwinkle"/><div><span className="text-[10px] text-slate-400 font-bold block">CPU INFERENCE</span><b className="text-xs">{inferenceSeconds.toFixed(2)} s · {selectedReport.workerCache || 'cache state n/a'}</b></div></div></Card>
                    <Card><div className="flex items-center gap-3"><Activity size={18} className="text-emerald-500"/><div><span className="text-[10px] text-slate-400 font-bold block">DECISION</span><Badge variant={status.variant}>{status.label}</Badge></div></div></Card>
                </div>

                {hydrating && <Card><div className="flex items-center justify-center gap-2 py-10 text-xs text-slate-400"><Loader2 size={17} className="animate-spin"/>Loading stored visual evidence only for this report…</div></Card>}
                {!hydrating && valid && <ImageViewer originalSrc={selectedReport.originalImage} heatmapSrc={selectedReport.heatmapImage} maskSrc={selectedReport.maskImage} overlaySrc={selectedReport.overlayImage} anomalyScore={selectedReport.anomalyScore}/>} 
                {!hydrating && !valid && selectedReport.originalImage && (
                    <Card title="Submitted Input" subtitle="Original image only; AI localization evidence is intentionally hidden because the category/input failed validation.">
                        <div className="bg-together-night rounded-md min-h-72 flex items-center justify-center overflow-hidden"><img src={selectedReport.originalImage} alt="Rejected input" className="max-h-[420px] max-w-full object-contain"/></div>
                    </Card>
                )}

                {!hydrating && valid && (
                    <Card title="Complete Model Evidence" subtitle="Stored backend outputs from preprocessing through Stage-3 refinement.">
                        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6 gap-3">
                            {[
                                ['Preprocessed', selectedReport.preprocessedImage, 'Model input preview'],
                                ['EfficientAD', selectedReport.efficientadHeatmapImage, selectedReport.efficientadImageScore == null ? 'Specialist map' : `Score ${selectedReport.efficientadImageScore.toFixed(4)}`],
                                ['PatchCore', selectedReport.patchcoreHeatmapImage, selectedReport.patchcoreImageScore == null ? 'Specialist map' : `Score ${selectedReport.patchcoreImageScore.toFixed(4)}`],
                                ['Stage-2', selectedReport.stage2HeatmapImage, selectedReport.stage2MapScore == null ? 'Fusion map' : `Peak ${selectedReport.stage2MapScore.toFixed(4)}`],
                                ['Stage-3 EVT-CLIP', selectedReport.stage3HeatmapImage, selectedReport.stage3MapScore == null ? 'Refined map' : `Peak ${selectedReport.stage3MapScore.toFixed(4)}`],
                                ['Defect location', selectedReport.defectBbox ? selectedReport.bboxOverlayImage : null, selectedReport.defectBbox ? `Mask bbox ${selectedReport.defectBbox.width}×${selectedReport.defectBbox.height}` : 'No accepted defect box'],
                            ].filter(([, src]) => Boolean(src)).map(([label, src, caption]) => (
                                <div key={label} className="overflow-hidden rounded-md border border-slate-200 dark:border-slate-800">
                                    <div className="aspect-square bg-together-night flex items-center justify-center">
                                        {src ? <img src={src} alt={label} className="max-h-full max-w-full object-contain"/> : <span className="px-3 text-center text-[10px] text-slate-500">Unavailable for this stored run</span>}
                                    </div>
                                    <div className="p-2.5"><b className="text-[11px] block">{label}</b><span className="text-[9px] text-slate-400">{caption}</span></div>
                                </div>
                            ))}
                        </div>
                    </Card>
                )}

                <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                    <Card title="Production Decision Evidence" subtitle="Values persisted from the backend pipeline">
                        <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-4 text-xs">
                            <div><dt className="text-slate-400">Anomaly score</dt><dd className="font-mono font-bold mt-1">{Number(selectedReport.anomalyScore || 0).toFixed(4)}</dd></div>
                            <div><dt className="text-slate-400">Confidence</dt><dd className="font-mono font-bold mt-1">{(Number(selectedReport.confidence || 0) * 100).toFixed(1)}%</dd></div>
                            <div><dt className="text-slate-400">Selected category</dt><dd className="font-bold mt-1 capitalize">{selectedReport.category?.replace('_', ' ')}</dd></div>
                            <div><dt className="text-slate-400">Predicted category</dt><dd className="font-bold mt-1 capitalize">{selectedReport.predictedCategory?.replace('_', ' ') || 'not available'}</dd></div>
                            <div><dt className="text-slate-400">Category validator</dt><dd className="font-bold mt-1 break-all">{selectedReport.categoryValidator || 'not available'}</dd></div>
                            <div><dt className="text-slate-400">Rejection code</dt><dd className="font-bold mt-1">{selectedReport.rejectionCode || 'none'}</dd></div>
                            <div><dt className="text-slate-400">Image quality</dt><dd className="font-bold mt-1">{selectedReport.imageQualityState || 'not recorded'}</dd></div>
                            <div><dt className="text-slate-400">Quality notice</dt><dd className="font-bold mt-1">{selectedReport.imageQualityMessage || 'none'}</dd></div>
                            <div><dt className="text-slate-400">Primary specialist</dt><dd className="font-bold mt-1">{selectedReport.primarySpecialist === 'efficientad' ? 'EfficientAD' : selectedReport.primarySpecialist === 'patchcore' ? 'PatchCore' : (selectedReport.primarySpecialist || 'not applicable')}</dd></div>
                            <div><dt className="text-slate-400">Decision source</dt><dd className="font-bold mt-1">{friendlyDecision(selectedReport.decisionSource)}</dd><code className="mt-1 block break-all text-[9px] text-slate-400">{selectedReport.decisionSource || 'not available'}</code></div>
                            <div><dt className="text-slate-400">Route</dt><dd className="font-bold mt-1">{friendlyRoute(selectedReport.route)}</dd><code className="mt-1 block break-all text-[9px] text-slate-400">{selectedReport.route || 'not available'}</code></div>
                            <div><dt className="text-slate-400">Localization source</dt><dd className="font-bold mt-1">{friendlyLocalization(selectedReport.localizationSource)}</dd><code className="mt-1 block break-all text-[9px] text-slate-400">{selectedReport.localizationSource || 'not applicable'}</code></div>
                            <div><dt className="text-slate-400">Mask coverage</dt><dd className="font-bold mt-1">{((selectedReport.defectAreaFraction || 0) * 100).toFixed(2)}%</dd></div>
                            <div><dt className="text-slate-400">Defect pixels</dt><dd className="font-bold mt-1">{selectedReport.defectAreaPixels || 0}</dd></div>
                            <div><dt className="text-slate-400">Connected regions</dt><dd className="font-bold mt-1">{selectedReport.defectComponentCount || 0}</dd></div>
                            <div><dt className="text-slate-400">Bounding box</dt><dd className="font-mono font-bold mt-1">{selectedReport.defectBbox ? `x=${selectedReport.defectBbox.x}, y=${selectedReport.defectBbox.y}, w=${selectedReport.defectBbox.width}, h=${selectedReport.defectBbox.height}` : 'none'}</dd></div>
                        </dl>
                    </Card>
                    <Card title="Measured Worker Timing" subtitle="Actual backend timings captured for this scan">
                        <div className="grid grid-cols-2 gap-3 text-xs">
                            {[['Input validation', selectedReport.validationSeconds], ['EfficientAD', selectedReport.efficientadSeconds], ['PatchCore', selectedReport.patchcoreSeconds], ['EVT-CLIP refiner', selectedReport.refinerSeconds]].map(([label, value]) => (
                                <div key={label} className="p-3 rounded-md bg-slate-50 dark:bg-[#08152e]"><span className="block text-[10px] text-slate-400">{label}</span><b className="font-mono">{Number(value || 0).toFixed(3)} s</b></div>
                            ))}
                        </div>
                        <div className="mt-4 flex gap-3 text-xs leading-relaxed text-slate-500 dark:text-slate-400"><ShieldCheck size={20} className="shrink-0 text-emerald-500"/><p>PDF and Evidence ZIP are generated on the server from the persisted inspection. The ZIP additionally includes JSON metadata, permitted evidence files, a SHA-256 manifest and an HMAC-SHA256 signature so a holder of the deployment signing secret can verify integrity and authenticity later.</p></div>
                    </Card>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6 font-sans">
            <SectionTitle title="Inspection Reports" subtitle="Open a stored scan to lazy-load visual evidence, export a PDF, or download a tamper-evident evidence ZIP." badge={`${history.length} / ${historyTotal || history.length} Loaded`} />
            {error && <div className="p-3 rounded-md border border-rose-200 bg-rose-50 dark:bg-rose-950/20 text-rose-700 dark:text-rose-300 text-xs">{error}</div>}
            {notice && <div role="status" className="p-3 rounded-md border border-emerald-200 bg-emerald-50 dark:bg-emerald-950/20 text-emerald-700 dark:text-emerald-300 text-xs">{notice}</div>}
            {(jobs || []).some((job) => ['queued','starting','running'].includes(job.status)) && (
                <Card title="Inspections in progress" subtitle="Submitted jobs stay visible before a completed report exists.">
                    <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
                        {(jobs || []).filter((job) => ['queued','starting','running'].includes(job.status)).slice(0,6).map((job) => (
                            <div key={job.id} className="rounded-lg border border-violet-200 bg-violet-50 px-3 py-3 text-xs dark:border-violet-900/40 dark:bg-violet-950/20">
                                <div className="flex items-center justify-between gap-2"><b>Scan #{job.id}</b><Badge variant="info">{job.status.toUpperCase()}</Badge></div>
                                <p className="mt-2 capitalize text-slate-500">{String(job.category || '').replace('_',' ')}</p>
                                <p className="mt-1 text-[9px] text-slate-400">A report becomes available when the inspection reaches a terminal result.</p>
                            </div>
                        ))}
                    </div>
                </Card>
            )}
            <Card>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="relative md:col-span-2"><Search size={17} className="absolute left-3 top-3 text-slate-400"/><input value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} placeholder="Search image, decision, category, rejection…" className="w-full pl-10 pr-4 py-2.5 text-xs rounded-md border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-together-night/40 focus:outline-none" /></div>
                    <select value={selectedCategory} onChange={(e) => setSelectedCategory(e.target.value)} className="px-3 py-2.5 text-xs rounded-md border border-slate-200 dark:border-slate-800 bg-white dark:bg-together-night/40"><option value="all">All trained categories</option>{categories.map((cat) => <option key={cat} value={cat}>{cat.replace('_', ' ')}</option>)}</select>
                </div>
            </Card>

            {filtered.length === 0 ? <Card className="py-16 text-center text-slate-400">No inspection reports match the active filters.</Card> : (
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                    {filtered.map((rep) => {
                        const state = reportStatus(rep);
                        return (
                            <Card key={rep.id} className="cursor-pointer overflow-hidden" padding={false}>
                                <button className="block text-left w-full" onClick={() => setSelectedReportId(rep.id)}>
                                    <div className="aspect-video w-full bg-together-night flex items-center justify-center overflow-hidden border-b border-slate-100 dark:border-slate-800 relative">
                                        <div className="flex flex-col items-center gap-2 text-slate-500"><ImageIcon size={28}/><span className="text-[10px]">Open report to load stored evidence</span></div>
                                        <div className="absolute top-3 right-3 font-mono font-bold text-xs bg-black/75 text-white py-1 px-2 rounded">S {Number(rep.anomalyScore || 0).toFixed(2)}</div>
                                    </div>
                                    <div className="p-5 space-y-3">
                                        <div className="flex items-center justify-between gap-3"><span className="text-[10px] text-slate-400 font-mono">{rep.timestamp}</span><Badge variant={state.variant}>{state.label}</Badge></div>
                                        <h3 className="font-semibold text-sm truncate">{rep.imageName}</h3>
                                        <div className="flex items-center justify-between text-[11px] text-slate-500"><span className="capitalize">{rep.category?.replace('_', ' ')}</span><span>{Number(rep.inferenceSeconds || 0).toFixed(2)} s CPU</span></div>
                                        {rep.rejectionCode && <p className="text-[10px] text-amber-600 dark:text-amber-400">Safety gate: {rep.rejectionCode.replaceAll('_', ' ')}</p>}
                                    </div>
                                </button>
                                <div className="px-5 pb-4 flex flex-wrap justify-end gap-2">
                                    <Button variant="secondary" size="sm" onClick={() => setSelectedReportId(rep.id)}>Open Report</Button>
                                    <Button variant="secondary" size="sm" onClick={(e) => removeInspection(rep.id, e)} icon={Trash2}>Delete</Button>
                                </div>
                            </Card>
                        );
                    })}
                </div>
            )}
            {history.length < historyTotal && (
                <div className="flex justify-center"><Button variant="secondary" onClick={() => loadOlderHistory()}>Load Older 100 Reports</Button></div>
            )}
        </div>
    );
};

export default Reports;
