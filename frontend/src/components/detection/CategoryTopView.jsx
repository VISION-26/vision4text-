import React from 'react';
import { displayCategory } from '../../constants/categoryLabels';

const ACCENTS = ['#ea580c', '#0891b2', '#db2777', '#7c3aed', '#0f766e', '#d97706', '#4f46e5', '#e11d48'];

const TopViewMark = ({ accent, variant }) => {
    const ridges = 10 + (variant % 4) * 2;
    const capRadius = 24 + (variant % 3);
    const marks = Array.from({ length: ridges }, (_, index) => {
        const angle = (index / ridges) * Math.PI * 2;
        return {
            x1: 60 + Math.cos(angle) * (capRadius - 2),
            y1: 58 + Math.sin(angle) * (capRadius - 2),
            x2: 60 + Math.cos(angle) * (capRadius + 7),
            y2: 58 + Math.sin(angle) * (capRadius + 7),
        };
    });

    return (
        <svg viewBox="0 0 120 120" className="h-24 w-24" aria-hidden="true">
            <ellipse cx="60" cy="108" rx="30" ry="6" fill="rgba(23,23,23,0.08)" />
            <circle cx="60" cy="58" r="48" fill="#f7f5f1" stroke="#e7e3dc" strokeWidth="1.5" />
            <circle cx="60" cy="58" r="40" fill="#fff" stroke={accent} strokeWidth="2.5" />
            {marks.map((mark) => (
                <line key={`${mark.x1}-${mark.y1}`} x1={mark.x1} y1={mark.y1} x2={mark.x2} y2={mark.y2} stroke={accent} strokeWidth="1.6" strokeLinecap="round" opacity="0.55" />
            ))}
            <circle cx="60" cy="58" r={capRadius} fill={accent} />
            <circle cx="60" cy="58" r={capRadius - 7} fill="none" stroke="#fff" strokeWidth="1.4" opacity="0.7" />
            {variant % 3 === 0 && <circle cx="60" cy="58" r="6" fill="#fff" />}
            {variant % 3 === 1 && <circle cx="60" cy="58" r="7" fill="none" stroke="#fff" strokeWidth="2.2" />}
            {variant % 3 === 2 && <circle cx="60" cy="58" r="3.2" fill="#fff" />}
        </svg>
    );
};

const CategoryTopView = ({ category, categories = [] }) => {
    const index = Math.max(0, categories.indexOf(category));
    const accent = ACCENTS[index % ACCENTS.length];

    return (
        <div className="rounded-xl border border-slate-200 bg-white p-3 text-center dark:border-slate-800">
            <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-500">TOPVIEW TO THE UPLOADED CATEGORY</p>
            <div className="mt-1 flex justify-center">
                <TopViewMark accent={accent} variant={index} />
            </div>
            <p className="text-sm font-semibold text-slate-800 dark:text-slate-100">{displayCategory(category)}</p>
        </div>
    );
};

export default CategoryTopView;
