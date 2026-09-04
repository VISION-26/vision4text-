import React, { useEffect, useRef, useState } from 'react';
import { Camera, RefreshCw, X } from 'lucide-react';
import Button from '../common/Button';

const CameraCapture = ({ onCapture, disabled = false }) => {
    const videoRef = useRef(null);
    const streamRef = useRef(null);
    const fallbackInputRef = useRef(null);
    const [open, setOpen] = useState(false);
    const [facingMode, setFacingMode] = useState('environment');
    const [error, setError] = useState('');
    const [starting, setStarting] = useState(false);

    const stopStream = () => {
        streamRef.current?.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
        if (videoRef.current) videoRef.current.srcObject = null;
    };

    const closeCamera = () => {
        stopStream();
        setOpen(false);
        setStarting(false);
    };

    useEffect(() => () => stopStream(), []);

    useEffect(() => {
        if (open && streamRef.current && videoRef.current) {
            videoRef.current.srcObject = streamRef.current;
            videoRef.current.play().catch(() => {});
        }
    }, [open, starting]);

    const startCamera = async (mode = facingMode) => {
        setError('');
        if (!navigator.mediaDevices?.getUserMedia) {
            setError('Live camera is unavailable in this browser. Use the device camera option instead.');
            fallbackInputRef.current?.click();
            return;
        }

        setOpen(true);
        setStarting(true);
        stopStream();
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    facingMode: { ideal: mode },
                    width: { ideal: 1920 },
                    height: { ideal: 1080 },
                },
                audio: false,
            });
            streamRef.current = stream;
            if (videoRef.current) {
                videoRef.current.srcObject = stream;
                await videoRef.current.play();
            }
        } catch (cameraError) {
            console.error('Unable to start camera', cameraError);
            closeCamera();
            setError('Camera permission was denied or no camera was found. You can still choose a camera photo from your device.');
        } finally {
            setStarting(false);
        }
    };

    const switchCamera = async () => {
        const nextMode = facingMode === 'environment' ? 'user' : 'environment';
        setFacingMode(nextMode);
        await startCamera(nextMode);
    };

    const captureFrame = (inspectImmediately) => {
        const video = videoRef.current;
        if (!video?.videoWidth || !video?.videoHeight) {
            setError('The camera is still starting. Wait a moment and try again.');
            return;
        }

        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
        canvas.toBlob((blob) => {
            if (!blob) {
                setError('The camera frame could not be captured. Please try again.');
                return;
            }
            const file = new File([blob], `camera-${Date.now()}.jpg`, { type: 'image/jpeg' });
            closeCamera();
            onCapture(file, inspectImmediately);
        }, 'image/jpeg', 0.94);
    };

    const handleFallbackCapture = (event) => {
        const file = event.target.files?.[0];
        if (file) onCapture(file, false);
        event.target.value = '';
    };

    return (
        <>
            <input
                ref={fallbackInputRef}
                type="file"
                accept="image/*"
                capture="environment"
                onChange={handleFallbackCapture}
                className="hidden"
                aria-hidden="true"
            />
            <div className="space-y-1.5">
                <Button variant="secondary" className="w-full" icon={Camera} disabled={disabled} onClick={() => startCamera()}>
                    Open Camera
                </Button>
                {error && <p className="text-[10px] leading-relaxed text-rose-500" role="alert">{error}</p>}
            </div>

            {open && (
                <div className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-950/90 p-3 sm:p-6" role="dialog" aria-modal="true" aria-label="Camera capture">
                    <div className="w-full max-w-4xl overflow-hidden rounded-2xl border border-slate-700 bg-slate-900 shadow-2xl">
                        <div className="flex items-center justify-between border-b border-slate-700 px-4 py-3">
                            <div>
                                <h2 className="text-sm font-bold text-white">Capture Inspection Image</h2>
                                <p className="text-[11px] text-slate-400">Keep the product steady, centered, and well lit.</p>
                            </div>
                            <button onClick={closeCamera} className="rounded-lg p-2 text-slate-300 hover:bg-slate-800 hover:text-white" aria-label="Close camera">
                                <X size={20} />
                            </button>
                        </div>

                        <div className="relative flex min-h-[280px] items-center justify-center bg-black sm:min-h-[480px]">
                            <video ref={videoRef} autoPlay playsInline muted className="max-h-[70vh] w-full object-contain" />
                            {starting ? (
                                <div className="absolute text-sm font-semibold text-slate-300">Starting camera…</div>
                            ) : (
                                <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
                                    <div className="relative flex items-center justify-center">
                                        <div className="h-52 w-52 sm:h-64 sm:w-64 rounded-full border-2 border-dashed border-cyan-400/80 shadow-[0_0_25px_rgba(6,182,212,0.35)]" />
                                        <div className="absolute -top-2 -left-2 h-4 w-4 border-t-2 border-l-2 border-cyan-300" />
                                        <div className="absolute -top-2 -right-2 h-4 w-4 border-t-2 border-r-2 border-cyan-300" />
                                        <div className="absolute -bottom-2 -left-2 h-4 w-4 border-b-2 border-l-2 border-cyan-300" />
                                        <div className="absolute -bottom-2 -right-2 h-4 w-4 border-b-2 border-r-2 border-cyan-300" />
                                    </div>
                                    <span className="mt-3 rounded-full bg-slate-950/80 px-3 py-1 text-[11px] font-medium text-cyan-200 backdrop-blur border border-cyan-500/30">
                                        Center product inside target guide
                                    </span>
                                </div>
                            )}
                        </div>

                        <div className="grid grid-cols-1 gap-2 border-t border-slate-700 p-4 sm:grid-cols-3">
                            <Button variant="secondary" icon={RefreshCw} onClick={switchCamera} disabled={starting}>Switch Camera</Button>
                            <Button variant="secondary" icon={Camera} onClick={() => captureFrame(false)} disabled={starting}>Capture Image</Button>
                            <Button variant="gradient" icon={Camera} onClick={() => captureFrame(true)} disabled={starting}>Capture & Inspect</Button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
};

export default CameraCapture;
