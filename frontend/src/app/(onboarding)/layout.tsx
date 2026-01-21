import { redirect } from "next/navigation";
import { createSupabaseServer } from "@/lib/supabase/server";

export default async function OnboardingLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const supabase = await createSupabaseServer();

    const {
        data: { user },
    } = await supabase.auth.getUser();

    if (!user) {
        redirect("/login");
    }

    const { data: profile } = await supabase
        .from("profiles")
        .select("onboarding_completed")
        .eq("id", user.id)
        .single();

    if (profile?.onboarding_completed) {
        redirect("/chat");
    }

    return (
        <div className="onboarding-bg min-h-screen w-full flex flex-col items-center justify-center relative overscroll-none">
            <div className="absolute inset-0 pointer-events-none bg-[radial-gradient(circle_at_center,transparent_10%,rgba(0,0,0,0.8)_120%)] z-0" />
            <div className="relative z-10 w-full flex justify-center">
                {children}
            </div>
        </div>
    );
}
