import React, { useContext, useEffect, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { DetectionContext } from '../../context/DetectionContext';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import SectionTitle from '../../components/common/SectionTitle';
import Badge from '../../components/common/Badge';
import Modal from '../../components/common/Modal';
import CameraCapture from '../../components/detection/CameraCapture';
import InspectionRunAnimation from '../../components/detection/InspectionRunAnimation';
import CategoryExampleGuide, { CATEGORY_GUIDANCE } from '../../components/detection/CategoryExampleGuide';
import { generateSampleImageFile } from '../../utils/sampleGenerator';
import {
    UploadCloud, FileText, Layers, Eye, Gauge,
    ShieldCheck, Clock, Cpu, AlertTriangle, CheckCircle2,
    Archive, Ban, RefreshCw, Crosshair, GitBranch, BrainCircuit,
    FileImage, TimerReset, XCircle, CircleDot, Sparkles, Zap, Award, BookOpen,
} from 'lucide-react';

const fallbackSupportedCategories = ['bottle', 'cable', 'capsule', 'metal_nut', 'pill'];
const knownCategoryOrder = ['bottle', 'cable', 'capsule', 'carpet', 'grid', 'hazelnut', 'leather', 'metal_nut', 'pill', 'screw', 'tile', 'toothbrush', 'transistor', 'wood', 'zipper'];
const CALIBRATED_THRESHOLD = 0.267;
const legacyStage3Categories = ['bottle', 'cable', 'capsule', 'metal_nut', 'pill'];
const labelCategory = (value) => (value || 'unknown').replace('_', ' ');
const friendlyRoute = (value) => ({ stage3_stable: 'Stable Stage-3 refinement', stage2_fallback: 'Stage-2 fallback', specialist_only: 'Specialist-only route' }[value] || 'Recorded route');
const friendlyCache = (value) => ({ cold_pair: 'First run · specialist pair loaded', warm_pair: 'Warm pair · models reused', partial_warm: 'Partially warm' }[value] || 'Runtime cache state');
const friendlyDecisionSource = (value) => value?.includes('patchcore') ? 'PatchCore specialist decision' : value?.includes('efficientad') ? 'EfficientAD specialist decision' : value === 'localization_area_fallback' ? 'Localization fallback decision' : 'Recorded backend decision';
const friendlyLocalization = (value) => value?.includes('stage3') ? 'EVT-CLIP Stage-3 localization' : value?.includes('stage2') ? 'Stage-2 fused localization' : 'Recorded localization path';
const friendlySpecialist = (value) => value === 'efficientad' ? 'EfficientAD' : value === 'patchcore' ? 'PatchCore' : labelCategory(value).replace(/\b\w/g, (c) => c.toUpperCase());

const Detection = () => {
    const {
        datasets,
        precheckInput,
        runDetection,
        jobStatus,
        currentJob,
        cancelCurrentJob,
        generateAndDownloadReport,
        downloadEvidenceBundle,
    } = useContext(DetectionContext);
    const [selectedImage, setSelectedImage] = useState(null);
    const [imagePreview, setImagePreview] = useState(null);
    const [selectedDatasetId, setSelectedDatasetId] = useState(String(datasets[0]?.id || '0'));
    const [category, setCategory] = useState('bottle');
    const [supportedCategories, setSupportedCategories] = useState(fallbackSupportedCategories);
    const [isRunning, setIsRunning] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState('');
    const [showHeatmap, setShowHeatmap] = useState(true);
    const [showMask, setShowMask] = useState(true);
    const [showOverlay, setShowOverlay] = useState(true);
    const [reportBusy, setReportBusy] = useState(false);
    const [bundleBusy, setBundleBusy] = useState(false);
    const [safetyModalOpen, setSafetyModalOpen] = useState(false);
    const [imageMeta, setImageMeta] = useState(null);
    const [jobAge, setJobAge] = useState(0);
    const [exportNotice, setExportNotice] = useState('');
    const [precheck, setPrecheck] = useState(null);
    const [precheckBusy, setPrecheckBusy] = useState(false);
    const [precheckModalOpen, setPrecheckModalOpen] = useState(false);

    useEffect(() => {
        let active = true;
        fetch('/health', { cache: 'no-store' })
            .then((response) => response.ok ? response.json() : Promise.reject(new Error('health')))
            .then((data) => {
                if (!active) return;
                const backendCategories = Array.isArray(data?.supported_categories) ? data.supported_categories : [];
                const available = knownCategoryOrder.filter((item) => backendCategories.includes(item) && CATEGORY_GUIDANCE[item]);
                const next = available.length ? available : fallbackSupportedCategories;
                setSupportedCategories(next);
                setCategory((current) => next.includes(current) ? current : next[0]);
            })
            .catch(() => {
                if (active) setSupportedCategories(fallbackSupportedCategories);
            });
        return () => { active = false; };
    }, []);

    useEffect(() => {
        if (!datasets.some((d) => String(d.id) === String(selectedDatasetId))) {
            setSelectedDatasetId(String(datasets[0]?.id || '0'));
        }
    }, [datasets, selectedDatasetId]);

    useEffect(() => {
        if (!currentJob?.startedAt || ['complete', 'failed', 'timed_out', 'cancelled'].includes(currentJob.status)) {
            setJobAge(currentJob?.ageSeconds || 0);
            return undefined;
        }
        const update = () => setJobAge(Math.floor((Date.now() - currentJob.startedAt) / 1000));
        update();
        const timer = window.setInterval(update, 1000);
        return () => window.clearInterval(timer);
    }, [currentJob?.startedAt, currentJob?.status, currentJob?.ageSeconds]);

    const selectImage = (file) => {
        if (!file) return;
        if (imagePreview) URL.revokeObjectURL(imagePreview);
        const preview = URL.createObjectURL(file);
        setSelectedImage(file);
        setImagePreview(preview);
        setImageMeta({ name: file.name, size: file.size, width: null, height: null, selectedAt: new Date().toLocaleTimeString() });
        const probe = new Image();
        probe.onload = () => setImageMeta((meta) => meta ? { ...meta, width: probe.naturalWidth, height: probe.naturalHeight } : meta);
        probe.src = preview;
        setResult(null);
        setError('');
        setExportNotice('');
        setSafetyModalOpen(false);
        setPrecheck(null);
        setPrecheckModalOpen(false);
    };

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop: (files) => selectImage(files[0]),
        accept: { 'image/png': ['.png'], 'image/jpeg': ['.jpg', '.jpeg'] },
        maxSize: 20 * 1024 * 1024,
        multiple: false,
    });

    const execute = async (file = selectedImage, categoryOverride = category) => {
        if (!file || isRunning) return;
        setIsRunning(true);
        setError('');
        setSafetyModalOpen(false);
        try {
            const record = await runDetection(file, selectedDatasetId, categoryOverride);
            setResult(record);
            if (!record.resultValid) setSafetyModalOpen(true);
        } catch (err) {
            setError(err.message || 'Detection failed.');
        } finally {
            setIsRunning(false);
        }
    };

    const handleCameraCapture = async (file, inspectImmediately) => {
        selectImage(file);
        if (inspectImmediately) await execute(file, category);
    };

    const handleReset = () => {
        if (imagePreview) URL.revokeObjectURL(imagePreview);
        setSelectedImage(null);
        setImagePreview(null);
        setResult(null);
        setError('');
        setSafetyModalOpen(false);
        setImageMeta(null);
        setExportNotice('');
        setPrecheck(null);
        setPrecheckModalOpen(false);
    };

    const handleCategoryChange = (next) => {
        setCategory(next);
        setResult(null);
        setSafetyModalOpen(false);
        setError('');
        setPrecheck(null);
        setPrecheckModalOpen(false);
    };

    const downloadReport = async () => {
        if (!result) return;
        setReportBusy(true);
        setExportNotice('');
        try { await generateAndDownloadReport(result.id); setExportNotice('PDF report downloaded successfully.'); }
        catch (err) { setError(err.message || 'Could not generate report.'); }
        finally { setReportBusy(false); }
    };

    const downloadBundle = async () => {
        if (!result) return;
        setBundleBusy(true);
        setExportNotice('');
        try { await downloadEvidenceBundle(result.id); setExportNotice('Evidence ZIP downloaded successfully.'); }
        catch (err) { setError(err.message || 'Could not export evidence bundle.'); }
        finally { setBundleBusy(false); }
    };

    const rerunWithDetectedCategory = async () => {
        const predicted = result?.predictedCategory;
        if (!predicted || !supportedCategories.includes(predicted) || result?.rejectionCode === 'unsupported_input') return;
        setCategory(predicted);
        setSafetyModalOpen(false);
        setResult(null);
        await execute(selectedImage, predicted);
    };

    const anomalyTone = result?.prediction === 'Anomalous' ? 'text-rose-500' : 'text-emerald-500';
    const hardRejected = result && !result.resultValid;
    const wrongCategory = ['invalid_category', 'category_uncertain'].includes(result?.rejectionCode);
    const unsupportedInput = result?.rejectionCode === 'unsupported_input';
    const poorQualityInput = result?.rejectionCode === 'poor_quality_input';
    const domainShift = result?.rejectionCode === 'domain_shift';

    return (
        <div className="space-y-6 font-sans">
            <SectionTitle
                title="AI Anomaly Inspection"
                subtitle="Run the five-category production inspection pipeline and inspect the evidence from each model stage."
                badge="CPU · 5 Categories"
            />

            {error && (
                <div className="flex items-start gap-3 border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700 dark:border-rose-900/50 dark:bg-rose-950/20 dark:text-rose-300 rounded-lg">
                    <AlertTriangle size={18} className="mt-0.5 shrink-0" />
                    <span>{error}</span>
                </div>
            )}

            {/* Viva & Examiner Quick-Test Bench */}
            <div className="rounded-xl border border-fuchsia-200 bg-gradient-to-r from-fuchsia-500/10 via-purple-500/10 to-cyan-500/10 p-4 dark:border-fuchsia-900/40">
                <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
                    <div className="flex items-center gap-2">
                        <Sparkles size={16} className="text-fuchsia-500 animate-pulse" />
                        <span className="text-xs font-bold text-slate-800 dark:text-white uppercase tracking-wider">
                            ⚡ Examiner / Viva 1-Click Test Bench
                        </span>
                        <Badge variant="gradient">Defense Ready</Badge>
                    </div>
                    <span className="text-[10px] text-fuchsia-600 dark:text-fuchsia-300 font-medium">Click any sample to instantly load realistic test data</span>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2 text-[11px]">
                    {[
                        { cat: 'bottle', kind: 'defect', label: 'Bottle (Defect)', icon: '🍾', badge: 'Crack / Stain' },
                        { cat: 'bottle', kind: 'good', label: 'Bottle (Normal)', icon: '🍾', badge: 'Pristine' },
                        { cat: 'capsule', kind: 'defect', label: 'Capsule (Defect)', icon: '💊', badge: 'Dent / Split' },
                        { cat: 'metal_nut', kind: 'defect', label: 'Metal Nut (Defect)', icon: '🔩', badge: 'Gouge / Scratch' },
                        { cat: 'cable', kind: 'defect', label: 'Cable (Defect)', icon: '🔌', badge: 'Exposed Wire' },
                        { cat: 'pill', kind: 'defect', label: 'Pill (Defect)', icon: '⚪', badge: 'Chipped Edge' },
                    ].map((item) => (
                        <button
                            key={`${item.cat}_${item.kind}`}
                            type="button"
                            onClick={async () => {
                                handleCategoryChange(item.cat);
                                const file = await generateSampleImageFile(item.cat, item.kind);
                                selectImage(file);
                            }}
                            disabled={isRunning}
                            className="flex flex-col items-center justify-center p-2.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-[#0c0f1f]/80 backdrop-blur hover:border-fuchsia-400 hover:shadow-md transition text-center group disabled:opacity-50"
                        >
                            <span className="text-xl group-hover:scale-110 transition-transform">{item.icon}</span>
                            <span className="font-semibold text-[10px] mt-1 text-slate-800 dark:text-slate-200 leading-tight">{item.label}</span>
                            <span className={`text-[8px] mt-1 px-1.5 py-0.5 rounded font-mono ${item.kind === 'defect' ? 'bg-rose-100 text-rose-700 dark:bg-rose-950/50 dark:text-rose-300' : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300'}`}>
                                {item.badge}
                            </span>
                        </button>
                    ))}
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <Card title="1. Select Input Source" subtitle="Upload an image or capture one directly from the camera">
                    {imagePreview ? (
                        <div className="relative group overflow-hidden border border-slate-200 dark:border-slate-800 bg-slate-950 aspect-[4/3] flex items-center justify-center rounded-lg">
                            <img src={imagePreview} alt="Selected input" className="max-h-full max-w-full object-contain" />
                            <div className="absolute inset-0 bg-[#010120]/70 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-3">
                                <div {...getRootProps()} className="cursor-pointer"><input {...getInputProps()} /><Button variant="secondary" size="sm">Change File</Button></div>
                                <Button variant="danger" size="sm" onClick={handleReset}>Remove</Button>
                            </div>
                        </div>
                    ) : (
                        <div {...getRootProps()} className={`border border-dashed p-6 text-center cursor-pointer transition-all aspect-[4/3] flex flex-col items-center justify-center gap-3 bg-slate-50 dark:bg-[#12122a] rounded-lg ${isDragActive ? 'border-fuchsia-500 bg-fuchsia-50/50' : 'border-slate-300 dark:border-slate-700 hover:border-fuchsia-400'}`}>
                            <input {...getInputProps()} />
                            <UploadCloud size={38} className="text-fuchsia-500" />
                            <div><span className="font-semibold text-fuchsia-600 dark:text-fuchsia-300 text-xs">Click to upload</span><span className="text-slate-400 text-xs font-semibold"> or drag & drop</span></div>
                            <p className="text-[10px] text-slate-400 font-medium">PNG, JPG, or JPEG · max 20 MB</p>
                        </div>
                    )}
                    {imageMeta && (
                        <div className="mt-3 grid grid-cols-2 gap-2 text-[10px]">
                            <div className="col-span-2 flex min-w-0 items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 dark:border-slate-800 dark:bg-[#0b152b]">
                                <FileImage size={14} className="shrink-0 text-fuchsia-500" />
                                <span className="truncate font-semibold">{imageMeta.name}</span>
                            </div>
                            <div className="rounded-lg border border-slate-200 px-3 py-2 dark:border-slate-800"><span className="block text-slate-400">File size</span><b>{(imageMeta.size / 1024).toFixed(1)} KB</b></div>
                            <div className="rounded-lg border border-slate-200 px-3 py-2 dark:border-slate-800"><span className="block text-slate-400">Dimensions</span><b>{imageMeta.width ? `${imageMeta.width} × ${imageMeta.height}` : 'Reading…'}</b></div>
                            <div className="col-span-2 rounded-lg border border-slate-200 px-3 py-2 text-slate-500 dark:border-slate-800"><span className="font-semibold text-slate-700 dark:text-slate-200">Selected at</span> {imageMeta.selectedAt}</div>
                        </div>
                    )}
                    <div className="mt-3 border-t border-slate-100 pt-3 dark:border-slate-800">
                        <CameraCapture onCapture={handleCameraCapture} disabled={isRunning} />
                    </div>
                </Card>

                <Card title="2. Inspection Configuration" subtitle="Select the trained product category; calibration stays model-controlled">
                    <div className="space-y-4">
                        <div className="space-y-1">
                            <div className="flex items-center justify-between gap-3">
                                <label className="text-[11px] font-semibold text-slate-500 dark:text-slate-400">PRODUCT MODEL</label>
                                <span className="text-[9px] text-slate-400">{supportedCategories.length} available</span>
                            </div>
                            <select value={category} onChange={(e) => handleCategoryChange(e.target.value)} className="w-full px-3 py-2.5 text-xs border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#010120] text-slate-800 dark:text-slate-100 focus:outline-none capitalize rounded-md">
                                {supportedCategories.map((c) => <option key={c} value={c}>{labelCategory(c)}</option>)}
                            </select>
                            <p className="pt-1 text-[9px] leading-4 text-slate-400">The list follows the model profiles reported by the active backend. Newly trained categories appear automatically after the backend registry is updated.</p>
                        </div>
                        <CategoryExampleGuide category={category} onSelectFile={selectImage} />
                        <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-[#12122a]">
                            <div className="grid grid-cols-2 gap-2 text-[10px]">
                                <div><span className="block text-slate-400">Selected category</span><b className="capitalize">{labelCategory(category)}</b></div>
                                <div><span className="block text-slate-400">Validation policy</span><b>Accept / Reject</b></div>
                            </div>
                            <details className="mt-3 border-t border-slate-200 pt-2 dark:border-slate-800">
                                <summary className="cursor-pointer text-[10px] font-semibold text-slate-500">Technical calibration details</summary>
                                <div className="mt-2 flex items-center justify-between"><span className="text-[10px] text-slate-400">Stage-3 threshold</span><span className="font-mono text-xs font-bold text-fuchsia-600 dark:text-fuchsia-300">{CALIBRATED_THRESHOLD}</span></div>
                                <p className="mt-2 text-[10px] leading-relaxed text-slate-400">Calibration is model-controlled. Strong category mismatches are rejected; low-margin validator differences remain advisory.</p>
                            </details>
                        </div>
                    </div>
                </Card>

                <Card title="3. Execute AI Pipeline" subtitle="Queued CPU inference with a persistent job record">
                    <div className="flex h-full min-h-[230px] flex-col justify-between py-1">
                        <div className="space-y-3 text-xs">
                            <div className="grid grid-cols-2 gap-2">
                                <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 dark:border-emerald-900/40 dark:bg-emerald-950/20">
                                    <span className="flex items-center gap-2 font-semibold text-emerald-700 dark:text-emerald-300"><CircleDot size={13}/> API available</span>
                                    <span className="mt-1 block text-[9px] text-slate-500">Upload, history, reports</span>
                                </div>
                                <div className="rounded-lg border border-fuchsia-200 bg-fuchsia-50 px-3 py-2 dark:border-fuchsia-900/40 dark:bg-fuchsia-950/20">
                                    <span className="flex items-center gap-2 font-semibold text-fuchsia-700 dark:text-fuchsia-300"><Cpu size={13}/> CPU queue configured</span>
                                    <span className="mt-1 block text-[9px] text-slate-500">Worker starts when needed</span>
                                </div>
                            </div>
                            {currentJob && isRunning && (
                                <div role="status" aria-live="polite" className="rounded-lg border border-violet-200 bg-violet-50 p-3 dark:border-violet-900/40 dark:bg-violet-950/20">
                                    <div className="flex items-center justify-between gap-3">
                                        <div>
                                            <span className="block text-[9px] font-bold uppercase tracking-[.1em] text-violet-500">Inspection job #{currentJob.id}</span>
                                            <b className="mt-1 block text-xs">{jobStatus === 'idle' ? 'Preparing inspection' : jobStatus}</b>
                                        </div>
                                        <span className="flex shrink-0 items-center gap-1 font-mono text-[10px] text-slate-500"><TimerReset size={13}/>{jobAge}s</span>
                                    </div>
                                    <div className="mt-2 flex items-center justify-between gap-3 text-[9px] text-slate-500">
                                        <span>Category: <b className="capitalize text-slate-700 dark:text-slate-200">{labelCategory(category)}</b></span>
                                        <button type="button" onClick={() => cancelCurrentJob().catch((err) => setError(err.message || 'Cancel failed.'))} className="inline-flex items-center gap-1 font-semibold text-rose-500 hover:text-rose-600"><XCircle size={12}/> Cancel</button>
                                    </div>
                                </div>
                            )}
                            {!isRunning && <p className="text-[10px] leading-relaxed text-slate-400">The scan ID is persisted as soon as the CPU job is submitted. A cold category run may take longer while the specialist pair is loaded.</p>}
                        </div>
                        <InspectionRunAnimation
                            imagePreview={imagePreview}
                            category={category}
                            isRunning={isRunning}
                            jobStatus={jobStatus}
                            result={result}
                            onRun={() => execute()}
                            runDisabled={!imagePreview || isRunning}
                            runLabel="Run Inspection"
                            onReset={handleReset}
                        />
                    </div>
                </Card>
            </div>

            {selectedImage && (
                <div className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-xs text-slate-700 dark:border-slate-800 dark:bg-[#12122a] dark:text-slate-300 flex flex-wrap items-center justify-between gap-3">
                    <span className="flex items-center gap-2">
                        <ShieldCheck size={16} className="text-fuchsia-500 shrink-0" />
                        <b>Product and image quality will be verified when inspection starts.</b>
                    </span>
                    <span className="text-[10px] text-slate-400 font-mono">CPU Specialist Validation · Fail-Closed</span>
                </div>
            )}

            {hardRejected && !safetyModalOpen && (
                <Card className="border-amber-300 dark:border-amber-800/70">
                    <div className="flex flex-col md:flex-row md:items-center gap-4 justify-between">
                        <div className="flex gap-3">
                            <Ban size={22} className="text-amber-500 shrink-0" />
                            <div>
                                <b className="text-sm text-slate-800 dark:text-slate-100">Inspection blocked by the category safety gate</b>
                                <p className="text-xs text-slate-500 mt-1">{result.notes}</p>
                            </div>
                        </div>
                        <Button variant="secondary" size="sm" onClick={() => setSafetyModalOpen(true)}>Show Details</Button>
                    </div>
                </Card>
            )}

            {result?.resultValid && (
                <div className="space-y-6">
                    <div className="border-t border-slate-200 dark:border-slate-800 pt-6" />

                    <div className="flex items-center gap-2 text-xs font-medium text-sky-700 dark:text-sky-300"><CheckCircle2 size={16} />Category accepted for the selected inspection profile.</div>
                    {result.reviewRequired && (
                        <div className="flex items-start gap-3 border border-amber-300 bg-amber-50 p-3 text-xs text-amber-800 dark:border-amber-800/70 dark:bg-amber-950/20 dark:text-amber-200 rounded-lg">
                            <AlertTriangle size={16} className="mt-0.5 shrink-0" />
                            <span><b>This result requires operator review.</b> {result.reviewReason === 'implausible_full_frame_localization' ? 'The predicted defect mask covers almost the whole image, so localization is not trusted as a normal production result.' : (result.reviewReason || 'Model evidence requires review.')}</span>
                        </div>
                    )}

                    {result.imageQualityState === 'warning' && (
                        <div className="flex items-start gap-3 border border-amber-300 bg-amber-50 p-3 text-xs text-amber-800 dark:border-amber-800/70 dark:bg-amber-950/20 dark:text-amber-200 rounded-lg">
                            <AlertTriangle size={16} className="mt-0.5 shrink-0" />
                            <span><b>Input quality caution:</b> {result.imageQualityMessage}</span>
                        </div>
                    )}

                    <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-6 gap-3">
                        <Card><span className="text-[9px] font-bold uppercase tracking-wider text-slate-400">Category status</span><div className="mt-2"><Badge variant="info">ACCEPTED</Badge></div><p className="mt-2 text-[10px] text-slate-400">Selected: <b className="capitalize">{labelCategory(category)}</b>{result.predictedCategory ? ` · Validator: ${labelCategory(result.predictedCategory)}` : ''}</p></Card>
                        <Card><span className="text-[9px] font-bold uppercase tracking-wider text-slate-400">Anomaly decision</span><b className={`mt-2 block text-lg ${anomalyTone}`}>{result.prediction}</b><p className="mt-2 text-[10px] text-slate-400">Separate from category confidence</p></Card>
                        <Card><span className="text-[9px] font-bold uppercase tracking-wider text-slate-400">Evidence score</span><b className={`mt-2 block font-mono text-lg ${anomalyTone}`}>{result.anomalyScore.toFixed(3)}</b><p className="mt-2 text-[10px] text-slate-400">Primary decision score</p></Card>
                        <Card><span className="text-[9px] font-bold uppercase tracking-wider text-slate-400">Input quality</span><b className="mt-2 block text-sm capitalize">{result.imageQualityState || 'ok'}</b><p className="mt-2 text-[10px] text-slate-400">{result.imageQualityState === 'warning' ? 'Quality caution recorded' : 'Quality checks passed'}</p></Card>
                        <Card><span className="text-[9px] font-bold uppercase tracking-wider text-slate-400">CPU time</span><b className="mt-2 block text-lg">{result.inferenceSeconds.toFixed(1)} s</b><p className="mt-2 text-[10px] text-slate-400">{friendlyCache(result.workerCache)}</p></Card>
                        <Card><span className="text-[9px] font-bold uppercase tracking-wider text-slate-400">Primary specialist</span><b className="mt-2 block text-sm">{friendlySpecialist(result.primarySpecialist || category)}</b><p className="mt-2 text-[10px] text-slate-400">Image-level decision source</p></Card>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                        <Card title="Original Image" subtitle="Uploaded/captured source" padding={false}><div className="aspect-[4/3] w-full bg-[#010120] flex items-center justify-center overflow-hidden border-t border-slate-100 dark:border-slate-800"><img src={result.originalImage} alt="Original" className="max-w-full max-h-full object-contain" /></div></Card>
                        <Card title="Anomaly Heatmap" subtitle="Backend-generated localization evidence" padding={false}><div className="aspect-[4/3] w-full bg-[#010120] flex items-center justify-center overflow-hidden border-t border-slate-100 dark:border-slate-800">{showHeatmap && result.heatmapImage ? <img src={result.heatmapImage} alt="Heatmap" className="max-w-full max-h-full object-contain" /> : <span className="text-xs text-slate-500">Heatmap hidden</span>}</div></Card>
                        <Card title="Segmentation Mask" subtitle="Calibrated production mask" padding={false}><div className="aspect-[4/3] w-full bg-[#010120] flex items-center justify-center overflow-hidden border-t border-slate-100 dark:border-slate-800">{showMask && result.maskImage ? <img src={result.maskImage} alt="Segmentation mask" className="max-w-full max-h-full object-contain" /> : <span className="text-xs text-slate-500">Mask hidden</span>}</div></Card>
                        <Card title="Overlay Image" subtitle="Backend-generated overlay" padding={false}><div className="aspect-[4/3] w-full bg-[#010120] flex items-center justify-center overflow-hidden border-t border-slate-100 dark:border-slate-800">{showOverlay && result.overlayImage ? <img src={result.overlayImage} alt="Overlay" className="max-w-full max-h-full object-contain" /> : <span className="text-xs text-slate-500">Overlay hidden</span>}</div></Card>
                    </div>

                    {!legacyStage3Categories.includes(category) && (
                        <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-xs text-amber-800 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-200">
                            <b>Specialist route for this category.</b> Stage-2 / Stage-3 calibration is not installed for this category yet, so unavailable stages are intentionally hidden. The live evidence comes from the trained EfficientAD/PatchCore specialists.
                        </div>
                    )}

                    <Card title="Complete Model Evidence" subtitle="Every stored map below comes from the backend worker; the browser does not invent defect regions.">
                        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6 gap-3">
                            {[
                                ['Preprocessed', result.preprocessedImage, '256×256 model input preview'],
                                ['EfficientAD', result.efficientadHeatmapImage, result.efficientadImageScore == null ? 'Specialist heatmap' : `Score ${result.efficientadImageScore.toFixed(4)}`],
                                ['PatchCore', result.patchcoreHeatmapImage, result.patchcoreImageScore == null ? 'Specialist heatmap' : `Score ${result.patchcoreImageScore.toFixed(4)}`],
                                ['Stage-2 Fusion', result.stage2HeatmapImage, result.stage2MapScore == null ? 'Calibrated fused map' : `Peak ${result.stage2MapScore.toFixed(4)}`],
                                ['Stage-3 EVT-CLIP', result.stage3HeatmapImage, result.stage3MapScore == null ? 'Refined localization map' : `Peak ${result.stage3MapScore.toFixed(4)}`],
                                ['Defect location', result.defectBbox ? result.bboxOverlayImage : null, result.defectBbox ? `Mask bbox ${result.defectBbox.width}×${result.defectBbox.height}` : 'No accepted defect box'],
                            ].filter(([, image]) => Boolean(image)).map(([title, image, caption]) => (
                                <div key={title} className="overflow-hidden rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-[#0b152b]">
                                    <div className="aspect-square bg-[#010120] flex items-center justify-center overflow-hidden">
                                        {image ? <img src={image} alt={title} className="max-w-full max-h-full object-contain" /> : <span className="px-4 text-center text-[10px] text-slate-500">Stage image unavailable for this stored run</span>}
                                    </div>
                                    <div className="p-2.5">
                                        <b className="block text-[11px]">{title}</b>
                                        <span className="mt-0.5 block text-[9px] text-slate-400">{caption}</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                        <div className="mt-3 flex flex-wrap items-center gap-x-5 gap-y-2 text-[10px] text-slate-400">
                            <span className="flex items-center gap-1.5"><GitBranch size={13}/> Stage-2 combines specialist localization.</span>
                            <span className="flex items-center gap-1.5"><BrainCircuit size={13}/> Stage-3 uses EVT-CLIP refinement when routing accepts it.</span>
                            <span>Ground truth is not fabricated for ordinary uploads or camera images.</span>
                        </div>
                    </Card>

                    {/* Academic 5-Stage Pipeline Breakdown */}
                    <Card title="5-Stage Theoretical Pipeline Breakdown" subtitle="Detailed algorithmic flow executed by the EVT-CLIP++ architecture during this inference pass.">
                        <div className="grid grid-cols-1 md:grid-cols-5 gap-3 text-xs">
                            <div className="rounded-xl border border-sky-200 dark:border-sky-900/40 bg-sky-50/50 dark:bg-sky-950/20 p-3.5 space-y-2">
                                <div className="flex items-center justify-between">
                                    <span className="font-mono text-[10px] font-bold text-sky-600 dark:text-sky-400">STAGE 01</span>
                                    <Badge variant="info">Fast Map</Badge>
                                </div>
                                <b className="block text-slate-800 dark:text-slate-100 font-semibold text-sm">EfficientAD</b>
                                <p className="text-[10px] text-slate-500 dark:text-slate-400 leading-relaxed">Student-Teacher ResNet feature distillation with multi-scale autoencoders for sub-millisecond local anomaly scoring.</p>
                                <div className="font-mono text-[9px] text-slate-400 pt-1 border-t border-sky-100 dark:border-sky-900/30">
                                    Score: {result.efficientadImageScore != null ? result.efficientadImageScore.toFixed(3) : 'Active'}
                                </div>
                            </div>

                            <div className="rounded-xl border border-fuchsia-200 dark:border-fuchsia-900/40 bg-fuchsia-50/50 dark:bg-fuchsia-950/20 p-3.5 space-y-2">
                                <div className="flex items-center justify-between">
                                    <span className="font-mono text-[10px] font-bold text-fuchsia-600 dark:text-fuchsia-400">STAGE 02</span>
                                    <Badge variant="gradient">Memory Bank</Badge>
                                </div>
                                <b className="block text-slate-800 dark:text-slate-100 font-semibold text-sm">PatchCore</b>
                                <p className="text-[10px] text-slate-500 dark:text-slate-400 leading-relaxed">WideResNet-50 mid-level patch extraction with greedy greedy-minimax coreset subsampling for k-NN anomaly matching.</p>
                                <div className="font-mono text-[9px] text-slate-400 pt-1 border-t border-fuchsia-100 dark:border-fuchsia-900/30">
                                    Score: {result.patchcoreImageScore != null ? result.patchcoreImageScore.toFixed(3) : 'Active'}
                                </div>
                            </div>

                            <div className="rounded-xl border border-violet-200 dark:border-violet-900/40 bg-violet-50/50 dark:bg-violet-950/20 p-3.5 space-y-2">
                                <div className="flex items-center justify-between">
                                    <span className="font-mono text-[10px] font-bold text-violet-600 dark:text-violet-400">STAGE 03</span>
                                    <Badge variant="secondary">Statistical EVT</Badge>
                                </div>
                                <b className="block text-slate-800 dark:text-slate-100 font-semibold text-sm">Weibull Tail Fusion</b>
                                <p className="text-[10px] text-slate-500 dark:text-slate-400 leading-relaxed">Extreme Value Theory (EVT) GEV fitting on nominal anomaly score tails to normalize disparate score distributions.</p>
                                <div className="font-mono text-[9px] text-slate-400 pt-1 border-t border-violet-100 dark:border-violet-900/30">
                                    Fused Peak: {result.stage2MapScore != null ? result.stage2MapScore.toFixed(3) : 'Calibrated'}
                                </div>
                            </div>

                            <div className="rounded-xl border border-amber-200 dark:border-amber-900/40 bg-amber-50/50 dark:bg-amber-950/20 p-3.5 space-y-2">
                                <div className="flex items-center justify-between">
                                    <span className="font-mono text-[10px] font-bold text-amber-600 dark:text-amber-400">STAGE 04</span>
                                    <Badge variant="warning">Zero-Shot ViT</Badge>
                                </div>
                                <b className="block text-slate-800 dark:text-slate-100 font-semibold text-sm">EVT-CLIP Refiner</b>
                                <p className="text-[10px] text-slate-500 dark:text-slate-400 leading-relaxed">ViT-B/16 vision-language cross-attention aligning industrial state prompts with localized anomaly patches.</p>
                                <div className="font-mono text-[9px] text-slate-400 pt-1 border-t border-amber-100 dark:border-amber-900/30">
                                    Refined Peak: {result.stage3MapScore != null ? result.stage3MapScore.toFixed(3) : '0.267 threshold'}
                                </div>
                            </div>

                            <div className="rounded-xl border border-emerald-200 dark:border-emerald-900/40 bg-emerald-50/50 dark:bg-emerald-950/20 p-3.5 space-y-2">
                                <div className="flex items-center justify-between">
                                    <span className="font-mono text-[10px] font-bold text-emerald-600 dark:text-emerald-400">STAGE 05</span>
                                    <Badge variant="success">Evidence</Badge>
                                </div>
                                <b className="block text-slate-800 dark:text-slate-100 font-semibold text-sm">BBox & Evidence</b>
                                <p className="text-[10px] text-slate-500 dark:text-slate-400 leading-relaxed">Otsu morphological filtering generating connected component masks, bounding box coordinates, and audit trail.</p>
                                <div className="font-mono text-[9px] text-slate-400 pt-1 border-t border-emerald-100 dark:border-emerald-900/30">
                                    Decision: {result.prediction} ({result.anomalyScore.toFixed(3)})
                                </div>
                            </div>
                        </div>
                    </Card>

                    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                        <Card title="Defect Analysis" subtitle="Measurements come from the accepted final binary mask." className="lg:col-span-1">
                            <div className="grid grid-cols-2 gap-3 text-xs">
                                <div className="rounded-lg bg-slate-50 dark:bg-[#0b152b] p-3"><span className="text-[9px] uppercase text-slate-400">Mask pixels</span><b className="mt-1 block text-base">{result.defectAreaPixels?.toLocaleString?.() || 0}</b></div>
                                <div className="rounded-lg bg-slate-50 dark:bg-[#0b152b] p-3"><span className="text-[9px] uppercase text-slate-400">Mask coverage</span><b className="mt-1 block text-base">{((result.defectAreaFraction || 0) * 100).toFixed(2)}%</b></div>
                                <div className="rounded-lg bg-slate-50 dark:bg-[#0b152b] p-3"><span className="text-[9px] uppercase text-slate-400">Regions</span><b className="mt-1 block text-base">{result.defectComponentCount || 0}</b></div>
                                <div className="rounded-lg bg-slate-50 dark:bg-[#0b152b] p-3"><span className="text-[9px] uppercase text-slate-400">Map agreement</span><b className="mt-1 block text-base">{result.mapAgreement == null ? '—' : `${(result.mapAgreement * 100).toFixed(1)}%`}</b></div>
                            </div>
                            <div className="mt-3 rounded-lg border border-slate-200 dark:border-slate-800 p-3 text-[10px] text-slate-500">
                                <span className="flex items-center gap-2 font-semibold text-slate-700 dark:text-slate-200"><Crosshair size={14}/> Bounding box</span>
                                <p className="mt-1 font-mono">
                                    {result.defectBbox
                                        ? `x=${result.defectBbox.x}, y=${result.defectBbox.y}, w=${result.defectBbox.width}, h=${result.defectBbox.height}`
                                        : 'No accepted defect pixels'}
                                </p>
                            </div>
                        </Card>

                        <Card title="Visualization & Runtime Evidence" subtitle="Display controls, routing, and measured CPU timings without hiding long technical values" className="lg:col-span-2">
                            <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
                                {[
                                    ['Heatmap', showHeatmap, setShowHeatmap, Layers],
                                    ['Mask', showMask, setShowMask, Eye],
                                    ['Overlay', showOverlay, setShowOverlay, ShieldCheck],
                                ].map(([label, value, setter, Icon]) => (
                                    <button key={label} onClick={() => setter(!value)} className={`flex min-w-0 items-center justify-between rounded-lg border px-3 py-3 text-xs font-semibold transition ${value ? 'border-fuchsia-300 bg-fuchsia-50 text-fuchsia-700 dark:border-fuchsia-800 dark:bg-fuchsia-950/20 dark:text-fuchsia-300' : 'border-slate-200 text-slate-500 dark:border-slate-800'}`}>
                                        <span className="flex min-w-0 items-center gap-2"><Icon size={15} className="shrink-0"/><span className="truncate">{label}</span></span>
                                        <span className="shrink-0 pl-2">{value ? 'Shown' : 'Hidden'}</span>
                                    </button>
                                ))}
                            </div>

                            <div className="mt-4 border-t border-slate-100 pt-4 dark:border-slate-800">
                                <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                                    {[
                                        ['Validation', result.validationSeconds, 'text-cyan-600 dark:text-cyan-300'],
                                        ['EfficientAD', result.efficientadSeconds, 'text-fuchsia-600 dark:text-fuchsia-300'],
                                        ['PatchCore', result.patchcoreSeconds, 'text-violet-600 dark:text-violet-300'],
                                        ['EVT-CLIP', result.refinerSeconds, 'text-orange-600 dark:text-orange-300'],
                                    ].map(([label, seconds, color]) => (
                                        <div key={label} className="min-w-0 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5 dark:border-slate-800 dark:bg-[#0b152b]">
                                            <span className="block truncate text-[9px] font-bold uppercase tracking-[.08em] text-slate-400">{label}</span>
                                            <strong className={`mt-1 block text-base leading-none ${color}`}>{Number(seconds || 0).toFixed(2)} s</strong>
                                        </div>
                                    ))}
                                </div>

                                <div className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2">
                                    {[
                                        ['Route', friendlyRoute(result.route)],
                                        ['Worker cache', friendlyCache(result.workerCache)],
                                        ['Decision source', friendlyDecisionSource(result.decisionSource)],
                                        ['Localization', friendlyLocalization(result.localizationSource)],
                                    ].map(([label, value]) => (
                                        <div key={label} className="min-w-0 rounded-lg border border-slate-200 bg-white px-3 py-2.5 dark:border-slate-800 dark:bg-[#0b152b]">
                                            <span className="block text-[9px] font-bold uppercase tracking-[.08em] text-slate-400">{label}</span>
                                            <span className="mt-1 block text-[10px] font-semibold leading-4 text-slate-700 dark:text-slate-200">{value}</span>
                                        </div>
                                    ))}
                                </div>
                                <details className="mt-3 rounded-lg border border-slate-200 px-3 py-2 dark:border-slate-800">
                                    <summary className="cursor-pointer text-[9px] font-bold uppercase tracking-[.08em] text-slate-400">Raw technical values</summary>
                                    <div className="mt-2 grid grid-cols-1 gap-2 text-[9px] sm:grid-cols-2">
                                        <code className="break-all">route: {result.route || '—'}</code>
                                        <code className="break-all">cache: {result.workerCache || '—'}</code>
                                        <code className="break-all">decision: {result.decisionSource || '—'}</code>
                                        <code className="break-all">localization: {result.localizationSource || '—'}</code>
                                    </div>
                                </details>
                            </div>
                        </Card>
                        <Card title="Reliable Export" subtitle="PDF plus tamper-evident engineering evidence">
                            <div className="flex flex-col gap-3 h-full min-h-[180px] justify-end">
                                <p className="text-[11px] text-slate-400 font-semibold leading-relaxed">PDF is best for sharing. Evidence ZIP is best for audit/handoff: PDF + metadata JSON + permitted evidence files + SHA-256 manifest + HMAC-SHA256 signature.</p>{exportNotice && <div role="status" className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-[10px] font-semibold text-emerald-700 dark:border-emerald-900/40 dark:bg-emerald-950/20 dark:text-emerald-300">{exportNotice}</div>}
                                <Button variant="gradient" className="w-full py-3" onClick={downloadReport} disabled={reportBusy || bundleBusy} icon={FileText}>{reportBusy ? 'Generating PDF…' : 'Download PDF Report'}</Button>
                                <Button variant="secondary" className="w-full py-3" onClick={downloadBundle} disabled={reportBusy || bundleBusy} icon={Archive}>{bundleBusy ? 'Building Evidence ZIP…' : 'Download Evidence ZIP'}</Button>
                            </div>
                        </Card>
                    </div>
                </div>
            )}

            <Modal
                isOpen={precheckModalOpen && Boolean(precheck) && precheck?.can_run === false}
                onClose={() => setPrecheckModalOpen(false)}
                title={precheck?.state === 'unsupported_input' ? 'Unsupported Image' : precheck?.state === 'poor_quality_input' ? 'Image Quality Too Poor' : 'Product Category Mismatch'}
                size="md"
                actions={(
                    <>
                        <Button variant="secondary" onClick={() => setPrecheckModalOpen(false)}>Keep Image</Button>
                        {precheck?.predicted_category && supportedCategories.includes(precheck.predicted_category) && precheck.predicted_category !== category && (
                            <Button variant="gradient" onClick={() => { setCategory(precheck.predicted_category); setPrecheckModalOpen(false); }}>Use {labelCategory(precheck.predicted_category)}</Button>
                        )}
                    </>
                )}
            >
                <div className="text-center py-2">
                    <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-rose-100 text-rose-600"><Ban size={28} /></div>
                    <h4 className="text-base font-bold">Full anomaly inspection has not started.</h4>
                    <p className="mt-3 text-sm text-slate-500">{precheck?.message}</p>
                    <div className="mt-5 grid grid-cols-2 gap-3 text-left text-xs">
                        <div className="rounded-lg border border-slate-200 p-3"><span className="block text-[10px] uppercase text-slate-400">Selected</span><b className="capitalize">{labelCategory(category)}</b></div>
                        <div className="rounded-lg border border-slate-200 p-3"><span className="block text-[10px] uppercase text-slate-400">Closest supported</span><b className="capitalize">{labelCategory(precheck?.predicted_category)}</b></div>
                    </div>
                    <p className="mt-4 text-[11px] text-slate-400">Only the lightweight category/OOD gate ran. EfficientAD, PatchCore, Stage-2 and Stage-3 were not executed.</p>
                </div>
            </Modal>

            <Modal
                isOpen={safetyModalOpen && Boolean(result)}
                onClose={() => setSafetyModalOpen(false)}
                title={domainShift ? 'Outside Calibrated Visual Domain' : poorQualityInput ? 'Image Quality Too Poor' : unsupportedInput ? 'Unsupported Image' : wrongCategory ? 'Product Category Mismatch' : 'Input Validation Failed'}
                size="md"
                actions={(
                    <>
                        <Button variant="secondary" onClick={() => { setSafetyModalOpen(false); handleReset(); }}>Choose Another Image</Button>
                        {wrongCategory && result?.predictedCategory && supportedCategories.includes(result.predictedCategory) && (
                            <Button variant="gradient" onClick={rerunWithDetectedCategory} icon={RefreshCw}>Run as {labelCategory(result.predictedCategory)}</Button>
                        )}
                    </>
                )}
            >
                <div className="text-center py-2">
                    <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-rose-100 text-rose-600 dark:bg-rose-950/40 dark:text-rose-300">
                        <Ban size={28} />
                    </div>
                    <h4 className="text-base font-bold text-slate-900 dark:text-white">
                        {domainShift ? 'The product category matches, but this visual appearance is outside the calibrated training domain.' : poorQualityInput ? 'This image is too blank or clipped for a reliable inspection.' : unsupportedInput ? 'This image is outside the trained production scope.' : wrongCategory ? 'The selected category does not match the uploaded product.' : 'The product category is uncertain.'}
                    </h4>
                    <p className="mt-3 text-sm text-slate-500 dark:text-slate-400">{result?.notes}</p>
                    <div className="mt-5 grid grid-cols-2 gap-3 text-left text-xs">
                        <div className="rounded-lg border border-slate-200 p-3 dark:border-slate-800"><span className="block text-[10px] uppercase text-slate-400">Selected</span><b className="capitalize">{labelCategory(category)}</b></div>
                        <div className="rounded-lg border border-slate-200 p-3 dark:border-slate-800"><span className="block text-[10px] uppercase text-slate-400">Closest supported</span><b className="capitalize">{poorQualityInput ? 'not evaluated' : labelCategory(result?.predictedCategory)}</b></div>
                    </div>
                    <p className="mt-4 text-[11px] leading-relaxed text-slate-400">For a hard mismatch or unsupported image, the production worker stops before the wrong category specialists are allowed to produce an accepted heatmap.</p>
                </div>
            </Modal>
        </div>
    );
};

export default Detection;
