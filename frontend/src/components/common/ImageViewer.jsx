import React, { useState } from 'react';
import { Layers, Eye, RefreshCw, ZoomIn, ZoomOut } from 'lucide-react';

const ImageViewer = ({ originalSrc, heatmapSrc, maskSrc, overlaySrc, anomalyScore = 0.0, className = '' }) => {
    const [activeTab, setActiveTab] = useState('overlay');
    const [zoomLevel, setZoomLevel] = useState(1);

    const tabs = [
        { id: 'original', label: 'Original', icon: Eye, src: originalSrc },
        { id: 'heatmap', label: 'Heatmap', icon: Layers, src: heatmapSrc },
        { id: 'mask', label: 'Mask', icon: Layers, src: maskSrc },
        { id: 'overlay', label: 'Overlay', icon: Layers, src: overlaySrc },
    ];
    const current = tabs.find((tab) => tab.id === activeTab);

    const handleZoom = (direction) => setZoomLevel((prev) => direction === 'in' ? Math.min(prev + 0.25, 2.5) : Math.max(prev - 0.25, 0.75));

    return (
        <div className={`flex flex-col border border-slate-200 dark:border-slate-800 rounded-md overflow-hidden bg-together-night text-slate-200 ${className}`}>
            <div className="px-5 py-3 border-b border-white/10 bg-together-night flex flex-wrap items-center justify-between gap-3">
                <div className="flex bg-white/5 border border-white/10 p-1 rounded-md">
                    {tabs.map((tab) => (
                        <button key={tab.id} onClick={() => setActiveTab(tab.id)} className={`px-3 py-1.5 rounded text-xs font-semibold flex items-center gap-1.5 ${activeTab === tab.id ? 'bg-white text-together-night' : 'text-slate-400 hover:text-white'}`}>
                            <tab.icon size={13} />{tab.label}
                        </button>
                    ))}
                </div>
                <div className="flex items-center gap-4 text-xs font-semibold text-slate-400">
                    <div className="flex items-center gap-2">
                        <button onClick={() => handleZoom('out')} className="hover:text-white p-1"><ZoomOut size={16} /></button>
                        <span>{Math.round(zoomLevel * 100)}%</span>
                        <button onClick={() => handleZoom('in')} className="hover:text-white p-1"><ZoomIn size={16} /></button>
                        <button onClick={() => setZoomLevel(1)} className="hover:text-white p-1"><RefreshCw size={12} /></button>
                    </div>
                    <span className="font-mono font-bold text-white">Score {Number(anomalyScore).toFixed(3)}</span>
                </div>
            </div>
            <div className="relative aspect-video flex items-center justify-center overflow-hidden bg-black/40 min-h-[300px]">
                {current?.src ? (
                    <img src={current.src} alt={`${current.label} result`} className="max-h-[90%] max-w-[92%] object-contain select-none transition-transform duration-200" style={{ transform: `scale(${zoomLevel})` }} />
                ) : (
                    <div className="text-xs text-slate-500">Backend did not return this visual asset.</div>
                )}
            </div>
            <div className="px-5 py-3 border-t border-white/10 text-[11px] text-slate-400">
                Every displayed heatmap, mask, and overlay is the image returned by the EVT-CLIP backend; the browser does not redraw defect regions.
            </div>
        </div>
    );
};

export default ImageViewer;
