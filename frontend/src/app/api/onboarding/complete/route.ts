import { NextResponse } from "next/server";
import { createSupabaseServer } from "@/lib/supabase/server";

export async function POST(req: Request) {
    const supabase = await createSupabaseServer();
    const body = await req.json();

    const {
        data: { user },
    } = await supabase.auth.getUser();

    if (!user) {
        return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const { error: updateError } = await supabase
        .from("profiles")
        .update({
            role: body.role,
            primary_use: body.primaryUse,
            environment: body.environment,
            onboarding_completed: true,
        })
        .eq("id", user.id);

    if (updateError) {
        console.error("Onboarding Update Error:", updateError);
        return NextResponse.json({ error: updateError.message }, { status: 500 });
    }

    // Verify the update stuck
    const { data: verifyProfile } = await supabase
        .from("profiles")
        .select("onboarding_completed")
        .eq("id", user.id)
        .single();

    if (!verifyProfile?.onboarding_completed) {
        console.error("Onboarding Update Failed verification");
        return NextResponse.json({ error: "Update failed verification" }, { status: 500 });
    }

    return NextResponse.json({ success: true });
}
