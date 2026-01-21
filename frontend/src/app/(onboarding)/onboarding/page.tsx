"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createSupabaseBrowser } from "@/lib/supabase/browser";
import { motion, AnimatePresence } from "framer-motion";

type Role = "founder" | "professional";
type PrimaryUse = "strategy" | "technical";
type Environment = "production" | "learning";

export default function OnboardingPage() {
    const router = useRouter();
    const supabase = createSupabaseBrowser();
    const [step, setStep] = useState(1);
    const [isSubmitting, setIsSubmitting] = useState(false);

    const [role, setRole] = useState<Role | null>(null);
    const [primaryUse, setPrimaryUse] = useState<PrimaryUse | null>(null);
    const [environment, setEnvironment] = useState<Environment | null>(null);

    async function completeOnboarding(finalEnv: Environment) {
        if (isSubmitting) return;
        setIsSubmitting(true);
        try {
            const { data: { user } } = await supabase.auth.getUser();
            if (!user) throw new Error("No user found");

            const { error } = await supabase
                .from("profiles")
                .update({
                    role: role,
                    primary_use: primaryUse,
                    environment: finalEnv,
                    onboarding_completed: true
                })
                .eq("id", user.id);

            if (error) throw error;

            router.replace("/chat");
        } catch (e) {
            setIsSubmitting(false);
            alert("Error completing onboarding");
            console.error(e);
        }
    }

    async function handleSignOut() {
        await supabase.auth.signOut();
        router.push("/login");
    }

    const OptionButton = ({
        selected,
        onClick,
        children
    }: {
        selected: boolean;
        onClick: () => void;
        children: React.ReactNode
    }) => (
        <motion.button
            whileHover={{ scale: 1.02, y: -2 }}
            whileTap={{ scale: 0.98 }}
            onClick={onClick}
            className={`w-full p-5 text-left rounded-xl border transition-all duration-300 group relative overflow-hidden ${selected
                ? "border-emerald-500/50 bg-emerald-500/10 shadow-[0_0_20px_rgba(16,185,129,0.15)] ring-1 ring-emerald-500/20"
                : "border-white/5 bg-white/5 hover:bg-white/10 hover:border-white/20 hover:shadow-lg"
                }`}
        >
            <div className={`relative z-10 text-[15px] font-medium transition-colors duration-200 ${selected ? "text-emerald-100" : "text-zinc-400 group-hover:text-zinc-100"
                }`}>
                {children}
            </div>
        </motion.button>
    );

    return (
        <div className="w-full max-w-md space-y-8 p-8 border border-white/5 border-t-white/10 rounded-2xl bg-black/20 backdrop-blur-xl shadow-[0_20px_60px_-15px_rgba(0,0,0,0.5)] shadow-[inset_0_1px_0_0_rgba(255,255,255,0.1)] animate-in fade-in zoom-in duration-500 relative">

            <div className="flex justify-between items-center px-1">
                <span className="text-[10px] uppercase tracking-[0.2em] text-zinc-500 font-medium">Step {step} of 3</span>
            </div>

            <AnimatePresence mode="wait">
                {/* STEP 1 */}
                {step === 1 && (
                    <motion.div
                        key="step1"
                        initial={{ opacity: 0, y: 12 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -12 }}
                        transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
                        className="flex flex-col gap-4"
                    >
                        <h1 className="text-2xl font-semibold tracking-tight text-white">
                            What best describes your <span className="text-emerald-400/90 drop-shadow-sm">role</span>?
                        </h1>
                        <OptionButton selected={role === "founder"} onClick={() => { setRole("founder"); setStep(2); }}>
                            Founder / Executive
                        </OptionButton>
                        <OptionButton selected={role === "professional"} onClick={() => { setRole("professional"); setStep(2); }}>
                            Professional / Specialist
                        </OptionButton>
                    </motion.div>
                )}

                {/* STEP 2 */}
                {step === 2 && (
                    <motion.div
                        key="step2"
                        initial={{ opacity: 0, y: 12 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -12 }}
                        transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
                        className="flex flex-col gap-4"
                    >
                        <h1 className="text-2xl font-semibold tracking-tight text-white">
                            What will you primarily <span className="text-blue-400/90 drop-shadow-sm">use</span> Asperic for?
                        </h1>
                        <OptionButton selected={primaryUse === "strategy"} onClick={() => { setPrimaryUse("strategy"); setStep(3); }}>
                            Strategic decisions & analysis
                        </OptionButton>
                        <OptionButton selected={primaryUse === "technical"} onClick={() => { setPrimaryUse("technical"); setStep(3); }}>
                            Technical execution (code, systems, data)
                        </OptionButton>
                    </motion.div>
                )}

                {/* STEP 3 */}
                {step === 3 && (
                    <motion.div
                        key="step3"
                        initial={{ opacity: 0, y: 12 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -12 }}
                        transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
                        className="flex flex-col gap-4"
                    >
                        <h1 className="text-2xl font-semibold tracking-tight text-white">
                            Where will you use Asperic <span className="text-purple-400/90 drop-shadow-sm">most</span>?
                        </h1>
                        <OptionButton selected={environment === "production"} onClick={() => { setEnvironment("production"); completeOnboarding("production"); }}>
                            Production / Work-critical
                        </OptionButton>
                        <OptionButton selected={environment === "learning"} onClick={() => { setEnvironment("learning"); completeOnboarding("learning"); }}>
                            Learning / Exploration
                        </OptionButton>
                    </motion.div>
                )}
            </AnimatePresence>

            <div className="pt-8 border-t border-white/5 text-center">
                <button
                    onClick={handleSignOut}
                    className="text-[10px] text-zinc-600 hover:text-red-400 uppercase tracking-widest font-mono transition-colors"
                >
                    Sign Out / Reset
                </button>
            </div>
        </div>
    );
}
