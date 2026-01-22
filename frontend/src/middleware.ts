import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { createServerClient } from "@supabase/ssr";

export async function middleware(req: NextRequest) {
  // Always allow request to continue by default
  let res = NextResponse.next({
    request: {
      headers: req.headers,
    },
  });

  // 🔒 SAFETY GUARD: If env vars are missing, SKIP Supabase logic
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  if (!supabaseUrl || !supabaseAnonKey) {
    // Do NOT crash the site
    console.warn("⚠️ Middleware: Supabase env vars missing. Skipping auth.");
    return res;
  }

  // Create Supabase client ONLY if env vars exist
  const supabase = createServerClient(
    supabaseUrl,
    supabaseAnonKey,
    {
      cookies: {
        getAll() {
          return req.cookies.getAll();
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value }) =>
            req.cookies.set(name, value)
          );

          res = NextResponse.next({
            request: {
              headers: req.headers,
            },
          });

          cookiesToSet.forEach(({ name, value, options }) =>
            res.cookies.set(name, value, options)
          );
        },
      },
    }
  );

  try {
    const {
      data: { user },
    } = await supabase.auth.getUser();

    // Optional logging only (NO blocking)
    if (
      req.nextUrl.pathname.startsWith("/chat") ||
      req.nextUrl.pathname.startsWith("/onboarding")
    ) {
      console.log(
        "🔐 MIDDLEWARE VERIFY_SESSION:",
        user?.id ?? "NO USER"
      );
    }
  } catch (err) {
    // Never crash middleware
    console.error("❌ Middleware auth check failed:", err);
  }

  return res;
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
