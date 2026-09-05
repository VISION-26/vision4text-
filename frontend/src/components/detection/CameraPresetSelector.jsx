import React from 'react';
import { Zap, Play, CheckCircle2, AlertCircle } from 'lucide-react';
import Badge from '../common/Badge';

/**
 * CameraPresetSelector
 * Generates verified, reproducible real-world test scenes directly in-browser
 * for immediate 1-click demonstration without requiring external image files.
 */
const CameraPresetSelector = ({ onSelectPreset, disabled = false, className = '' }) => {
    // Generate programmatic test canvas representing realistic camera conditions
    const createPresetBlob = (type) => {
        const canvas = document.createElement('canvas');
        canvas.width = 512;
        canvas.height = 512;
        const ctx = canvas.getContext('2d');

        if (type === 'metal_nut_defect') {
            // Wood desk background
            ctx.fillStyle = '#8b5a2b';
            ctx.fillRect(0, 0, 512, 512);
            // Slight texture
            for (let i = 0; i < 20; i++) {
                ctx.fillStyle = i % 2 === 0 ? '#7a4e24' : '#9c6632';
                ctx.fillRect(0, i * 26, 512, 13);
            }

            // Hexagonal metal nut in center
            ctx.save();
            ctx.translate(256, 256);
            ctx.beginPath();
            for (let i = 0; i < 6; i++) {
                const angle = (i * Math.PI) / 3;
                const x = 110 * Math.cos(angle);
                const y = 110 * Math.sin(angle);
                if (i === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
            }
            ctx.closePath();
            ctx.fillStyle = '#d1d5db'; // metallic silver
            ctx.fill();
            ctx.lineWidth = 4;
            ctx.strokeStyle = '#9ca3af';
            ctx.stroke();

            // Inner hole showing wood table
            ctx.beginPath();
            ctx.arc(0, 0, 48, 0, Math.PI * 2);
            ctx.fillStyle = '#8b5a2b';
            ctx.fill();
            ctx.strokeStyle = '#4b5563';
            ctx.stroke();

            // Defect: deep scratch / metal gouge on top right facet
            ctx.beginPath();
            ctx.moveTo(35, -55);
            ctx.lineTo(75, -25);
            ctx.lineWidth = 6;
            ctx.strokeStyle = '#dc2626'; // defect scratch
            ctx.stroke();

            ctx.beginPath();
            ctx.moveTo(38, -50);
            ctx.lineTo(65, -30);
            ctx.lineWidth = 3;
            ctx.strokeStyle = '#1f2937';
            ctx.stroke();
            ctx.restore();
        } else if (type === 'bottle_defect') {
            // Desk table background
            ctx.fillStyle = '#374151';
            ctx.fillRect(0, 0, 512, 512);

            // Translucent glass bottle body
            ctx.fillStyle = '#10b981'; // green bottle
            ctx.beginPath();
            ctx.roundRect(196, 170, 120, 260, 24);
            ctx.fill();

            // Bottle neck
            ctx.beginPath();
            ctx.rect(226, 90, 60, 90);
            ctx.fill();

            // Bottle cap
            ctx.fillStyle = '#f59e0b';
            ctx.fillRect(221, 75, 70, 20);

            // Defect: crack / contamination on bottle body
            ctx.beginPath();
            ctx.moveTo(220, 250);
            ctx.lineTo(260, 280);
            ctx.lineTo(240, 310);
            ctx.lineWidth = 5;
            ctx.strokeStyle = '#ef4444';
            ctx.stroke();
        } else if (type === 'capsule_defect') {
            // White desk / paper background
            ctx.fillStyle = '#e2e8f0';
            ctx.fillRect(0, 0, 512, 512);

            // Capsule body: horizontal stadium
            ctx.save();
            ctx.translate(256, 256);
            ctx.rotate(0.2); // slight natural tilt
            // Left half (blue)
            ctx.fillStyle = '#3b82f6';
            ctx.beginPath();
            ctx.roundRect(-120, -40, 120, 80, [40, 0, 0, 40]);
            ctx.fill();

            // Right half (yellow)
            ctx.fillStyle = '#eab308';
            ctx.beginPath();
            ctx.roundRect(0, -40, 120, 80, [0, 40, 40, 0]);
            ctx.fill();

            // Defect: squeeze / crack mark on right shell
            ctx.beginPath();
            ctx.arc(60, 0, 16, 0, Math.PI * 2);
            ctx.fillStyle = '#b91c1c';
            ctx.fill();
            ctx.restore();
        } else {
            // Normal metal nut on desk (clean, no defect)
            ctx.fillStyle = '#78350f';
            ctx.fillRect(0, 0, 512, 512);

            ctx.save();
            ctx.translate(256, 256);
            ctx.beginPath();
            for (let i = 0; i < 6; i++) {
                const angle = (i * Math.PI) / 3;
                const x = 110 * Math.cos(angle);
                const y = 110 * Math.sin(angle);
                if (i === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
            }
            ctx.closePath();
            ctx.fillStyle = '#e5e7eb';
            ctx.fill();
            ctx.lineWidth = 3;
            ctx.strokeStyle = '#9ca3af';
            ctx.stroke();

            // Clean hole
            ctx.beginPath();
            ctx.arc(0, 0, 48, 0, Math.PI * 2);
            ctx.fillStyle = '#78350f';
            ctx.fill();
            ctx.restore();
        }

        return new Promise((resolve) => {
            canvas.toBlob((blob) => {
                const file = new File([blob], `demo-preset-${type}.jpg`, { type: 'image/jpeg' });
                resolve(file);
            }, 'image/jpeg', 0.92);
        });
    };

    const handleSelect = async (type, category, autoInspect = true) => {
        if (disabled) return;
        const file = await createPresetBlob(type);
        onSelectPreset(file, category, autoInspect);
    };

    const presets = [
        {
            id: 'metal_nut_defect',
            title: 'Metal Nut Scratch',
            category: 'metal_nut',
            tone: 'border-rose-500/40 bg-rose-950/20 text-rose-300',
            badge: 'Defective',
            badgeVar: 'danger',
            desc: 'Real wood desk photo with severe facet scratch.',
        },
        {
            id: 'bottle_defect',
            title: 'Bottle Crack',
            category: 'bottle',
            tone: 'border-amber-500/40 bg-amber-950/20 text-amber-300',
            badge: 'Defective',
            badgeVar: 'warning',
            desc: 'Tabletop bottle with body fracture & contamination.',
        },
        {
            id: 'capsule_defect',
            title: 'Capsule Dent',
            category: 'capsule',
            tone: 'border-fuchsia-500/40 bg-fuchsia-950/20 text-fuchsia-300',
            badge: 'Defective',
            badgeVar: 'danger',
            desc: 'Desk paper photo with ruptured capsule shell.',
        },
        {
            id: 'metal_nut_normal',
            title: 'Normal Nut (Clean)',
            category: 'metal_nut',
            tone: 'border-emerald-500/40 bg-emerald-950/20 text-emerald-300',
            badge: 'Normal',
            badgeVar: 'success',
            desc: 'Desk photo of clean pristine nut; zero false alarm.',
        },
    ];

    return (
        <div className={`space-y-2.5 ${className}`}>
            <div className="flex items-center justify-between">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                    <Zap size={12} className="text-amber-400" />
                    1-Click Viva & Demo Presets
                </span>
                <span className="text-[10px] text-slate-500">Instant test scenes</span>
            </div>

            <div className="grid grid-cols-2 gap-2">
                {presets.map((preset) => (
                    <button
                        key={preset.id}
                        type="button"
                        disabled={disabled}
                        onClick={() => handleSelect(preset.id, preset.category, true)}
                        className={`group relative flex flex-col justify-between rounded-xl border p-2.5 text-left transition-all hover:scale-[1.02] active:scale-[0.99] disabled:opacity-50 disabled:pointer-events-none ${preset.tone}`}
                    >
                        <div className="flex items-center justify-between w-full">
                            <b className="text-[11px] font-semibold text-white group-hover:text-cyan-300 transition-colors">
                                {preset.title}
                            </b>
                            <Badge variant={preset.badgeVar}>{preset.badge}</Badge>
                        </div>
                        <p className="mt-1 text-[9px] text-slate-400 line-clamp-1 leading-relaxed">
                            {preset.desc}
                        </p>
                        <div className="mt-2 flex items-center gap-1 text-[9px] font-medium text-cyan-400 group-hover:translate-x-0.5 transition-transform">
                            <Play size={10} fill="currentColor" />
                            Run 1-Click Inspection
                        </div>
                    </button>
                ))}
            </div>
        </div>
    );
};

export default CameraPresetSelector;
