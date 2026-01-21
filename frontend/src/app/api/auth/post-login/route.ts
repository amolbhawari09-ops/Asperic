import { NextResponse } from "next/server";
import { createSupabaseServer } from "@/lib/supabase/server";

export async function GET() {
    const supabase = await createSupabaseServer();

    const {
        data: { user },
    } = await supabase.auth.getUser();

    if (!user) {
        return NextResponse.json({ redirectTo: "/login" });
    }

    const { data: profile } = await supabase
        .from("profiles")
        .select("onboarding_completed")
        .eq("id", user.id)
        .single();

    if (!profile?.onboarding_completed) {
        return NextResponse.json({ redirectTo: "/onboarding" });
    }

    return NextResponse.json({ redirectTo: "/chat" });
}
