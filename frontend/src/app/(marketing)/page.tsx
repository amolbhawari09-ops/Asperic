"use client";

import Link from "next/link";
import { useEffect } from "react";
import {
  AlertTriangle,
  Shield,
  Globe,
  Database,
  XCircle,
  ArrowRight,
} from "lucide-react";

export default function LandingPage() {
  // subtle scroll reveal
  useEffect(() => {
    const els = document.querySelectorAll(".reveal-hidden");
    const obs = new IntersectionObserver(
      entries =>
        entries.forEach(e => {
          if (e.isIntersecting) e.target.classList.add("reveal-visible");
        }),
      { threshold: 0.15 }
    );
    els.forEach(el => obs.observe(el));
    return () => obs.disconnect();
  }, []);

  return (
    <div
      className="min-h-screen text-gray-200 selection:bg-emerald-500/20"
      style={{ backgroundColor: "#0B0F14" }} // Hardcoded safety
    >

      {/* BACKGROUND DEPTH & TEXTURE */}
      <div className="fixed inset-0 -z-10 pointer-events-none">
        {/* Base Layer */}
        <div className="absolute inset-0 bg-[#0B0F14]" />

        {/* Radial Glows for Life */}
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-indigo-900/10 via-[#0B0F14] to-[#0B0F14]" />

        {/* Engineered Grid */}
        <div className="absolute inset-0 opacity-[0.03]
          bg-[linear-gradient(to_right,#ffffff08_1px,transparent_1px),
          linear-gradient(to_bottom,#ffffff08_1px,transparent_1px)]
          bg-[size:32px_32px]" />

        {/* Noise Texture for Tactile Feel */}
        <div className="absolute inset-0 opacity-[0.15] mix-blend-overlay"
          style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' opacity='1'/%3E%3C/svg%3E")` }}
        />
      </div>

      {/* NAV */}
      <nav className="h-20 border-b border-white/5 flex items-center justify-between px-8 bg-[#0B0F14]/80 backdrop-blur-md sticky top-0 z-50">
        <div className="flex items-center gap-4 group cursor-pointer">
          <div className="relative">
            <div className="absolute inset-0 bg-emerald-500/20 blur-md rounded-full opacity-0 group-hover:opacity-100 transition-opacity" />
            <img src="/asperic-logo.png" alt="Asperic" className="relative w-7 h-7" />
          </div>
          <span className="font-bold tracking-[0.2em] text-sm text-white group-hover:text-emerald-50 transition-colors">ASPERIC</span>
        </div>
        <Link href="/login" className="text-xs font-bold tracking-wide bg-white text-black px-5 py-2.5 rounded-full hover:bg-gray-200 transition-colors">
          Sign In
        </Link>
      </nav>

      {/* HERO */}
      <section className="relative max-w-6xl mx-auto px-8 pt-32 pb-24 reveal-hidden">
        {/* Local Focus Glow */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-emerald-500/10 blur-[120px] rounded-full pointer-events-none -z-10 mix-blend-screen" />

        <div className="inline-flex items-center gap-2 text-[11px] text-red-400 bg-red-500/10 px-3 py-1 rounded-full mb-8 font-mono uppercase tracking-wider border border-red-500/10">
          <AlertTriangle size={12} />
          Built for decisions where mistakes are costly
        </div>

        <h1 className="text-[72px] leading-[0.95] font-bold text-white max-w-4xl tracking-tight">
          Intelligence,<br />Not Just Conversation.
        </h1>

        <p className="mt-12 text-xl text-gray-200/90 max-w-xl leading-relaxed font-medium">
          Chatbots optimize for sounding good. Asperic optimizes for being right —
          even if that means refusing to answer.
        </p>

        <p className="mt-6 text-sm text-gray-400/80 max-w-[55ch] leading-relaxed font-medium">
          A confident answer that is wrong is more dangerous than no answer.
        </p>

        <div className="mt-16 flex flex-col items-start gap-5">
          <Link
            href="/signup"
            className="inline-flex items-center gap-3 bg-emerald-600 hover:bg-emerald-500
              text-white font-bold px-9 py-4 rounded-lg
              shadow-[0_0_30px_-10px_rgba(16,185,129,0.5)] hover:shadow-[0_0_50px_-10px_rgba(16,185,129,0.7)] transition-all duration-300"
          >
            Get Started <ArrowRight size={16} />
          </Link>
          <div className="text-[10px] text-gray-500 font-mono tracking-wide uppercase flex gap-3 pl-1">
            <span>No training</span>
            <span className="text-gray-800">•</span>
            <span>No retention</span>
            <span className="text-gray-800">•</span>
            <span>Local-first</span>
          </div>
        </div>
      </section>

      {/* HERO */}
      <section className="relative max-w-6xl mx-auto px-8 pt-32 pb-48 reveal-hidden">
        {/* ... content ... */}
        {/* (Hero content maintained, just showing context for next sections) */}
      </section>

      {/* PAUSE -> STATEMENT: WHY CHATBOTS FAIL */}
      <section className="py-20 bg-[#0E131A] border-y border-white/[0.02] reveal-hidden">
        <div className="max-w-5xl mx-auto px-8">
          <h2 className="text-4xl font-bold mb-12 text-white tracking-tight">
            Why most AI tools are unsafe for real decisions
          </h2>

          <ul className="space-y-6 text-gray-300/80 text-[15px] max-w-2xl font-medium pl-2 border-l-2 border-white/5">
            <li className="pl-4">• Confident answers that turn out to be wrong</li>
            <li className="pl-4">• Answers based on outdated knowledge, presented as current</li>
            <li className="pl-4">• Critical context forgotten as conversations grow</li>
            <li className="pl-4">• Guessing instead of admitting uncertainty</li>
          </ul>
        </div>
      </section>

      {/* PAUSE -> PROOF: COST OF BEING WRONG */}
      <section className="py-20 max-w-5xl mx-auto px-8 reveal-hidden">
        <h2 className="text-3xl font-bold mb-10 text-white/90">
          Accuracy isn’t optional when decisions cost money, systems, or trust
        </h2>
        <p className="text-gray-300 max-w-[65ch] text-lg leading-relaxed font-medium">
          Financial analysis, infrastructure design, internal tooling,
          and compliance decisions punish confident mistakes.
        </p>
      </section>

      {/* PAUSE -> SOLUTION: HOW ASPERIC THINKS */}
      <section className="py-20 bg-[#0E131A] border-y border-white/[0.02] reveal-hidden">
        <div className="max-w-6xl mx-auto px-8 grid md:grid-cols-3 gap-10">
          <Step icon={<Globe />} title="Works with real, current data">
            Stop relying on stale training cutoffs. Connect to live systems for up-to-the-second accuracy.
          </Step>
          <Step icon={<Database />} title="Uses your data without exporting it">
            Full project context awareness with zero data retention or external model training.
          </Step>
          <Step icon={<Shield />} title="Verifies answers — or says “I don’t know”">
            Eliminate hallucinations with strict refusal protocols when certainty is impossible.
          </Step>
        </div>
      </section>

      {/* PAUSE -> CLARITY: WHO NOT FOR */}
      <section className="py-20 bg-[#050608] border-y border-red-500/5 reveal-hidden">
        <div className="max-w-4xl mx-auto px-8">
          <h2 className="text-3xl font-bold mb-12 text-white tracking-tight">
            Who this is <span className="text-red-500">NOT</span> for
          </h2>
          <ul className="space-y-6 text-gray-400 font-medium text-lg">
            <li className="flex gap-6 items-center p-4 rounded-lg hover:bg-white/[0.02] transition-colors border border-transparent hover:border-white/[0.02]">
              <XCircle className="text-red-500 shrink-0" size={24} />
              <span>Creative writing or entertainment</span>
            </li>
            <li className="flex gap-6 items-center p-4 rounded-lg hover:bg-white/[0.02] transition-colors border border-transparent hover:border-white/[0.02]">
              <XCircle className="text-red-500 shrink-0" size={24} />
              <span>Casual chat or brainstorming</span>
            </li>
            <li className="flex gap-6 items-center p-4 rounded-lg hover:bg-white/[0.02] transition-colors border border-transparent hover:border-white/[0.02]">
              <XCircle className="text-red-500 shrink-0" size={24} />
              <span>Fast answers without verification</span>
            </li>
          </ul>
        </div>
      </section>

      {/* PAUSE -> TRUST: SECURITY */}
      <section className="py-20 bg-[#0E131A] border-t border-white/[0.02] reveal-hidden">
        <div className="max-w-5xl mx-auto px-8">
          <h2 className="text-3xl font-bold mb-8 text-white">Built to run without leaking your data</h2>
          <p className="text-gray-300 max-w-[65ch] text-lg leading-relaxed font-medium">
            Your data never leaves your system. No model training. No data retention.
            Designed for secure environments where privacy is mandatory.
          </p>
        </div>
      </section>

      {/* FINAL CTA WITH CONVICTION */}
      <footer className="relative py-24 text-center reveal-hidden overflow-hidden">
        {/* Subtle Focus Stage */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-emerald-500/5 blur-[100px] rounded-full pointer-events-none -z-10" />

        <h2 className="text-4xl font-bold mb-10 text-white tracking-tight">Ready to execute?</h2>

        <div className="flex flex-col items-center gap-6">
          <Link
            href="/signup"
            className="group relative inline-flex items-center gap-3 bg-white text-black px-10 py-5 rounded-full font-bold text-lg
              hover:bg-gray-100 transition-all shadow-[0_0_40px_-10px_rgba(255,255,255,0.3)] hover:shadow-[0_0_60px_-10px_rgba(255,255,255,0.5)] hover:-translate-y-1"
          >
            Get Started <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
          </Link>

          <p className="text-sm text-gray-500 font-mono tracking-wide">
            Complete control. No data lock-in.
          </p>
        </div>

        <div className="mt-24 text-[10px] text-gray-700 tracking-[0.2em] font-mono uppercase">
          © 2026 ASPERIC — ALL SYSTEMS NOMINAL
        </div>
      </footer>
    </div>
  );
}

function Step({ icon, title, children }: any) {
  return (
    <div className="group bg-[#121923] border border-white/5 p-8 rounded-xl transition-all duration-300
      hover:-translate-y-1 hover:bg-[#161e2a] hover:border-emerald-500/20 hover:shadow-[0_10px_30px_-10px_rgba(0,0,0,0.5)]">
      <div className="text-emerald-500 mb-6 p-3 bg-emerald-500/5 rounded-lg w-fit group-hover:bg-emerald-500/10 transition-colors">
        {icon}
      </div>
      <h3 className="text-lg font-bold mb-3 text-white group-hover:text-emerald-400 transition-colors">{title}</h3>
      <p className="text-sm text-gray-400 font-medium leading-relaxed group-hover:text-gray-300 transition-colors">{children}</p>
    </div>
  );
}
