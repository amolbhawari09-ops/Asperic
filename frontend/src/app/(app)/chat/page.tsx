"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { createSupabaseBrowser } from "@/lib/supabase/browser";
import {
    Plus,
    MessageSquare,
    Database,
    Settings,
    Menu,
    X,
    Check,
} from "lucide-react";

/* ---------------- TYPES ---------------- */

type Chat = {
    id: string;
    title: string;
    created_at: string;
};

type Message = {
    id: string;
    role: "user" | "assistant" | "system";
    content: string;
    created_at: string;
};

/* -------------- COMPONENT -------------- */

export default function ChatPage() {
    const router = useRouter();
    const supabase = createSupabaseBrowser();
    const bottomRef = useRef<HTMLDivElement>(null);

    /* ---------------- STATE ---------------- */

    const [user, setUser] = useState<any>(null);
    const [chats, setChats] = useState<Chat[]>([]);
    const [activeChatId, setActiveChatId] = useState<string | null>(null);
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(true);
    const [sending, setSending] = useState(false);

    // 🔹 MOBILE SIDEBAR
    const [sidebarOpen, setSidebarOpen] = useState(false);

    // 🔹 NEW TOGGLES
    const [thinkingMode, setThinkingMode] = useState<"practical" | "analytical">("practical");
    const [outputMode, setOutputMode] = useState<"simple" | "professional">("simple");

    /* ------------ AUTH CHECK ------------ */

    useEffect(() => {
        const init = async () => {
            const { data } = await supabase.auth.getSession();
            if (!data.session) {
                router.replace("/login");
                return;
            }
            setUser(data.session.user);
            fetchChats(data.session.user.id);
        };
        init();
    }, []);

    /* ------------ FETCH CHATS ------------ */

    const fetchChats = async (userId: string) => {
        const { data } = await supabase
            .from("chats")
            .select("*")
            .eq("user_id", userId)
            .order("created_at", { ascending: false });

        setChats(data || []);
        if (data && data.length > 0) setActiveChatId(data[0].id);
        else createNewSession(userId);

        setLoading(false);
    };

    /* ---------- CREATE SESSION ---------- */

    const createNewSession = async (forceUserId?: string) => {
        const uid = forceUserId || user?.id;
        if (!uid) return;

        const { data } = await supabase
            .from("chats")
            .insert({ user_id: uid, title: "New Session" })
            .select()
            .single();

        setChats(prev => [data, ...prev]);
        setActiveChatId(data.id);
        setMessages([]);
        setSidebarOpen(false);
    };

    /* ---------- FETCH MESSAGES ---------- */

    useEffect(() => {
        if (!activeChatId) return;

        const loadMessages = async () => {
            const { data } = await supabase
                .from("messages")
                .select("*")
                .eq("chat_id", activeChatId)
                .order("created_at", { ascending: true });

            setMessages(data || []);
        };

        loadMessages();
    }, [activeChatId]);

    /* ------------ SEND MESSAGE ------------ */

    const sendMessage = async () => {
        if (!input.trim() || !activeChatId || !user) return;

        const content = input;
        setInput("");
        setSending(true);

        try {
            await supabase.from("messages").insert({
                chat_id: activeChatId,
                user_id: user.id,
                role: "user",
                content,
            });

            await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    chat_id: activeChatId,
                    user_query: content,
                    thinking: thinkingMode,
                    output: outputMode,
                }),
            });

        } finally {
            setSending(false);
        }
    };

    /* ------------ SCROLL ------------ */

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const activeChat =
        chats.find(c => c.id === activeChatId) ||
        ({ title: "New Session" } as Chat);

    /* ---------------- UI ---------------- */

    return (
        <div className="flex h-screen bg-black text-gray-200 relative overflow-hidden">

            {/* SIDEBAR OMITTED — UNCHANGED */}

            <main className="flex-1 flex flex-col h-full w-full relative">

                {/* HEADER */}
                <header className="h-14 border-b border-white/10 flex items-center px-4 gap-4 bg-black sticky top-0 z-10">

                    <span className="text-sm font-mono tracking-wide text-gray-400 truncate">
                        SESSION / <span className="text-gray-200">{activeChat.title}</span>
                    </span>

                    {/* 🧠 THINKING TOGGLE (LEFT) */}
                    <div className="ml-auto flex gap-1 bg-white/5 border border-white/10 rounded-lg p-1">
                        {["practical", "analytical"].map(v => (
                            <button
                                key={v}
                                onClick={() => setThinkingMode(v as any)}
                                className={`px-3 py-1 text-xs rounded-md transition ${
                                    thinkingMode === v
                                        ? "bg-white text-black"
                                        : "text-gray-400 hover:text-gray-200"
                                }`}
                            >
                                {v}
                            </button>
                        ))}
                    </div>

                    {/* ✍️ OUTPUT TOGGLE (RIGHT) */}
                    <div className="flex gap-1 bg-white/5 border border-white/10 rounded-lg p-1">
                        {["simple", "professional"].map(v => (
                            <button
                                key={v}
                                onClick={() => setOutputMode(v as any)}
                                className={`px-3 py-1 text-xs rounded-md transition ${
                                    outputMode === v
                                        ? "bg-white text-black"
                                        : "text-gray-400 hover:text-gray-200"
                                }`}
                            >
                                {v}
                            </button>
                        ))}
                    </div>
                </header>

                {/* MESSAGES */}
                <div className="flex-1 overflow-y-auto p-4 space-y-6">
                    {messages.map(msg => (
                        <div
                            key={msg.id}
                            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                        >
                            <div
                                className={`max-w-[85%] px-4 py-3 rounded-lg text-sm ${
                                    msg.role === "user"
                                        ? "bg-white text-black"
                                        : "bg-white/10 border border-white/5"
                                }`}
                            >
                                {msg.content}
                            </div>
                        </div>
                    ))}
                    <div ref={bottomRef} />
                </div>

                {/* INPUT */}
                <footer className="p-4 border-t border-white/10 bg-black">
                    <div className="flex gap-2 max-w-4xl mx-auto">
                        <input
                            value={input}
                            onChange={e => setInput(e.target.value)}
                            onKeyDown={e => e.key === "Enter" && sendMessage()}
                            placeholder="Type your instruction…"
                            className="flex-1 bg-white/5 border border-white/10 px-4 py-3 rounded-lg outline-none"
                        />
                        <button
                            onClick={sendMessage}
                            disabled={sending}
                            className="bg-white/10 hover:bg-white/20 px-4 rounded-lg"
                        >
                            <Plus className="rotate-90" size={20} />
                        </button>
                    </div>
                </footer>
            </main>
        </div>
    );
}