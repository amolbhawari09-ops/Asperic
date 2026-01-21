import { redirect } from "next/navigation";
import { createSupabaseServer } from "@/lib/supabase/server";

export default async function AppLayout({
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

    if (!profile?.onboarding_completed) {
        redirect("/onboarding");
    }

    return (
        <div className="min-h-screen flex">
            {/* Sidebar / Header later */}
            <main className="flex-1">{children}</main>
        </div>
    );
}
