import React, { useEffect, useMemo, useState } from 'react';
import {
    AlertTriangle,
    CheckCircle2,
    Cpu,
    Play,
    RotateCcw,
    ScanLine,
    ShieldCheck,
} from 'lucide-react';

const stageForStatus = (status = '') => {
    const value = status.toLowerCase();
    if (value.includes('upload') || value.includes('prepar') || value.includes('submit')) return 0;
    if (value.includes('queue') || value.includes('waiting') || value.includes('starting') || value.includes('cpu worker')) return 1;
    if (value.includes('running') || value.includes('validat') || value.includes('model') || value.includes('evt-clip') || value.includes('inspecting')) return 2;
    if (value.includes('complete') || value.includes('final') || value.includes('rejected')) return 3;
    return 0;
};

const statusLabel = (status = '') => {
    const value = status.toLowerCase();
    if (value.includes('upload') || value.includes('prepar')) return 'Preparing inspection image';
    if (value.includes('submit')) return 'Submitting inspection job';
    if (value.includes('queue') || value.includes('waiting') || value.includes('cpu worker') || value.includes('starting')) return 'Waiting for CPU worker';
    if (value.includes('validat') || value.includes('running') || value.includes('inspect')) return 'Validating input and running EVT-CLIP inspection';
    if (value.includes('complete') || value.includes('final')) return 'Finalizing evidence and decision';
    return status || 'Running inspection';
};

const resultPresentation = (result) => {
    if (!result) return null;
    if (!result.resultValid) {
        const hardRejected = ['invalid_category', 'unsupported_input'].includes(result.rejectionCode);
        return {
            label: 'INPUT REJECTED',
            detail: result.notes || 'Input validation did not pass',
            tone: 'review',
            Icon: AlertTriangle,
        };
    }
    if (result.prediction === 'Anomalous') {
        return {
            label: 'ANOMALY DETECTED',
            detail: 'Defect evidence is ready',
            tone: 'anomaly',
            Icon: AlertTriangle,
        };
    }
    return {
        label: 'NORMAL',
        detail: 'Inspection completed successfully',
        tone: 'normal',
        Icon: CheckCircle2,
    };
};

const InspectionRunAnimation = ({
    imagePreview,
    category,
    isRunning,
    jobStatus,
    result,
    onRun,
    onReset,
    runDisabled = false,
    runLabel = 'Run Inspection',
}) => {
    const activeStage = stageForStatus(jobStatus);
    const completion = useMemo(() => resultPresentation(result), [result]);
    const CompletionIcon = completion?.Icon;
    // Keep a completed or rejected result visible until the operator changes or resets the input.
    // A timed transition back to the run screen made a completed inspection look like a loop.
    const view = isRunning ? 'running' : (completion ? 'complete' : 'idle');
    const categoryLabel = (category || 'product').replace('_', ' ');

    return (
        <div className="evt-inspection-shell" aria-live="polite">
            <div className="evt-inspection-topline">
                <div className="flex items-center gap-2 min-w-0">
                    <span className={`evt-inspection-dot ${isRunning ? 'is-live' : ''}`} />
                    <span className="truncate">{isRunning ? statusLabel(jobStatus) : 'Ready for production inspection'}</span>
                </div>
                <span className="evt-inspection-category">{categoryLabel}</span>
            </div>

            <div className={`evt-inspection-viewport is-${view}`}>
                {view === 'idle' && (
                    <button
                        type="button"
                        onClick={onRun}
                        disabled={!imagePreview || runDisabled}
                        className="evt-inspection-run-button"
                    >
                        <span className="evt-inspection-run-glow" />
                        <span className="relative z-10 flex items-center justify-center gap-2.5">
                            <Play size={17} fill="currentColor" />
                            {!imagePreview ? 'Select an image first' : runLabel}
                        </span>
                    </button>
                )}

                {view === 'running' && (
                    <>
                        <div className="evt-inspection-road" aria-hidden="true">
                            <span className="evt-road-line evt-road-line-one" />
                            <span className="evt-road-line evt-road-line-two" />
                        </div>

                        <div className="evt-inspection-scanner" aria-hidden="true">
                            <div className="evt-scanner-cap">
                                <ScanLine size={14} />
                                <span>AI SCAN</span>
                            </div>
                            <span className="evt-scan-beam" />
                            <span className="evt-scan-haze" />
                        </div>

                        <div className="evt-inspection-carrier">
                            <div className="evt-sample-frame">
                                {imagePreview ? <img src={imagePreview} alt="Selected inspection sample" /> : <Cpu size={24} />}
                            </div>
                            <div className="evt-carrier-base">
                                <span />
                                <span />
                            </div>
                        </div>

                        <div className="evt-model-pulse evt-model-pulse-left">EfficientAD</div>
                        <div className="evt-model-pulse evt-model-pulse-right">PatchCore</div>
                        <div className="evt-refiner-badge"><ShieldCheck size={12} /> EVT-CLIP</div>
                    </>
                )}

                {view === 'complete' && completion && (
                    <div className={`evt-inspection-complete is-${completion.tone}`}>
                        <div className="evt-complete-sample">
                            {imagePreview && <img src={imagePreview} alt="Inspected sample" />}
                            <span className="evt-complete-ring" />
                        </div>
                        <div className="evt-complete-copy">
                            <span className="evt-complete-kicker">INSPECTION COMPLETE</span>
                            <strong>{CompletionIcon && <CompletionIcon size={18} />} {completion.label}</strong>
                            <span>{completion.detail}</span>
                        </div>
                    </div>
                )}
            </div>

            <div className="evt-inspection-progress-row">
                {['Input', 'CPU queue', 'AI models', 'Decision'].map((label, index) => (
                    <div key={label} className={`evt-inspection-progress-step ${isRunning && index <= activeStage ? 'is-active' : ''} ${!isRunning && result ? 'is-done' : ''}`}>
                        <span>{index + 1}</span>
                        <small>{label}</small>
                    </div>
                ))}
                <button
                    type="button"
                    onClick={onReset}
                    disabled={!imagePreview || isRunning}
                    className="evt-inspection-reset"
                    title="Reset inspection"
                    aria-label="Reset inspection"
                >
                    <RotateCcw size={15} />
                </button>
            </div>
        </div>
    );
};

export default InspectionRunAnimation;
