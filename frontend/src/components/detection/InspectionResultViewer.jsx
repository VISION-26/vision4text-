import React, { useState } from 'react';
import { Sparkles, Crosshair } from 'lucide-react';
import Card from '../common/Card';

const InspectionResultViewer = ({
    result,
    category,
    showHeatmap = true,
    showMask = true,
    showOverlay = true,
    className = '',
}) => {
    const [viewMode, setViewMode] = useState('isolated');

    if (!result) return null;

    const isRealCamera = result.yoloRoiState === 'isolated_real_camera' ||
        (result.notes && result.notes.includes('isolated')) ||
        (result.originalImage && result.preprocessedImage && result.originalImage !== result.preprocessedImage);

    return (
        <div className={`space-y-6 ${className}`}>
            {isRealCamera && (
                <div className="rounded-xl border border-cyan-500/30 bg-gradient-to-r from-cyan-950/40 via-slate-900/60 to-purple-950/40 p-4 text-xs backdrop-blur">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                        <div className="flex items-center gap-2.5">
                            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
                                <Sparkles size={16} />
                            </div>
                            <div>
                                <h4 className="font-semibold text-white flex items-center gap-2">
                                    Real-World Camera Pipeline Applied
                                    <span className="rounded-full bg-cyan-500/20 px-2 py-0.5 text-[10px] font-mono text-cyan-300 border border-cyan-500/30">
                                        Auto-Isolated
                                    </span>
                                </h4>
                                <p className="text-slate-400 text-[11px] mt-0.5">
                                    Background table disturbance, shadows, and room glare were neutralized before passing to EfficientAD & PatchCore.
                                </p>
                            </div>
                        </div>

                        <div className="flex items-center bg-slate-950/60 border border-slate-700/60 rounded-lg p-1">
                            <button
                                onClick={() => setViewMode('source')}
                                className={`px-2.5 py-1 rounded text-xs font-medium transition-all ${viewMode === 'source' ? 'bg-cyan-500 text-slate-950 font-semibold' : 'text-slate-400 hover:text-white'}`}
                            >
                                Raw Camera
                            </button>
                            <button
                                onClick={() => setViewMode('isolated')}
                                className={`px-2.5 py-1 rounded text-xs font-medium transition-all ${viewMode === 'isolated' ? 'bg-cyan-500 text-slate-950 font-semibold' : 'text-slate-400 hover:text-white'}`}
                            >
                                Isolated ROI
                            </button>
                            <button
                                onClick={() => setViewMode('split')}
                                className={`px-2.5 py-1 rounded text-xs font-medium transition-all ${viewMode === 'split' ? 'bg-cyan-500 text-slate-950 font-semibold' : 'text-slate-400 hover:text-white'}`}
                            >
                                Side-by-Side
                            </button>
                        </div>
                    </div>
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <Card
                    title={viewMode === 'source' ? 'Raw Camera Source' : isRealCamera ? 'Isolated Model ROI' : 'Original Image'}
                    subtitle={viewMode === 'source' ? 'Unprocessed photo from device' : isRealCamera ? 'Background-neutralized 256×256 input' : 'Uploaded/captured source'}
                    padding={false}
                >
                    <div className="aspect-[4/3] w-full bg-[#010120] flex items-center justify-center overflow-hidden border-t border-slate-100 dark:border-slate-800 relative group">
                        {viewMode === 'split' && isRealCamera ? (
                            <div className="grid grid-cols-2 w-full h-full">
                                <div className="relative border-r border-slate-800 flex items-center justify-center overflow-hidden bg-black/40">
                                    <img src={result.originalImage} alt="Raw source" className="max-w-full max-h-full object-contain" />
                                    <span className="absolute bottom-2 left-2 rounded bg-black/70 px-1.5 py-0.5 text-[9px] font-mono text-slate-300">Raw</span>
                                </div>
                                <div className="relative flex items-center justify-center overflow-hidden bg-black/40">
                                    <img src={result.preprocessedImage || result.originalImage} alt="Isolated ROI" className="max-w-full max-h-full object-contain" />
                                    <span className="absolute bottom-2 right-2 rounded bg-cyan-950/80 border border-cyan-500/40 px-1.5 py-0.5 text-[9px] font-mono text-cyan-300">Isolated</span>
                                </div>
                            </div>
                        ) : (
                            <img
                                src={viewMode === 'source' ? result.originalImage : (result.preprocessedImage || result.originalImage)}
                                alt="Input view"
                                className="max-w-full max-h-full object-contain transition-transform duration-200"
                            />
                        )}
                        {isRealCamera && viewMode !== 'split' && (
                            <button
                                onClick={() => setViewMode((prev) => prev === 'source' ? 'isolated' : 'source')}
                                className="absolute bottom-2 right-2 rounded-lg bg-black/80 border border-slate-700 px-2 py-1 text-[10px] text-cyan-300 hover:text-white backdrop-blur transition-colors opacity-80 hover:opacity-100"
                            >
                                {viewMode === 'source' ? 'Switch to Isolated ROI →' : '← Show Raw Camera'}
                            </button>
                        )}
                    </div>
                </Card>

                <Card title="Anomaly Heatmap" subtitle="Backend-generated localization evidence" padding={false}>
                    <div className="aspect-[4/3] w-full bg-[#010120] flex items-center justify-center overflow-hidden border-t border-slate-100 dark:border-slate-800">
                        {showHeatmap && result.heatmapImage ? (
                            <img src={result.heatmapImage} alt="Anomaly heatmap" className="max-w-full max-h-full object-contain" />
                        ) : (
                            <span className="text-xs text-slate-500">Heatmap hidden</span>
                        )}
                    </div>
                </Card>

                <Card title="Segmentation Mask" subtitle="Calibrated production mask (0.267)" padding={false}>
                    <div className="aspect-[4/3] w-full bg-[#010120] flex items-center justify-center overflow-hidden border-t border-slate-100 dark:border-slate-800">
                        {showMask && result.maskImage ? (
                            <img src={result.maskImage} alt="Segmentation mask" className="max-w-full max-h-full object-contain" />
                        ) : (
                            <span className="text-xs text-slate-500">Mask hidden</span>
                        )}
                    </div>
                </Card>

                <Card title="Overlay Image" subtitle="Backend-generated defect overlay" padding={false}>
                    <div className="aspect-[4/3] w-full bg-[#010120] flex items-center justify-center overflow-hidden border-t border-slate-100 dark:border-slate-800">
                        {showOverlay && result.overlayImage ? (
                            <img src={result.overlayImage} alt="Overlay" className="max-w-full max-h-full object-contain" />
                        ) : (
                            <span className="text-xs text-slate-500">Overlay hidden</span>
                        )}
                    </div>
                </Card>
            </div>

            {result.defectBbox && (
                <div className="rounded-xl border border-rose-500/30 bg-rose-950/20 p-4">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                        <div className="flex items-center gap-2">
                            <Crosshair size={18} className="text-rose-400" />
                            <h4 className="text-sm font-bold text-white">Detected Defect Geometry</h4>
                        </div>
                        <div className="flex items-center gap-3 text-xs font-mono text-slate-300">
                            <span>BBox: [{result.defectBbox.x}, {result.defectBbox.y}, {result.defectBbox.width}×{result.defectBbox.height}]</span>
                            {result.defectAreaPixels != null && (
                                <span>Area: {result.defectAreaPixels.toLocaleString()} px</span>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default InspectionResultViewer;
