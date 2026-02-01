import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";
import { NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

/* ---------------- TYPES ---------------- */

type ChatRequest = {
  chat_id: string;
  user_query: string;
  thinking?: "practical" | "analytical";
  output?: "simple" | "professional";
};

export async function POST(req: Request) {
  const requestId = crypto.randomUUID();

  try {
    /* ---------------- ENV VALIDATION ---------------- */
    const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL;
    const SUPABASE_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
    const API_URL = process.env.NEXT_PUBLIC_API_URL;

    if (!SUPABASE_URL || !SUPABASE_KEY || !API_URL) {
      console.error("❌ ENV MISSING");
      return NextResponse.json(
        { error: "Server misconfigured" },
        { status: 500 }
      );
    }

    /* ---------------- SUPABASE SSR ---------------- */
    const cookieStore = cookies();

    const supabase = createServerClient(
      SUPABASE_URL,
      SUPABASE_KEY,
      {
        cookies: {
          getAll: () => cookieStore.getAll(),
          setAll: (cookiesToSet) => {
            try {
              cookiesToSet.forEach(({ name, value, options }) => {
                cookieStore.set(name, value, options);
              });
            } catch {
              // no-op (server components)
            }
          },
        },
      }
    );

    /* ---------------- AUTH ---------------- */
    const {
      data: { session },
    } = await supabase.auth.getSession();

    if (!session) {
      return NextResponse.json(
        { error: "Unauthorized" },
        { status: 401 }
      );
    }

    /* ---------------- BODY ---------------- */
    let body: ChatRequest;
    try {
      body = await req.json();
    } catch {
      return NextResponse.json(
        { error: "Invalid JSON body" },
        { status: 422 }
      );
    }

    const {
      chat_id,
      user_query,
      thinking = "practical",
      output = "simple",
    } = body;

    if (!chat_id || !user_query) {
      return NextResponse.json(
        { error: "chat_id and user_query required" },
        { status: 400 }
      );
    }

    /* ---------------- CHAT OWNERSHIP ---------------- */
    const { data: chat, error: chatError } = await supabase
      .from("chats")
      .select("id")
      .eq("id", chat_id)
      .eq("user_id", session.user.id)
      .single();

    if (chatError || !chat) {
      return NextResponse.json(
        { error: "Chat not found or forbidden" },
        { status: 403 }
      );
    }

    /* ---------------- CONTEXT ---------------- */
    const { data: messages } = await supabase
      .from("messages")
      .select("role, content")
      .eq("chat_id", chat_id)
      .order("created_at", { ascending: true });

    /* ---------------- BACKEND CALL ---------------- */
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 25_000);

    const backendRes = await fetch(`${API_URL}/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      signal: controller.signal,
      body: JSON.stringify({
        user_query,
        user_id: session.user.id,
        project_id: chat_id,
        thinking,
        output,
        history: messages ?? [],
      }),
    });

    clearTimeout(timeout);

    if (!backendRes.ok) {
      const errorText = await backendRes.text();
      console.error("❌ BACKEND FAIL", {
        requestId,
        status: backendRes.status,
        errorText,
      });

      return NextResponse.json(
        { error: "AI backend failure" },
        { status: 502 }
      );
    }

    const assistantText = await backendRes.text();

    /* ---------------- SAVE ASSISTANT ---------------- */
    const { error: insertError } = await supabase
      .from("messages")
      .insert({
        chat_id,
        user_id: session.user.id,
        role: "assistant",
        content: assistantText,
      });

    if (insertError) {
      console.error("❌ DB INSERT FAIL", insertError);
      return NextResponse.json(
        { error: "Failed to save message" },
        { status: 500 }
      );
    }

    return NextResponse.json(
      { success: true, requestId },
      { status: 200 }
    );

  } catch (err) {
    console.error("🔥 API ROUTE CRASH", err);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}