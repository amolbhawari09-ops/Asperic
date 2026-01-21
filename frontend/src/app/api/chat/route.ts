
import { createServerClient, type CookieOptions } from "@supabase/ssr";
import { cookies } from "next/headers";
import { NextResponse } from "next/server";

export async function POST(req: Request) {
    const cookieStore = await cookies();

    // 1. AUTHENTICATE
    const supabase = createServerClient(
        process.env.NEXT_PUBLIC_SUPABASE_URL!,
        process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
        {
            cookies: {
                getAll() {
                    return cookieStore.getAll();
                },
                setAll(cookiesToSet) {
                    try {
                        cookiesToSet.forEach(({ name, value, options }) =>
                            cookieStore.set(name, value, options)
                        );
                    } catch {
                        // The `setAll` method was called from a Server Component.
                        // This can be ignored if you have middleware refreshing
                        // user sessions.
                    }
                },
            },
        }
    );

    const { data: { session } } = await supabase.auth.getSession();
    if (!session) {
        return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    try {
        // ENGINEERING TRUTH: Accept mode from frontend
        const { chat_id, user_query, mode } = await req.json();

        if (!chat_id || !user_query) {
            return NextResponse.json({ error: "Missing required fields" }, { status: 400 });
        }

        // 2. VALIDATE OWNERSHIP (RLS CHECK)
        const { data: chat, error: chatError } = await supabase
            .from("chats")
            .select("id")
            .eq("id", chat_id)
            .eq("user_id", session.user.id)
            .single();

        if (chatError || !chat) {
            return NextResponse.json({ error: "Chat not found or access denied" }, { status: 403 });
        }

        // 3. FETCH CONTEXT
        const { data: messages } = await supabase
            .from("messages")
            .select("role, content")
            .eq("chat_id", chat_id)
            .order("created_at", { ascending: true });

        const history = messages?.map((msg: any) => ({
            role: msg.role,
            content: msg.content
        })) || [];

        // Add System Prompt
        const context = [
            { role: "system", content: "You are Asperic, a precise and authoritative AI assistant. You strictly refuse to answer if you lack data. You optimize for correctness over fluency." },
            ...history
        ];

        // 4. CALL PYTHON BACKEND (Hard Dependency)
        // ENGINEERING TRUTH: Forward mode (GENERAL, RESEARCH, CODE) from frontend
        const pythonResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/ask`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                user_query: user_query,
                user_id: session.user.id,
                project_id: chat_id, // We use chat_id as project_id for now to map memory
                mode: mode || "GENERAL" // Strict Mode Enforcement
            }),
        });

        if (!pythonResponse.ok) {
            throw new Error(`Core Intelligence System Failure: ${pythonResponse.statusText}`);
        }

        const assistantText = await pythonResponse.text(); // Using text() as backend returns PlainTextResponse

        // 5. PERSIST ASSISTANT MESSAGE
        const { error: insertError } = await supabase
            .from("messages")
            .insert({
                chat_id: chat_id,
                user_id: session.user.id,
                role: "assistant",
                content: assistantText
            });

        if (insertError) {
            throw new Error(`Persistence Failure: ${insertError.message}`);
        }

        // 6. RETURN SUCCESS (No Content to Frontend)
        return NextResponse.json({ success: true });

    } catch (error: any) {
        console.error("API ROUTE ERROR:", error);
        return NextResponse.json({ error: error.message }, { status: 500 });
    }
}
