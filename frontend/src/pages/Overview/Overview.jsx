import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { motion, useReducedMotion } from 'framer-motion';
import { displayCategory } from '../../constants/categoryLabels';
import {
    Activity, ArrowRight, BrainCircuit, ClipboardCheck, Crosshair,
    Database, FileDown, Gauge, GitCompareArrows, Layers3, ScanLine,
    ShieldCheck, TimerReset, Image as ImageIcon, History, SlidersHorizontal,
} from 'lucide-react';

const stages = [
    { number: '01', name: 'Input', detail: 'Upload an image', accent: '#0891b2' },
    { number: '02', name: 'Validate', detail: 'Quality + category', accent: '#8b5cf6' },
    { number: '03', name: 'Inspect', detail: 'EfficientAD + PatchCore', accent: '#ef2cc1' },
    { number: '04', name: 'Fuse', detail: 'Calibrated Stage-2', accent: '#fc4c02' },
    { number: '05', name: 'Refine', detail: 'EVT-CLIP Stage-3', accent: '#f59e0b' },
    { number: '06', name: 'Evidence', detail: 'Mask + report + history', accent: '#6366f1' },
];

const fallbackCategories = ['bottle', 'cable', 'capsule', 'metal_nut', 'pill'];
const categoryLabel = displayCategory;

const proofItems = [
    [Activity, 'Model input', 'The uploaded image and standardized preprocessing preview are stored with the scan.'],
    [GitCompareArrows, 'Stage evidence', 'EfficientAD, PatchCore, Stage-2 fusion, Stage-3 refinement, and the accepted final map can be inspected separately.'],
    [Crosshair, 'Defect geometry', 'Mask pixels, mask coverage, connected regions, and a bounding box are calculated from the final mask.'],
    [FileDown, 'Inspection record', 'The stored result can be exported as a PDF or signed evidence ZIP and reopened from history.'],
];

const story = [
    [ShieldCheck, 'Problem', 'A single anomaly score is not enough. The system should also show where the defect is and preserve evidence for later review.'],
    [BrainCircuit, 'Method', 'EfficientAD and PatchCore provide specialist evidence. Stage-2 combines their maps and EVT-CLIP refines the localization path.'],
    [ClipboardCheck, 'Result', 'Each scan stores the decision, model-stage maps, final mask, defect measurements, CPU timing, history, and exportable evidence.'],
];

const flowSteps = [
    ['01', 'Choose input', 'Upload an inspection image.'],
    ['02', 'Select category', 'Choose one of the product profiles currently available in the active model registry.'],
    ['03', 'Run inspection', 'The CPU worker executes the specialist and refinement pipeline.'],
    ['04', 'Inspect evidence', 'Compare the final result with each stored model-stage output.'],
    ['05', 'Save the record', 'Reopen the scan in history or export PDF and evidence ZIP.'],
];

