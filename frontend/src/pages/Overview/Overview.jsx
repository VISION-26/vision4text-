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
        <div className="min-h-screen overflow-hidden bg-white font-sans text-slate-900">
            <div className="evt-grid-light pointer-events-none fixed inset-0 opacity-40" />
            <div className="evt-overview-aurora evt-overview-aurora-one opacity-10" />
            <div className="evt-overview-aurora evt-overview-aurora-two opacity-10" />

            <div className="relative z-10">
                <header className="mx-auto flex h-20 max-w-7xl items-center justify-between border-b border-slate-200 bg-white/95 px-5 sm:px-7 backdrop-blur-sm">
                    <Link to="/" className="flex min-w-0 items-center gap-3.5" aria-label="EVT-CLIP overview">
                        <span className="flex h-8 items-end gap-1" aria-hidden="true">
                            <i className="block h-5 w-1.5 rounded-sm bg-[#fc4c02]" />
                            <i className="block h-8 w-1.5 rounded-sm bg-[#ef2cc1]" />
                            <i className="block h-6 w-1.5 rounded-sm bg-[#6366f1]" />
                        </span>
                        <span className="truncate text-xl font-black tracking-tight text-slate-900">EVT-CLIP</span>
                    </Link>
                    <div className="flex items-center gap-3">
                        <a href="#how" className="hidden px-3.5 py-2 text-base font-semibold text-slate-600 transition hover:text-slate-900 sm:inline-flex">How it works</a>
                        <a href="#proof" className="hidden px-3.5 py-2 text-base font-semibold text-slate-600 transition hover:text-slate-900 md:inline-flex">Evidence</a>
                        <a href="#flow" className="hidden px-3.5 py-2 text-base font-semibold text-slate-600 transition hover:text-slate-900 lg:inline-flex">Inspection flow</a>
                        <Link to="/login" className="rounded-xl bg-slate-900 px-5 py-2.5 text-base font-bold text-white transition hover:-translate-y-0.5 hover:bg-black hover:shadow-md">Sign In</Link>
                    </div>
                </header>

                <main>
                    <section className="mx-auto grid max-w-7xl items-center gap-8 px-5 pb-12 pt-10 sm:px-7 lg:grid-cols-[.94fr_1.06fr] lg:pt-14">
                        <motion.div {...(reduceMotion ? {} : { initial: { opacity: 0, x: -24 }, animate: { opacity: 1, x: 0 }, transition: { duration: .55 } })}>
                            <div className="inline-flex items-center gap-2 rounded-full border border-purple-200 bg-purple-50 px-4 py-2 text-xs sm:text-sm font-bold uppercase tracking-[.14em] text-purple-900">
                                <ScanLine size={16} /> Vision-language anomaly inspection
                            </div>
                            <h1 className="mt-6 max-w-3xl text-5xl font-black leading-[1.06] tracking-[-.04em] text-slate-900 sm:text-6xl lg:text-[4.25rem]">
                                Detect the anomaly. <span className="evt-gradient-text">Show where it is.</span> Keep the evidence.
                            </h1>
                            <p className="mt-6 max-w-2xl text-lg sm:text-xl leading-relaxed text-slate-700">
                                EVT-CLIP combines category-specific anomaly specialists with calibrated map fusion and vision-language refinement. Each inspection produces a decision, localization evidence, defect measurements, runtime information, history, and exportable records.
                            </p>
                            <div className="mt-8 flex flex-wrap gap-4">
                                <Link to="/login" className="evt-gradient evt-hero-cta inline-flex items-center gap-2.5 rounded-xl px-6 py-3.5 text-base sm:text-lg font-bold text-white shadow-md hover:shadow-lg">
                                    Open Workspace <ArrowRight size={19} />
                                </Link>
                                <a href="#how" className="inline-flex items-center gap-2 rounded-xl border border-slate-300 bg-white px-6 py-3.5 text-base sm:text-lg font-bold text-slate-900 shadow-sm transition hover:border-slate-400 hover:bg-slate-50">
                                    See the workflow
                                </a>
                            </div>

                            <div className="mt-8 grid max-w-2xl grid-cols-2 gap-3 sm:grid-cols-4">
                                {[
                                    [String(activeCategories.length), 'available product models', '#06b6d4'],
                                    ['Multi', 'stage inspection', '#ef2cc1'],
                                    ['CPU', 'cloud inference', '#fc4c02'],
                                    ['PDF', 'evidence report', '#6366f1'],
                                ].map(([value, label, accent]) => (
                                    <div key={label} className="group rounded-2xl border border-slate-200 bg-white p-4 sm:p-5 transition hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-md" style={{ boxShadow: `inset 0 3px 0 ${accent}` }}>
                                        <b className="block text-2xl sm:text-3xl font-black text-slate-900">{value}</b>
                                        <span className="mt-1 block text-xs sm:text-sm font-bold uppercase tracking-wider text-slate-600">{label}</span>
                                    </div>
                                ))}
                            </div>
                        </motion.div>

                        <motion.div {...(reduceMotion ? {} : { initial: { opacity: 0, x: 24 }, animate: { opacity: 1, x: 0 }, transition: { duration: .6, delay: .06 } })} className="relative">
                            <div className="absolute -inset-5 rounded-[2.5rem] bg-gradient-to-br from-cyan-500/10 via-fuchsia-500/10 to-orange-500/10 blur-2xl" />
                            <div className="relative overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-xl">
                                <div className="flex items-center justify-between border-b border-slate-200 bg-slate-50/70 px-6 py-4 text-xs sm:text-sm font-bold text-slate-700">
                                    <div className="flex items-center gap-2 text-slate-800"><Activity size={16} className="text-fuchsia-600" /> INSPECTION PIPELINE</div>
                                    <span className={`flex items-center gap-2 ${healthReady ? 'text-cyan-800' : health.status === 'checking' ? 'text-slate-500' : 'text-amber-700'}`}>
                                        <i className={`h-2 w-2 rounded-full ${healthReady ? 'bg-cyan-600' : health.status === 'checking' ? 'bg-slate-400 animate-pulse' : 'bg-amber-500'}`} />
                                        {healthReady ? 'System ready' : health.status === 'checking' ? 'Checking system' : 'System unavailable'}
                                    </span>
                                </div>

                                <div className="p-6">
                                    <div className="grid gap-4 sm:grid-cols-[.75fr_1.25fr]">
                                        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                                            <div className="flex items-center gap-3.5">
                                                <span className="flex h-12 w-12 items-center justify-center rounded-2xl border border-cyan-400/30 bg-cyan-50 text-cyan-700">
                                                    <ImageIcon size={24} />
                                                </span>
                                                <div>
                                                    <b className="block text-base sm:text-lg font-bold text-slate-900">One inspection image</b>
                                                    <span className="mt-1 block text-sm leading-relaxed text-slate-600">Upload one image and select one inspection category.</span>
                                                </div>
                                            </div>
                                            <div className="mt-5 rounded-xl border border-slate-200 bg-slate-50/80 p-4">
                                                <div className="mb-3 flex items-center justify-between text-xs sm:text-sm font-bold uppercase tracking-wider text-slate-600">
                                                    <span>What is produced</span>
                                                    <span className="text-indigo-700 font-extrabold">Stored evidence</span>
                                                </div>
                                                <div className="space-y-2.5 text-sm">
                                                    <div className="flex items-center gap-2.5 text-slate-800"><Crosshair size={15} className="text-fuchsia-600 shrink-0" /><span>Heatmap, binary mask, and overlay</span></div>
                                                    <div className="flex items-center gap-2.5 text-slate-800"><Gauge size={15} className="text-orange-600 shrink-0" /><span>Scores, mask coverage, bounding box, CPU time</span></div>
                                                    <div className="flex items-center gap-2.5 text-slate-800"><Database size={15} className="text-indigo-600 shrink-0" /><span>History, PDF report, and signed evidence ZIP</span></div>
                                                </div>
                                            </div>
                                        </div>

                                        <div className="evt-overview-pipeline rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                                            <div className="relative">
                                                <div className="evt-overview-pipeline-rail" aria-hidden="true">
                                                    {!reduceMotion && <span className="evt-overview-pipeline-tracer" />}
                                                </div>
                                                <div className="grid grid-cols-3 gap-x-2.5 gap-y-3.5">
                                                    {stages.map((stage) => (
                                                        <div key={stage.name} className="evt-overview-pipeline-node relative rounded-xl border border-slate-200 bg-white p-3.5 shadow-sm" style={{ '--stage-accent': stage.accent }}>
                                                            <div className="flex items-center justify-between gap-2">
                                                                <span className="text-xs sm:text-sm font-black" style={{ color: stage.accent }}>{stage.number}</span>
                                                                <i className="h-2 w-2 rounded-full" style={{ background: stage.accent, boxShadow: `0 0 10px ${stage.accent}88` }} />
                                                            </div>
                                                            <b className="mt-2 block text-sm sm:text-base font-bold text-slate-900">{stage.name}</b>
                                                            <span className="mt-1 block text-xs sm:text-sm leading-snug text-slate-600">{stage.detail}</span>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="mt-4 grid grid-cols-3 gap-3">
                                        {[
                                            [Layers3, 'Decision', 'Normal or anomalous'],
                                            [Crosshair, 'Localization', 'Where the mask is'],
                                            [FileDown, 'Record', 'Evidence preserved'],
                                        ].map(([Icon, title, detail], index) => (
                                            <div key={title} className="rounded-xl border border-slate-200 bg-white p-3.5 shadow-sm">
                                                <Icon size={16} className={index === 0 ? 'text-cyan-700' : index === 1 ? 'text-fuchsia-600' : 'text-indigo-600'} />
                                                <b className="mt-2 block text-sm sm:text-base font-bold text-slate-900">{title}</b>
                                                <span className="text-xs sm:text-sm font-semibold uppercase tracking-wider text-slate-600">{detail}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    </section>

                    <motion.section id="how" {...reveal} className="mx-auto max-w-7xl px-5 py-8 sm:px-7">
                        <div className="mb-6 flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
                            <div>
                                <p className="text-xs sm:text-sm font-extrabold uppercase tracking-[.18em] text-cyan-800">How EVT-CLIP works</p>
                                <h2 className="mt-2 text-3xl sm:text-4xl lg:text-5xl font-black tracking-tight text-slate-900">The problem, the method, and the evidence.</h2>
                            </div>
                            <span className="max-w-md text-base leading-relaxed text-slate-700">Each screen stays focused on the operational path: input, validation, model evidence, defect localization, history, and export.</span>
                        </div>
                        <div className="grid gap-4 md:grid-cols-3">
                            {story.map(([Icon, title, copy], index) => (
                                <article key={title} className="group relative overflow-hidden rounded-2xl border border-slate-200 bg-white p-6 sm:p-7 shadow-sm transition hover:-translate-y-1 hover:border-slate-300 hover:shadow-md">
                                    <div className="absolute inset-x-0 top-0 h-[3px] bg-gradient-to-r from-cyan-500 via-fuchsia-500 to-orange-500" />
                                    <div className="flex items-center justify-between">
                                        <span className="flex h-12 w-12 items-center justify-center rounded-2xl border border-slate-200 bg-slate-50"><Icon size={24} className={index === 0 ? 'text-cyan-700' : index === 1 ? 'text-fuchsia-600' : 'text-indigo-600'} /></span>
                                        <span className="text-3xl sm:text-4xl font-black text-slate-300">0{index + 1}</span>
                                    </div>
                                    <h3 className="mt-5 text-xl sm:text-2xl font-black text-slate-900">{title}</h3>
                                    <p className="mt-3 text-sm sm:text-base leading-relaxed text-slate-700">{copy}</p>
                                </article>
                            ))}
                        </div>
                    </motion.section>

                    <motion.section id="proof" {...reveal} className="mx-auto max-w-7xl px-5 py-8 sm:px-7">
                        <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white p-6 sm:p-8 shadow-sm">
                            <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
                                <div>
                                    <p className="text-xs sm:text-sm font-extrabold uppercase tracking-[.18em] text-indigo-700">Evidence from one inspection</p>
                                    <h2 className="mt-2 text-3xl sm:text-4xl lg:text-5xl font-black tracking-tight text-slate-900">The decision can be traced back through the model stages.</h2>
                                </div>
                                <span className="text-sm sm:text-base font-semibold text-slate-600">Stored backend outputs · no browser-drawn defect regions</span>
                            </div>
                            <div className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                                {proofItems.map(([Icon, title, copy], index) => (
                                    <div key={title} className="rounded-2xl border border-slate-200 bg-white p-5 sm:p-6 shadow-sm transition hover:border-slate-300 hover:shadow-md" style={{ boxShadow: `inset 0 3px 0 ${stages[index + 1]?.accent || '#6366f1'}` }}>
                                        <Icon size={22} style={{ color: stages[index + 1]?.accent || '#6366f1' }} />
                                        <b className="mt-4 block text-base sm:text-lg font-bold text-slate-900">{title}</b>
                                        <p className="mt-2 text-sm sm:text-base leading-relaxed text-slate-700">{copy}</p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </motion.section>

                    <motion.section {...reveal} className="mx-auto max-w-7xl px-5 py-8 sm:px-7">
                        <div className="grid gap-6 rounded-3xl border border-slate-200 bg-white p-6 sm:p-8 shadow-sm lg:grid-cols-[.72fr_1.28fr]">
                            <div>
                                <p className="text-xs sm:text-sm font-extrabold uppercase tracking-[.18em] text-orange-700">Active inspection scope</p>
                                <h2 className="mt-2 text-2xl sm:text-3xl font-black tracking-tight text-slate-900">Product profiles follow the active backend model registry.</h2>
                                <div className="mt-5 flex flex-wrap gap-2.5">
                                    {activeCategories.map((item, index) => (
                                        <span
                                            key={item}
                                            className="rounded-full border px-4 py-2 text-sm sm:text-base font-bold shadow-sm"
                                            style={{
                                                borderColor: `${stages[index % stages.length]?.accent}88`,
                                                background: `${stages[index % stages.length]?.accent}15`,
                                                color: '#0f172a',
                                            }}
                                        >
                                            {categoryLabel(item)}
                                        </span>
                                    ))}
                                </div>
                                <p className="mt-5 text-sm sm:text-base leading-relaxed text-slate-700">The New Inspection screen uses the same registry, so newly integrated product models appear in the selector without turning the interface into a large static category gallery.</p>
                            </div>
                            <div className="grid gap-4 sm:grid-cols-2">
                                {[
                                    [ScanLine, 'Localization', 'Heatmap, mask, overlay, mask pixels, coverage, connected regions, and mask-derived bounding box.'],
                                    [GitCompareArrows, 'Model evidence', 'Preprocessed input, EfficientAD, PatchCore, Stage-2 fusion, Stage-3 refinement, and final output.'],
                                    [TimerReset, 'Measured runtime', 'Validation, each specialist, refiner, cache state, and total CPU time.'],
                                    [ImageIcon, 'Image upload', 'Inspection starts from an uploaded image. External images never receive invented benchmark ground truth.'],
                                ].map(([Icon, title, copy], index) => (
                                    <div key={title} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm hover:shadow-md transition">
                                        <Icon size={22} style={{ color: stages[index + 1]?.accent }} />
                                        <b className="mt-3.5 block text-base sm:text-lg font-bold text-slate-900">{title}</b>
                                        <p className="mt-2 text-sm sm:text-base leading-relaxed text-slate-700">{copy}</p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </motion.section>

                    <motion.section id="flow" {...reveal} className="mx-auto max-w-7xl px-5 py-8 sm:px-7">
                        <div className="rounded-3xl border border-slate-200 bg-white p-6 sm:p-8 shadow-sm">
                            <div className="flex items-center justify-between gap-4">
                                <div>
                                    <p className="text-xs sm:text-sm font-extrabold uppercase tracking-[.18em] text-fuchsia-700">Inspection flow</p>
                                    <h2 className="mt-2 text-2xl sm:text-3xl font-black tracking-tight text-slate-900">Five steps from image to evidence record.</h2>
                                </div>
                                <Gauge size={30} className="hidden text-fuchsia-600 sm:block" />
                            </div>
                            <div className="relative mt-6 grid gap-3 lg:grid-cols-5">
                                <div className="absolute left-8 right-8 top-6 hidden h-px bg-gradient-to-r from-cyan-400/40 via-fuchsia-400/50 to-orange-400/40 lg:block" />
                                {flowSteps.map(([number, title, copy], index) => (
                                    <div key={number} className="relative rounded-2xl border border-slate-200 bg-white p-5 shadow-sm hover:shadow-md transition">
                                        <span className="relative z-10 inline-flex h-8 w-8 items-center justify-center rounded-full border border-slate-300 bg-white text-xs sm:text-sm font-black" style={{ color: stages[index]?.accent }}>{number}</span>
                                        <b className="mt-3.5 block text-base sm:text-lg font-bold text-slate-900">{title}</b>
                                        <p className="mt-2 text-sm leading-relaxed text-slate-700">{copy}</p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </motion.section>

                    <motion.section {...reveal} className="mx-auto max-w-7xl px-5 pb-14 pt-8 sm:px-7">
                        <div className="grid gap-4 text-sm sm:grid-cols-3">
                            {[
                                [ShieldCheck, 'Input safety', 'Active', 'Image quality and product-category checks protect the inspection path before an accepted result is shown.', '#0891b2'],
                                [SlidersHorizontal, 'Model evidence', 'Traceable', 'Specialist maps, fusion, refinement, final mask, geometry, and timings remain available behind the simple result.', '#6366f1'],
                                [History, 'Inspection records', 'Persistent', 'Completed scans can be reopened from History or Reports and exported as evidence.', '#f59e0b'],
                            ].map(([Icon, title, state, copy, accent]) => (
                                <div key={title} className="rounded-2xl border border-slate-200 bg-white p-5 sm:p-6 shadow-sm hover:shadow-md transition">
                                    <div className="flex items-center justify-between gap-2">
                                        <span className="flex items-center gap-2.5"><Icon size={18} style={{ color: accent }} /><b className="text-base sm:text-lg font-bold text-slate-900">{title}</b></span>
                                        <span className="text-xs sm:text-sm font-bold uppercase tracking-wider text-slate-500">{state}</span>
                                    </div>
                                    <p className="mt-3 text-sm sm:text-base leading-relaxed text-slate-700">{copy}</p>
                                </div>
                            ))}
                        </div>
                        <div className="mt-8 flex items-center justify-between gap-4 border-t border-slate-200 pt-6 text-sm sm:text-base font-medium text-slate-600">
                            <span>EVT-CLIP · Vision-language anomaly inspection</span>
                            <Link to="/login" className="inline-flex items-center gap-1.5 font-bold text-slate-900 hover:text-black">Sign in <ArrowRight size={15}/></Link>
                        </div>
                    </motion.section>
                </main>
            </div>
        </div>
    );
};

export default Overview;
