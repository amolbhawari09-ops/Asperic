"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createSupabaseBrowser } from "@/lib/supabase/browser";
import { motion, AnimatePresence } from "framer-motion";
import { Check, AlertCircle, ArrowRight, Loader2 } from "lucide-react";

export default function AuthPage() {
    const router = useRouter();
    const supabase = createSupabaseBrowser();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState<"signin" | "signup" | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);

    // Micro-interaction: Active Validation
    const isEmailValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);

    const handleSignIn = async () => {
        setLoading("signin");
        setError(null);
        setSuccessMessage(null);

        try {
            const { data, error } = await supabase.auth.signInWithPassword({
                email,
                password,
            });
            if (error) throw error;

            // 5. SIGN IN LOGIC (EXISTING USER) - Check Profile
            const { data: profile } = await supabase
                .from("profiles")
                .select("onboarding_completed")
                .eq("id", data.user.id)
                .single();

            if (profile?.onboarding_completed === false) {
                router.replace("/onboarding");
            } else {
                router.replace("/chat");
            }

        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(null);
        }
    };

    const handleSignUp = async () => {
        setLoading("signup");
        setError(null);
        setSuccessMessage(null);

        try {
            // 4. SIGN UP LOGIC (NEW USER)
            const { data, error } = await supabase.auth.signUp({
                email,
                password,
                options: {
                    emailRedirectTo: undefined, // disable verification preference
                }
            });
            if (error) throw error;
            if (!data.user) throw new Error("Signup failed");

            // Explicitly force onboarding state
            await supabase
                .from("profiles")
                .update({ onboarding_completed: false })
                .eq("id", data.user.id);

            router.replace("/onboarding");
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(null);
        }
    };

    return (
        <div className="w-full max-w-[420px] px-8">

            {/* Header Typography */}
            <div className="mb-10 text-center lg:text-left">
                <h1 className="text-3xl font-medium text-white tracking-wide leading-relaxed mb-3">
                    Welcome to Asperic
                </h1>
                <p className="text-[#a1a1aa]/80 text-sm leading-relaxed max-w-[35ch]">
                    Identify yourself to access the workspace.
                </p>
            </div>

            {/* Glass Card */}
            <motion.div
                layout
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4 }}
                className="relative"
            >
                {/* Shake Animation Container */}
                <motion.div
                    animate={error ? { x: [-5, 5, -5, 5, 0] } : {}}
                    transition={{ duration: 0.4 }}
                    className="space-y-6"
                >
                    {/* Input: Email */}
                    <div className="space-y-2 group">
                        <div className="flex items-baseline justify-between">
                            <label className="text-[10px] font-semibold text-zinc-500 uppercase tracking-widest block transition-colors group-focus-within:text-emerald-500">
                                Email
                            </label>
                            <span className="text-[10px] text-zinc-600/60">Work email preferred</span>
                        </div>
                        <div className="relative">
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className="w-full bg-[#0a0c10] border border-[#27272a] rounded-lg px-4 py-3
                                    text-sm text-white placeholder-zinc-800 outline-none transition-all duration-300
                                    focus:border-emerald-500/60 focus:shadow-[0_0_20px_rgba(16,185,129,0.15)] focus:bg-[#0d0f13]"
                                placeholder="name@company.com"
                            />
                            {/* Validation Icon */}
                            {isEmailValid && (
                                <div className="absolute right-3 top-1/2 -translate-y-1/2 text-emerald-500">
                                    <Check size={14} />
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Input: Password */}
                    <div className="space-y-2 group">
                        <div className="flex items-baseline justify-between">
                            <label className="text-[10px] font-semibold text-zinc-500 uppercase tracking-widest block transition-colors group-focus-within:text-emerald-500">
                                Password
                            </label>
                            <span className="text-[10px] text-zinc-600/60">Minimum 8 characters</span>
                        </div>
                        <div className="relative">
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="w-full bg-[#0a0c10] border border-[#27272a] rounded-lg px-4 py-3
                                    text-sm text-white placeholder-zinc-800 outline-none transition-all duration-300
                                    focus:border-emerald-500/60 focus:shadow-[0_0_20px_rgba(16,185,129,0.15)] focus:bg-[#0d0f13]"
                                placeholder="••••••••"
                            />
                        </div>
                    </div>

                    {/* Feedback Messages */}
                    <AnimatePresence mode="wait">
                        {error && (
                            <motion.div
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: "auto" }}
                                exit={{ opacity: 0, height: 0 }}
                                className="flex items-center gap-2 text-xs text-red-400 bg-red-400/10 p-3 rounded-md border border-red-400/20"
                            >
                                <AlertCircle size={14} />
                                {error}
                            </motion.div>
                        )}
                        {successMessage && (
                            <motion.div
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: "auto" }}
                                exit={{ opacity: 0, height: 0 }}
                                className="flex items-center gap-2 text-xs text-emerald-400 bg-emerald-500/10 p-3 rounded-md border border-emerald-500/20"
                            >
                                <Check size={14} />
                                {successMessage}
                            </motion.div>
                        )}
                    </AnimatePresence>

                    {/* Action Buttons */}
                    <div className="space-y-4 pt-2">
                        {/* Primary: Sign In */}
                        <button
                            onClick={handleSignIn}
                            disabled={!!loading}
                            className="w-full group relative overflow-hidden rounded-lg bg-gradient-to-r from-emerald-600 to-emerald-700
                                p-[1px] shadow-[0_0_20px_rgba(16,185,129,0.15)] transition-all duration-200
                                hover:shadow-[0_0_30px_rgba(16,185,129,0.3)] hover:-translate-y-0.5
                                active:translate-y-0.5 active:shadow-[0_0_10px_rgba(16,185,129,0.1)]
                                disabled:opacity-70 disabled:cursor-not-allowed disabled:transform-none"
                        >
                            <div className="relative h-11 bg-[#0a0c10]/0 flex items-center justify-center rounded-[7px] transition-all group-hover:bg-white/[0.03]">
                                {loading === "signin" ? (
                                    <span className="text-sm font-semibold text-white tracking-wide flex items-center gap-2">
                                        <Loader2 className="animate-spin" size={16} />
                                        Verifying...
                                    </span>
                                ) : (
                                    <span className="text-sm font-semibold text-white tracking-wide flex items-center gap-2">
                                        Sign In <ArrowRight size={14} className="opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all" />
                                    </span>
                                )}
                            </div>
                        </button>

                        {/* Secondary: Create Account (Ghost) */}
                        <button
                            onClick={handleSignUp}
                            disabled={!!loading}
                            className="w-full h-11 flex items-center justify-center rounded-lg border border-white/10 bg-transparent
                                text-sm font-medium text-gray-400 hover:text-white hover:border-white/20 hover:bg-white/[0.02]
                                transition-all duration-200"
                        >
                            {loading === "signup" ? (
                                <Loader2 className="animate-spin" size={16} />
                            ) : (
                                "Sign Up"
                            )}
                        </button>
                    </div>

                </motion.div>
            </motion.div>
        </div>
    );
}