const Overview = () => {
    const [health, setHealth] = useState({ status: 'checking', supported_categories: fallbackCategories });
    const reduceMotion = useReducedMotion();

    useEffect(() => {
        let active = true;
        fetch('/health', { cache: 'no-store' })
            .then((response) => response.ok ? response.json() : Promise.reject(new Error('health')))
            .then((data) => {
                if (active) setHealth({
                    ...data,
                    status: String(data?.status || 'unavailable').toLowerCase(),
                    supported_categories: Array.isArray(data?.supported_categories) && data.supported_categories.length
                        ? data.supported_categories
                        : fallbackCategories,
                });
            })
            .catch(() => {
                if (active) setHealth({ status: 'unavailable', supported_categories: fallbackCategories });
            });
        return () => { active = false; };
    }, []);

    const healthReady = health.status === 'ready';
    const activeCategories = health.supported_categories || fallbackCategories;
    const reveal = reduceMotion ? {} : {
        initial: { opacity: 0, y: 22 },
        whileInView: { opacity: 1, y: 0 },
        viewport: { once: true, amount: 0.18 },
        transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] },
    };

    return (
        <div className="min-h-screen overflow-hidden bg-white font-sans text-[#171717]">
            <div className="evt-grid-light pointer-events-none fixed inset-0" />
            <div className="evt-overview-aurora evt-overview-aurora-one" />
            <div className="evt-overview-aurora evt-overview-aurora-two" />

            <div className="relative z-10">
                <header className="mx-auto flex h-16 max-w-7xl items-center justify-between border-b border-slate-200 px-5 sm:px-7">
                    <Link to="/" className="flex min-w-0 items-center gap-3" aria-label="EVT-CLIP overview">
                        <span className="flex h-7 items-end gap-[3px]" aria-hidden="true">
                            <i className="block h-4 w-1.5 rounded-sm bg-[#fc4c02]" />
                            <i className="block h-7 w-1.5 rounded-sm bg-[#ef2cc1]" />
                            <i className="block h-5 w-1.5 rounded-sm bg-[#bdbbff]" />
                        </span>
                        <span className="truncate font-bold tracking-tight">EVT-CLIP</span>
                    </Link>
                    <div className="flex items-center gap-2">
                        <a href="#how" className="hidden px-3 py-2 text-sm text-slate-600 transition hover:text-[#171717] sm:inline-flex">How it works</a>
                        <a href="#proof" className="hidden px-3 py-2 text-sm text-slate-600 transition hover:text-[#171717] md:inline-flex">Evidence</a>
                        <a href="#flow" className="hidden px-3 py-2 text-sm text-slate-600 transition hover:text-[#171717] lg:inline-flex">Inspection flow</a>
                        <Link to="/login" className="rounded-lg bg-[#171717] px-4 py-2 text-sm font-bold text-white transition hover:-translate-y-0.5 hover:bg-black">Sign In</Link>
                    </div>
                </header>

                <main>
                    <section className="mx-auto grid max-w-7xl items-center gap-7 px-5 pb-10 pt-9 sm:px-7 lg:grid-cols-[.94fr_1.06fr] lg:pt-12">
                        <motion.div {...(reduceMotion ? {} : { initial: { opacity: 0, x: -24 }, animate: { opacity: 1, x: 0 }, transition: { duration: .55 } })}>
                            <div className="inline-flex items-center gap-2 rounded-full border border-[#ddd6fe] bg-white px-3 py-1.5 text-xs font-bold uppercase tracking-[.16em] text-[#5b21b6]">
                                <ScanLine size={14} /> Vision-language anomaly inspection
                            </div>
                            <h1 className="mt-5 max-w-3xl text-5xl font-black leading-[1.02] tracking-[-.05em] text-[#171717] sm:text-6xl lg:text-[4rem]">
                                Detect the anomaly. <span className="evt-gradient-text">Show where it is.</span> Keep the evidence.
                            </h1>
                            <p className="mt-5 max-w-2xl text-base leading-8 text-slate-700 sm:text-lg">
                                EVT-CLIP combines category-specific anomaly specialists with calibrated map fusion and vision-language refinement. Each inspection produces a decision, localization evidence, defect measurements, runtime information, history, and exportable records.
                            </p>
                            <div className="mt-6 flex flex-wrap gap-3">
                                <Link to="/login" className="evt-gradient evt-hero-cta inline-flex items-center gap-2 rounded-xl px-5 py-3 text-sm font-bold text-white">
                                    Open Workspace <ArrowRight size={17} />
                                </Link>
                                <a href="#how" className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-5 py-3 text-base font-semibold text-[#171717] shadow-sm transition hover:border-slate-300">
                                    See the workflow
                                </a>
                            </div>

                            <div className="mt-6 grid max-w-2xl grid-cols-2 gap-2 sm:grid-cols-4">
                                {[
                                    [String(activeCategories.length), 'available product models', '#06b6d4'],
                                    ['Multi', 'stage inspection', '#ef2cc1'],
                                    ['CPU', 'cloud inference', '#fc4c02'],
                                    ['PDF', 'evidence report', '#bdbbff'],
                                ].map(([value, label, accent]) => (
                                    <div key={label} className="group rounded-xl border border-slate-200 bg-white px-3 py-3 transition hover:-translate-y-0.5 hover:border-slate-300" style={{ boxShadow: `inset 0 2px 0 ${accent}55` }}>
                                        <b className="block text-xl text-[#171717]">{value}</b>
                                        <span className="text-[11px] uppercase tracking-[.1em] text-slate-500">{label}</span>
                                    </div>
                                ))}
                            </div>
                        </motion.div>

                        <motion.div {...(reduceMotion ? {} : { initial: { opacity: 0, x: 24 }, animate: { opacity: 1, x: 0 }, transition: { duration: .6, delay: .06 } })} className="relative">
                            <div className="absolute -inset-5 rounded-[2rem] bg-gradient-to-br from-cyan-500/10 via-fuchsia-500/10 to-orange-500/10 blur-2xl" />
                            <div className="relative overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-xl">
                                <div className="flex items-center justify-between border-b border-slate-200 px-5 py-3.5 text-[10px]">
                                    <div className="flex items-center gap-2 text-slate-700"><Activity size={14} className="text-fuchsia-600" /> INSPECTION PIPELINE</div>
                                    <span className={`flex items-center gap-1.5 ${healthReady ? 'text-cyan-700' : health.status === 'checking' ? 'text-slate-400' : 'text-amber-600'}`}>
                                        <i className={`h-1.5 w-1.5 rounded-full ${healthReady ? 'bg-cyan-600' : health.status === 'checking' ? 'bg-slate-500 animate-pulse' : 'bg-amber-500'}`} />
                                        {healthReady ? 'System ready' : health.status === 'checking' ? 'Checking system' : 'System unavailable'}
                                    </span>
                                </div>

                                <div className="p-5">
                                    <div className="grid gap-3 sm:grid-cols-[.72fr_1.28fr]">
                                        <div className="rounded-2xl border border-slate-200 bg-[#FAF9F6] p-4">
                                            <div className="flex items-center gap-3">
                                                <span className="flex h-11 w-11 items-center justify-center rounded-xl border border-cyan-400/20 bg-cyan-400/[.06] text-cyan-700">
                                                    <ImageIcon size={21} />
                                                </span>
                                                <div>
                                                    <b className="block text-base">One inspection image</b>
                                                    <span className="mt-1 block text-xs leading-5 text-slate-600">Upload one image and select one inspection category.</span>
                                                </div>
                                            </div>
                                            <div className="mt-4 rounded-xl border border-slate-200 bg-white p-3">
                                                <div className="mb-2 flex items-center justify-between text-[11px] uppercase tracking-[.14em] text-slate-500">
                                                    <span>What is produced</span>
                                                    <span className="text-indigo-600">Stored evidence</span>
                                                </div>
                                                <div className="space-y-2 text-xs">
                                                    <div className="flex items-center gap-2"><Crosshair size={13} className="text-fuchsia-600" /><span>Heatmap, binary mask, and overlay</span></div>
                                                    <div className="flex items-center gap-2"><Gauge size={13} className="text-orange-600" /><span>Scores, mask coverage, bounding box, CPU time</span></div>
                                                    <div className="flex items-center gap-2"><Database size={13} className="text-indigo-600" /><span>History, PDF report, and signed evidence ZIP</span></div>
                                                </div>
                                            </div>
                                        </div>

                                        <div className="evt-overview-pipeline rounded-2xl border border-slate-200 bg-[#FAF9F6] p-4">
                                            <div className="relative">
                                                <div className="evt-overview-pipeline-rail" aria-hidden="true">
                                                    {!reduceMotion && <span className="evt-overview-pipeline-tracer" />}
                                                </div>
                                                <div className="grid grid-cols-3 gap-x-2 gap-y-3">
                                                    {stages.map((stage, index) => (
                                                        <div key={stage.name} className="evt-overview-pipeline-node relative rounded-xl border border-slate-200 bg-white p-3 shadow-sm" style={{ '--stage-accent': stage.accent }}>
                                                            <div className="flex items-center justify-between gap-2">
                                                                <span className="text-[11px] font-black" style={{ color: stage.accent }}>{stage.number}</span>
                                                                <i className="h-1.5 w-1.5 rounded-full" style={{ background: stage.accent, boxShadow: `0 0 10px ${stage.accent}88` }} />
                                                            </div>
                                                            <b className="mt-2 block text-sm text-[#171717]">{stage.name}</b>
                                                            <span className="mt-1 block text-xs leading-4 text-slate-600">{stage.detail}</span>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="mt-3 grid grid-cols-3 gap-2">
                                        {[
                                            [Layers3, 'Decision', 'Normal or anomalous'],
                                            [Crosshair, 'Localization', 'Where the mask is'],
                                            [FileDown, 'Record', 'Evidence preserved'],
                                        ].map(([Icon, title, detail], index) => (
                                            <div key={title} className="rounded-xl border border-slate-200 bg-white px-3 py-2.5 shadow-sm">
                                                <Icon size={14} className={index === 0 ? 'text-cyan-700' : index === 1 ? 'text-fuchsia-600' : 'text-indigo-600'} />
                                                <b className="mt-1.5 block text-xs text-[#171717]">{title}</b>
                                                <span className="text-[11px] uppercase tracking-[.1em] text-slate-500">{detail}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    </section>

                    <motion.section id="how" {...reveal} className="mx-auto max-w-7xl px-5 py-6 sm:px-7">
                        <div className="mb-4 flex flex-col justify-between gap-2 sm:flex-row sm:items-end">
                            <div>
                                <p className="text-xs font-bold uppercase tracking-[.18em] text-cyan-700">How EVT-CLIP works</p>
                                <h2 className="mt-1 text-3xl font-black tracking-tight sm:text-4xl">The problem, the method, and the evidence.</h2>
                            </div>
                            <span className="max-w-md text-sm leading-5 text-slate-600">Each screen stays focused on the operational path: input, validation, model evidence, defect localization, history, and export.</span>
                        </div>
                        <div className="grid gap-3 md:grid-cols-3">
                            {story.map(([Icon, title, copy], index) => (
                                <article key={title} className="group relative overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm p-5 transition hover:-translate-y-1 hover:border-slate-300">
                                    <div className="absolute inset-x-0 top-0 h-[2px] bg-gradient-to-r from-cyan-400 via-fuchsia-400 to-orange-400 opacity-70" />
                                    <div className="flex items-center justify-between">
                                        <span className="flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200 bg-slate-50"><Icon size={20} className={index === 0 ? 'text-cyan-700' : index === 1 ? 'text-fuchsia-600' : 'text-indigo-600'} /></span>
                                        <span className="text-3xl font-black text-slate-200">0{index + 1}</span>
                                    </div>
                                    <h3 className="mt-4 text-xl font-bold">{title}</h3>
                                    <p className="mt-2 text-sm leading-6 text-slate-600">{copy}</p>
                                </article>
                            ))}
                        </div>
                    </motion.section>

                    <motion.section id="proof" {...reveal} className="mx-auto max-w-7xl px-5 py-6 sm:px-7">
                        <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm p-5 sm:p-7">
                            <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
                                <div>
                                    <p className="text-xs font-bold uppercase tracking-[.18em] text-indigo-600">Evidence from one inspection</p>
                                    <h2 className="mt-2 text-3xl font-black tracking-tight sm:text-4xl">The decision can be traced back through the model stages.</h2>
                                </div>
                                <span className="text-sm text-slate-600">Stored backend outputs · no browser-drawn defect regions</span>
                            </div>
                            <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                                {proofItems.map(([Icon, title, copy], index) => (
                                    <div key={title} className="rounded-xl border border-slate-200 bg-[#FAF9F6] p-4 transition hover:border-slate-300" style={{ boxShadow: `inset 0 2px 0 ${stages[index + 1]?.accent || '#bdbbff'}55` }}>
                                        <Icon size={19} style={{ color: stages[index + 1]?.accent || '#bdbbff' }} />
                                        <b className="mt-3 block text-base">{title}</b>
                                        <p className="mt-1 text-sm leading-6 text-slate-600">{copy}</p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </motion.section>

                    <motion.section {...reveal} className="mx-auto max-w-7xl px-5 py-6 sm:px-7">
                        <div className="grid gap-5 rounded-2xl border border-slate-200 bg-white shadow-sm p-5 sm:p-7 lg:grid-cols-[.72fr_1.28fr]">
                            <div>
                                <p className="text-xs font-bold uppercase tracking-[.18em] text-orange-600">Active inspection scope</p>
                                <h2 className="mt-2 text-2xl font-black tracking-tight">Product profiles follow the active backend model registry.</h2>
                                <div className="mt-4 flex flex-wrap gap-2">
                                    {activeCategories.map((item, index) => <span key={item} className="rounded-full border px-3 py-1.5 text-xs" style={{ borderColor: `${stages[index % stages.length]?.accent}55`, background: `${stages[index % stages.length]?.accent}12`, color: '#171717' }}>{categoryLabel(item)}</span>)}
                                </div>
                                <p className="mt-4 text-sm leading-6 text-slate-600">The New Inspection screen uses the same registry, so newly integrated product models appear in the selector without turning the interface into a large static category gallery.</p>
                            </div>
                            <div className="grid gap-3 sm:grid-cols-2">
                                {[
                                    [ScanLine, 'Localization', 'Heatmap, mask, overlay, mask pixels, coverage, connected regions, and mask-derived bounding box.'],
                                    [GitCompareArrows, 'Model evidence', 'Preprocessed input, EfficientAD, PatchCore, Stage-2 fusion, Stage-3 refinement, and final output.'],
                                    [TimerReset, 'Measured runtime', 'Validation, each specialist, refiner, cache state, and total CPU time.'],
                                    [ImageIcon, 'Image upload', 'Inspection starts from an uploaded image. External images never receive invented benchmark ground truth.'],
                                ].map(([Icon, title, copy], index) => (
                                    <div key={title} className="rounded-xl border border-slate-200 bg-[#FAF9F6] p-4">
                                        <Icon size={19} style={{ color: stages[index + 1]?.accent }} />
                                        <b className="mt-3 block text-base">{title}</b>
                                        <p className="mt-1 text-sm leading-6 text-slate-600">{copy}</p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </motion.section>

                    <motion.section id="flow" {...reveal} className="mx-auto max-w-7xl px-5 py-6 sm:px-7">
                        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-7">
                            <div className="flex items-center justify-between gap-4">
                                <div>
                                    <p className="text-xs font-bold uppercase tracking-[.18em] text-fuchsia-600">Inspection flow</p>
                                    <h2 className="mt-2 text-2xl font-black tracking-tight">Five steps from image to evidence record.</h2>
                                </div>
                                <Gauge size={26} className="hidden text-fuchsia-600 sm:block" />
                            </div>
                            <div className="relative mt-5 grid gap-2 lg:grid-cols-5">
                                <div className="absolute left-8 right-8 top-5 hidden h-px bg-gradient-to-r from-cyan-400/30 via-fuchsia-400/40 to-orange-400/30 lg:block" />
                                {flowSteps.map(([number, title, copy], index) => (
                                    <div key={number} className="relative rounded-xl border border-slate-200 bg-[#FAF9F6] p-4">
                                        <span className="relative z-10 inline-flex h-7 w-7 items-center justify-center rounded-full border border-slate-200 bg-white text-[11px] font-black" style={{ color: stages[index]?.accent }}>{number}</span>
                                        <b className="mt-3 block text-base">{title}</b>
                                        <p className="mt-1 text-sm leading-5 text-slate-600">{copy}</p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </motion.section>

                    <motion.section {...reveal} className="mx-auto max-w-7xl px-5 pb-12 pt-6 sm:px-7">
                        <div className="grid gap-3 text-sm sm:grid-cols-3">
                            {[
                                [ShieldCheck, 'Input safety', 'Active', 'Image quality and product-category checks protect the inspection path before an accepted result is shown.', '#06b6d4'],
                                [SlidersHorizontal, 'Model evidence', 'Traceable', 'Specialist maps, fusion, refinement, final mask, geometry, and timings remain available behind the simple result.', '#bdbbff'],
                                [History, 'Inspection records', 'Persistent', 'Completed scans can be reopened from History or Reports and exported as evidence.', '#f59e0b'],
                            ].map(([Icon, title, state, copy, accent]) => (
                                <div key={title} className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                                    <div className="flex items-center justify-between gap-2">
                                        <span className="flex items-center gap-2"><Icon size={15} style={{ color: accent }} /><b>{title}</b></span>
                                        <span className="text-[11px] uppercase tracking-[.14em] text-slate-500">{state}</span>
                                    </div>
                                    <p className="mt-2 text-sm leading-6 text-slate-600">{copy}</p>
                                </div>
                            ))}
                        </div>
                        <div className="mt-7 flex items-center justify-between gap-4 border-t border-slate-200 pt-5 text-sm text-slate-600">
                            <span>EVT-CLIP · Vision-language anomaly inspection</span>
                            <Link to="/login" className="inline-flex items-center gap-1.5 text-[#171717] hover:text-black">Sign in <ArrowRight size={13}/></Link>
                        </div>
                    </motion.section>
                </main>
            </div>
        </div>
    );
};

export default Overview;
