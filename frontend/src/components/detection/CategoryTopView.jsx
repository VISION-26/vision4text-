import React, { useEffect, useState } from 'react';
import { displayCategory } from '../../constants/categoryLabels';

const SAMPLE_BASE = '/example-assets';

const CategoryTopView = ({ category }) => {
    const [imgSrc, setImgSrc] = useState(`${SAMPLE_BASE}/${encodeURIComponent(category)}/good`);
    const [triedFallback, setTriedFallback] = useState(false);
    const [failed, setFailed] = useState(false);

    useEffect(() => {
        setImgSrc(`${SAMPLE_BASE}/${encodeURIComponent(category)}/good`);
        setTriedFallback(false);
        setFailed(false);
    }, [category]);

    const handleError = () => {
        if (!triedFallback) {
            setTriedFallback(true);
            setImgSrc(`${SAMPLE_BASE}/${encodeURIComponent(category)}/bad`);
        } else {
            setFailed(true);
        }
    };

    return (
        <div className="rounded-xl border border-slate-200 bg-white p-3 text-center dark:border-slate-800 dark:bg-[#07101f]">
            <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-500">REAL DATASET REFERENCE</p>
            {!failed && (
                <div className="my-2 flex justify-center items-center h-28 overflow-hidden rounded-lg bg-slate-50 dark:bg-[#020617] border border-slate-100 dark:border-slate-800/60">
                    <img
                        key={imgSrc}
                        src={imgSrc}
                        alt={`Real ${category} dataset reference`}
                        onError={handleError}
                        className="h-full w-full object-contain p-1"
                    />
                </div>
            )}
            <p className="text-sm font-semibold text-slate-800 dark:text-slate-100">{displayCategory(category)}</p>
        </div>
    );
};

export default CategoryTopView;
