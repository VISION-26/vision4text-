import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import useAuth from '../../hooks/useAuth';
import Input from '../../components/common/Input';
import Button from '../../components/common/Button';
import {
    ArrowLeft, Mail, Lock, ShieldCheck, Cpu, ScanLine, FileCheck2, Activity,
} from 'lucide-react';

const Login = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const { login, loading } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (event) => {
        event.preventDefault();
        setError('');
        if (!email || !password) {
            setError('Enter the project account email and password.');
            return;
        }
        try {
            await login(email, password);
            navigate('/dashboard');
        } catch (err) {
            setError(err.message || 'Sign-in failed. Check the credentials and try again.');
        }
    };

    return (
        <div className="min-h-screen bg-[#060611] text-white font-sans lg:grid lg:grid-cols-[1.16fr_.84fr]">
            <section className="relative min-h-[300px] overflow-hidden border-b border-white/10 lg:min-h-screen lg:border-b-0 lg:border-r" aria-label="Vision Text inspection preview">
                <video
                    className="absolute inset-0 h-full w-full object-cover"
                    autoPlay
                    muted
                    loop
                    playsInline
                    preload="metadata"
                    poster="/vision-text-login-poster.png"
                    aria-hidden="true"
                >
                    <source src="/vision-text-login-loop.mp4" type="video/mp4" />
                </video>
                <div className="absolute inset-0 bg-gradient-to-r from-[#060611]/35 via-[#060611]/15 to-[#060611]/80 lg:bg-gradient-to-t lg:from-[#060611]/90 lg:via-[#060611]/20 lg:to-[#060611]/20" />
                <div className="absolute inset-0 evt-login-video-vignette" />

                <div className="relative z-10 flex min-h-[300px] h-full flex-col justify-between p-5 sm:p-8 lg:p-10">
                    <Link to="/" className="inline-flex w-fit items-center gap-2 rounded-full border border-white/15 bg-black/20 px-3 py-2 text-[11px] font-semibold text-slate-200 backdrop-blur-md transition hover:bg-black/35">
                        <ArrowLeft size={14} /> Overview
                    </Link>

                    <div className="max-w-xl pb-2 lg:pb-5">
                        <div className="mb-4 hidden items-center gap-2 text-[10px] font-bold uppercase tracking-[.18em] text-cyan-200 sm:flex">
                            <span className="h-2 w-2 rounded-full bg-fuchsia-400 shadow-[0_0_16px_rgba(232,44,193,.65)]" />
                            Inspection process preview
                        </div>
                        <h1 className="max-w-lg text-3xl font-black leading-[1.04] tracking-[-.04em] sm:text-4xl lg:text-5xl">
                            One image in. <span className="evt-gradient-text">Evidence at every stage.</span>
                        </h1>
                        <p className="mt-3 max-w-xl text-xs leading-5 text-slate-300/85 sm:text-sm sm:leading-6">
                            The preview shows the same inspection story used by the application: validate the input, run both specialists, refine the anomaly map, and preserve the result as evidence.
                        </p>
                        <div className="mt-5 hidden grid-cols-3 gap-2 sm:grid">
                            {[
                                [ScanLine, '5 categories', 'trained industrial scope'],
                                [Cpu, 'CPU worker', 'queued Modal inference'],
                                [FileCheck2, 'Evidence', 'PDF + signed archive'],
                            ].map(([Icon, value, label]) => (
                                <div key={value} className="rounded-xl border border-white/12 bg-black/25 p-3 backdrop-blur-md">
                                    <Icon size={16} className="text-fuchsia-300" />
                                    <b className="mt-2 block text-xs">{value}</b>
                                    <span className="mt-0.5 block text-[9px] leading-4 text-slate-400">{label}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </section>

            <main className="relative flex min-h-[calc(100vh-300px)] items-center justify-center overflow-hidden bg-[#f7f7fb] px-5 py-10 text-slate-950 dark:bg-[#090914] dark:text-white lg:min-h-screen lg:px-10">
                <div className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full bg-fuchsia-500/10 blur-3xl" />
                <div className="pointer-events-none absolute -bottom-24 -left-24 h-72 w-72 rounded-full bg-cyan-500/10 blur-3xl" />

                <div className="relative z-10 w-full max-w-[430px]">
                    <div className="mb-8 flex items-center gap-3">
                        <span className="flex h-9 items-end gap-[3px]" aria-hidden="true">
                            <i className="block h-5 w-2 rounded-sm bg-[#fc4c02]" />
                            <i className="block h-9 w-2 rounded-sm bg-[#ef2cc1]" />
                            <i className="block h-7 w-2 rounded-sm bg-[#bdbbff]" />
                        </span>
                        <div>
                            <p className="text-sm font-black tracking-tight">EVT-CLIP</p>
                            <p className="text-[10px] text-slate-500 dark:text-slate-400">Vision-language anomaly inspection workspace</p>
                        </div>
                    </div>

                    <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-[0_24px_80px_rgba(1,1,32,.10)] dark:border-white/10 dark:bg-[#101021] sm:p-8">
                        <div className="flex items-start justify-between gap-4">
                            <div>
                                <p className="text-[10px] font-bold uppercase tracking-[.18em] text-fuchsia-600 dark:text-fuchsia-300">Secure access</p>
                                <h2 className="mt-2 text-3xl font-black tracking-[-.035em]">Welcome back</h2>
                                <p className="mt-2 text-xs leading-5 text-slate-500 dark:text-slate-400">Sign in to open the dashboard, run inspections, inspect model evidence, and export reports.</p>
                            </div>
                            <span className="hidden h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-fuchsia-50 text-fuchsia-600 dark:bg-fuchsia-950/30 dark:text-fuchsia-300 sm:flex">
                                <Activity size={18} />
                            </span>
                        </div>

                        <form onSubmit={handleSubmit} className="mt-7 space-y-4">
                            {error && (
                                <div role="alert" className="flex items-start gap-2 rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs font-medium text-rose-700 dark:border-rose-900/40 dark:bg-rose-950/20 dark:text-rose-300">
                                    <ShieldCheck size={16} className="mt-0.5 shrink-0" /> {error}
                                </div>
                            )}
                            <Input
                                label="Email address"
                                id="email"
                                type="email"
                                value={email}
                                onChange={(event) => setEmail(event.target.value)}
                                placeholder="name@example.com"
                                autoComplete="username"
                                required
                                leadingIcon={Mail}
                                inputClassName="h-12 rounded-xl"
                            />
                            <Input
                                label="Password"
                                id="password"
                                type="password"
                                value={password}
                                onChange={(event) => setPassword(event.target.value)}
                                placeholder="Enter password"
                                autoComplete="current-password"
                                required
                                leadingIcon={Lock}
                                inputClassName="h-12 rounded-xl"
                            />
                            <Button type="submit" variant="gradient" className="w-full py-3.5 rounded-xl" disabled={loading}>
                                {loading ? 'Signing in…' : 'Sign In'}
                            </Button>
                        </form>
                    </div>

                    <p className="mt-5 text-center text-[10px] text-slate-400">Five industrial categories · model-stage evidence · stored inspection history</p>
                </div>
            </main>
        </div>
    );
};

export default Login;
