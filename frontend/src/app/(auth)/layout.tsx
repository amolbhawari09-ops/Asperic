import { redirect } from "next/navigation";
import { createSupabaseServer } from "@/lib/supabase/server";
import AuthTrustPanel from "./AuthTrustPanel";

export default async function AuthLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const supabase = await createSupabaseServer();
    const {
        data: { user },
    } = await supabase.auth.getUser();

    if (user) {
        // Redirect disabled for testing/viewing auth pages
        // redirect("/chat");
    }

    return (
        <div className="min-h-screen grid lg:grid-cols-[1fr_1.2fr] bg-[#080A0E] relative text-gray-200 overflow-hidden">
            {/* Ambient Background Drift */}
            <div className="absolute inset-0 z-0 opacity-[0.08] pointer-events-none bg-gradient-to-br from-indigo-900/40 via-[#0B0F14] to-emerald-900/40 animate-subtle-drift" />

            {/* LEFT SIDE: Trust & Assurance Panel (Animated Client Component) */}
            <div className="relative z-10 hidden lg:block h-full border-r border-white/[0.03]">
                <AuthTrustPanel />
            </div>

            {/* RIGHT SIDE: Auth Unified Form */}
            <div className="flex items-center justify-center bg-[#080A0E] relative z-10 h-full">
                {/* Mobile Background Depth */}
                <div className="absolute inset-0 lg:hidden bg-gradient-to-b from-[#0f131a] to-black -z-10" />
                {children}
            </div>
        </div>
    );
}
