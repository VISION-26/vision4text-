import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Image as ImageIcon, CheckCircle2, AlertTriangle } from 'lucide-react';

export const CATEGORY_GUIDANCE = {
    bottle: { title: 'Bottle', framing: 'Use one bottle, centered and upright, with the complete body visible and a plain background.', defect: 'Crack, dent, contamination, broken edge, or unusual surface region.' },
    cable: { title: 'Cable', framing: 'Place one cable segment clearly inside the frame. Keep bends visible and avoid hands covering the cable.', defect: 'Cut, exposed region, damaged insulation, irregular bend, or foreign material.' },
    capsule: { title: 'Capsule', framing: 'Capture one capsule at a time, large enough to fill the central area without cropping either end.', defect: 'Crack, deformation, dent, contamination, split shell, or surface mark.' },
    carpet: { title: 'Carpet', framing: 'Capture a flat carpet region from above with even lighting and enough texture visible across the frame.', defect: 'Hole, cut, contamination, damaged fiber, or local texture change.' },
    grid: { title: 'Grid', framing: 'Keep the grid plane parallel to the camera so the repeating pattern is visible across most of the frame.', defect: 'Broken line, bent cell, missing structure, contamination, or distorted pattern.' },
    hazelnut: { title: 'Hazelnut', framing: 'Use one hazelnut, centered and fully visible, with a simple background and minimal shadow.', defect: 'Crack, hole, shell damage, contamination, or abnormal shape.' },
    leather: { title: 'Leather', framing: 'Photograph a flat leather surface with the texture visible and without folds hiding the inspected region.', defect: 'Cut, scratch, hole, discoloration, contamination, or abnormal texture.' },
    metal_nut: { title: 'Metal Nut', framing: 'Center one metal nut, show the complete outer edge and inner hole, and minimize strong reflections.', defect: 'Scratch, dent, chip, deformation, damaged edge, or contamination.' },
    pill: { title: 'Pill', framing: 'Capture one pill/tablet at a time with its whole outline visible and enough scale to show surface details.', defect: 'Crack, chip, dent, contamination, broken edge, or abnormal shape.' },
    screw: { title: 'Screw', framing: 'Show one screw from head to tip. Keep threads visible and avoid cropping the shaft.', defect: 'Damaged thread, bent shaft, deformed head, scratch, or missing material.' },
    tile: { title: 'Tile', framing: 'Capture a flat tile face with the full inspected surface visible and the camera close to perpendicular.', defect: 'Crack, chip, glaze defect, contamination, or abnormal texture.' },
    toothbrush: { title: 'Toothbrush', framing: 'Show the toothbrush head, bristles, neck, and enough handle to identify the complete product.', defect: 'Missing/bent bristle, deformed head, damaged handle, or contamination.' },
    transistor: { title: 'Transistor', framing: 'Capture one component clearly with its body and leads visible. Avoid overlapping parts or wires.', defect: 'Bent/missing lead, damaged package edge, crack, displacement, or foreign material.' },
    wood: { title: 'Wood', framing: 'Photograph a flat wood region with grain visible and avoid heavy perspective distortion.', defect: 'Scratch, hole, crack, discoloration, contamination, or disrupted grain.' },
    zipper: { title: 'Zipper', framing: 'Keep both tooth rows and the center seam visible. Use a straight, well-lit section of zipper.', defect: 'Missing/bent tooth, broken link, irregular spacing, contamination, or damaged fabric edge.' },
};

const SAMPLE_BASE = '/example-assets';

