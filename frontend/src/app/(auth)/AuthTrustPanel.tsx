"use client";

import { motion, Variants } from "framer-motion";
import { Check, Shield, Briefcase } from "lucide-react";

export default function AuthTrustPanel() {
    const variants: Variants = {
        hidden: { opacity: 0, x: -20 },
        visible: (i: number) => ({
            opacity: 1,
            x: 0,
            transition: {
                delay: 0.3 + (i * 0.15),
                duration: 0.5,
                ease: "easeOut"
            }
        })
    };

    return (
        <div className="hidden lg:flex flex-col justify-between p-16 bg-gradient-to-br from-[#0F141C] to-[#0B0F14] relative overflow-hidden h-full">

            {/* Soft Vertical Gradient Divider (Absolute) */}
            <div className="absolute right-0 top-0 bottom-0 w-[1px] bg-gradient-to-b from-transparent via-white/05 to-transparent" />

            {/* Asperic Mark */}
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.8 }}
                className="flex items-center gap-3"
            >
                <img src="/asperic-logo.png" alt="Asperic" className="w-8 h-8 opacity-90" />
                <span className="font-bold tracking-[0.2em] text-sm text-gray-300">ASPERIC</span>
            </motion.div>

            {/* Assurance Content */}
            <div className="max-w-md">
                <motion.h1
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, ease: "easeOut" }}
                    className="text-4xl font-bold text-white mb-12 tracking-tight leading-tight"
                >
                    Built for decisions that matter.
                </motion.h1>

                <div className="space-y-8">
                    {[
                        {
                            icon: <Shield size={18} />,
                            title: "Private & Secure",
                            desc: "Your data is never used to train models. It stays yours."
                        },
                        {
                            icon: <Check size={18} />,
                            title: "Verifiable Accuracy",
                            desc: "Answers are verified against your source data — or refused."
                        },
                        {
                            icon: <Briefcase size={18} />,
                            title: "Professional Grade",
                            desc: "Designed for serious work, engineering, and compliance."
                        }
                    ].map((item, i) => (
                        <motion.div
                            key={i}
                            custom={i}
                            initial="hidden"
                            animate="visible"
                            variants={variants}
                            className="group flex gap-4 items-start p-4 -mx-4 rounded-xl transition-all duration-300 hover:bg-white/[0.02] hover:translate-x-1 cursor-default"
                        >
                            <div className="p-2 rounded-full bg-emerald-500/10 text-emerald-500 mt-1 shrink-0 group-hover:bg-emerald-500/20 transition-colors">
                                {item.icon}
                            </div>
                            <div>
                                <h3 className="text-white font-medium mb-1 group-hover:text-emerald-400 transition-colors">{item.title}</h3>
                                <p className="text-gray-400 text-sm leading-relaxed">{item.desc}</p>
                            </div>
                        </motion.div>
                    ))}
                </div>
            </div>

            {/* Minimal Footer */}
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 1, duration: 0.8 }}
                className="text-[10px] text-gray-600 font-mono tracking-widest uppercase"
            >
                © 2026 ASPERIC SYSTEMS
            </motion.div>
        </div>
    );
}