const RealSampleCard = ({ category, kind, title, onSelectFile }) => {
    const [busy, setBusy] = useState(false);
    const [failed, setFailed] = useState(false);
    const src = `${SAMPLE_BASE}/${encodeURIComponent(category)}/${kind}`;

    const choose = async () => {
        if (busy) return;
        setBusy(true);
        try {
            const response = await fetch(src, { cache: 'no-store' });
            if (!response.ok) throw new Error('sample unavailable');
            const contentTypeHeader = response.headers.get('Content-Type') || '';
            if (!contentTypeHeader.startsWith('image/')) throw new Error('sample unavailable');
            const blob = await response.blob();
            const contentType = blob.type || 'image/png';
            const extension = contentType.includes('jpeg') ? 'jpg' : contentType.includes('webp') ? 'webp' : 'png';
            const file = new File([blob], `${category}_${kind}.${extension}`, { type: contentType });
            onSelectFile?.(file);
        } catch {
            setFailed(true);
        } finally {
            setBusy(false);
        }
    };

    return (
        <button
            type="button"
            onClick={choose}
            className="group overflow-hidden rounded-xl border border-slate-200 bg-white text-left transition hover:border-fuchsia-300 hover:shadow-md dark:border-slate-800 dark:bg-[#07101f] dark:hover:border-fuchsia-800"
            title={`Use this real ${kind} ${category} sample as the inspection input`}
        >
            <div className="relative aspect-[4/3] overflow-hidden bg-slate-100 dark:bg-[#020617]">
                {!failed ? (
                    <img
                        src={src}
                        alt={`${CATEGORY_GUIDANCE[category]?.title || category} ${title}`}
                        className="h-full w-full object-contain transition duration-200 group-hover:scale-[1.02]"
                        onError={() => setFailed(true)}
                    />
                ) : (
                    <div className="flex h-full items-center justify-center px-4 text-center text-[10px] text-slate-500">
                        Real sample is not installed on this deployment yet.
                    </div>
                )}
                <span className={`absolute left-2 top-2 rounded-full border px-2 py-1 text-[9px] font-black uppercase tracking-[.12em] backdrop-blur ${kind === 'bad' ? 'border-rose-300/40 bg-rose-500/20 text-rose-100' : 'border-emerald-300/40 bg-emerald-500/20 text-emerald-100'}`}>
                    {title}
                </span>
                <span className="absolute bottom-2 right-2 rounded-md bg-black/65 px-2 py-1 text-[8px] font-bold text-white backdrop-blur">
                    {busy ? 'Loading…' : 'Click to use'}
                </span>
            </div>
        </button>
    );
};

const CategoryExampleGuide = ({ category, onSelectFile }) => {
    const [open, setOpen] = useState(false);
    const guide = CATEGORY_GUIDANCE[category] || CATEGORY_GUIDANCE.bottle;

    return (
        <div className="rounded-xl border border-slate-200 bg-slate-50/80 dark:border-slate-800 dark:bg-[#0c1530]">
            <button
                type="button"
                onClick={() => setOpen((value) => !value)}
                className="flex w-full items-center justify-between gap-3 p-3 text-left"
                aria-expanded={open}
            >
                <div className="flex min-w-0 items-center gap-2">
                    <ImageIcon size={14} className="shrink-0 text-cyan-500" />
                    <div>
                        <div className="text-[10px] font-black uppercase tracking-[.12em] text-slate-600 dark:text-slate-300">
                            Real dataset samples · {guide.title}
                        </div>
                        <div className="mt-0.5 text-[9px] text-slate-500">One GOOD and one BAD image from the stored MVTec AD sample set.</div>
                    </div>
                </div>
                {open ? <ChevronUp size={15} className="shrink-0 text-slate-500" /> : <ChevronDown size={15} className="shrink-0 text-slate-500" />}
            </button>

            {open && (
                <div className="border-t border-slate-200 p-3 dark:border-slate-800">
                    <div className="grid grid-cols-2 gap-2">
                        <div>
                            <RealSampleCard category={category} kind="good" title="GOOD" onSelectFile={onSelectFile} />
                            <div className="mt-1.5 flex gap-1.5 text-[9px] leading-4 text-slate-500">
                                <CheckCircle2 size={12} className="mt-0.5 shrink-0 text-emerald-500" />
                                <span>Known-good dataset sample. Click it to load it into the inspection input.</span>
                            </div>
                        </div>
                        <div>
                            <RealSampleCard category={category} kind="bad" title="BAD" onSelectFile={onSelectFile} />
                            <div className="mt-1.5 flex gap-1.5 text-[9px] leading-4 text-slate-500">
                                <AlertTriangle size={12} className="mt-0.5 shrink-0 text-rose-500" />
                                <span>{guide.defect}</span>
                            </div>
                        </div>
                    </div>
                    <div className="mt-3 rounded-lg border border-slate-200 bg-white px-3 py-2 text-[9px] leading-4 text-slate-500 dark:border-slate-800 dark:bg-[#010120] dark:text-slate-400">
                        <b className="text-slate-700 dark:text-slate-200">Recommended framing:</b> {guide.framing}
                    </div>
                </div>
            )}
        </div>
    );
};

export default CategoryExampleGuide;
