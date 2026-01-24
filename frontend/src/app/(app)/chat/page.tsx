"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { createSupabaseBrowser } from "@/lib/supabase/browser";
import {
    Plus,
    MessageSquare,
    Database,
    Settings,
    Menu, // Added
    X,    // Added
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

    // 🔹 MOBILE SIDEBAR STATE (New)
    const [sidebarOpen, setSidebarOpen] = useState(false);

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
        const { data, error } = await supabase
            .from("chats")
            .select("*")
            .eq("user_id", userId)
            .order("created_at", { ascending: false });

        if (error) {
            console.error(error);
            return;
        }

        setChats(data || []);

        if (data && data.length > 0) {
            setActiveChatId(data[0].id);
        } else {
            createNewSession(userId);
        }

        setLoading(false);
    };

    /* ---------- CREATE SESSION ---------- */

    const createNewSession = async (forceUserId?: string) => {
        const uid = forceUserId || user?.id;
        if (!uid) return;

        const { data, error } = await supabase
            .from("chats")
            .insert({
                user_id: uid,
                title: "New Session",
            })
            .select()
            .single();

        if (error) {
            console.error(error);
            return;
        }

        setChats(prev => [data, ...prev]);
        setActiveChatId(data.id);
        setMessages([]);
        
        // Close sidebar on mobile when creating new chat
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

            const { data } = await supabase
                .from("messages")
                .select("*")
                .eq("chat_id", activeChatId)
                .order("created_at", { ascending: true });

            setMessages(data || []);

            await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    chat_id: activeChatId,
                    user_query: content,
                    mode: "GENERAL",
                }),
            });

            const { data: final } = await supabase
                .from("messages")
                .select("*")
                .eq("chat_id", activeChatId)
                .order("created_at", { ascending: true });

            setMessages(final || []);
        } catch (err) {
            console.error(err);
            alert("Failed to send message");
            setInput(content);
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
            
            {/* 1. MOBILE OVERLAY (Closes sidebar when clicking outside) */}
            {sidebarOpen && (
                <div 
                    className="fixed inset-0 bg-black/60 z-30 md:hidden backdrop-blur-sm"
                    onClick={() => setSidebarOpen(false)}
                />
            )}

            {/* 2. SIDEBAR (Responsive) */}
            <aside
                className={`
                    fixed inset-y-0 left-0 z-40 w-72 bg-black border-r border-white/10 p-4
                    transform transition-transform duration-300 ease-in-out
                    ${sidebarOpen ? "translate-x-0" : "-translate-x-full"}
                    md:relative md:translate-x-0 md:w-64 md:block
                `}
            >
                <div className="flex items-center justify-between mb-4 md:hidden">
                    <span className="font-bold text-lg">Asperic</span>
                    <button onClick={() => setSidebarOpen(false)}>
                        <X size={20} className="text-gray-400" />
                    </button>
                </div>

                <button
                    onClick={() => createNewSession()}
                    className="w-full flex items-center justify-center gap-2 bg-white text-black py-2 rounded font-medium hover:bg-gray-200 transition"
                >
                    <Plus size={16} /> New Task
                </button>

                <div className="mt-6 space-y-1 overflow-y-auto max-h-[calc(100vh-200px)]">
                    <div className="text-xs font-mono text-gray-500 mb-2 uppercase tracking-wider">Sessions</div>
                    {chats.map(chat => (
                        <button
                            key={chat.id}
                            onClick={() => {
                                setActiveChatId(chat.id);
                                setSidebarOpen(false); // Close sidebar on mobile selection
                            }}
                            className={`w-full text-left px-3 py-3 rounded text-sm transition-colors flex items-center gap-2 ${
                                activeChatId === chat.id
                                    ? "bg-white/10 text-white"
                                    : "text-gray-400 hover:bg-white/5 hover:text-gray-200"
                            }`}
                        >
                            <MessageSquare size={14} />
                            <span className="truncate">{chat.title || "Untitled Session"}</span>
                        </button>
                    ))}
                </div>

                <div className="absolute bottom-4 left-4 right-4">
                    <button className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition w-full p-2 hover:bg-white/5 rounded">
                        <Database size={14} /> Knowledge Base
                    </button>
                    <button className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition w-full p-2 hover:bg-white/5 rounded mt-1">
                        <Settings size={14} /> Settings
                    </button>
                </div>
            </aside>

            {/* 3. MAIN CONTENT (Full width on mobile) */}
            <main className="flex-1 flex flex-col h-full w-full relative">
                
                {/* HEADER */}
                <header className="h-14 border-b border-white/10 flex items-center px-4 gap-3 bg-black sticky top-0 z-10">
                    <button 
                        className="md:hidden p-2 -ml-2 text-gray-400 hover:text-white"
                        onClick={() => setSidebarOpen(true)}
                    >
                        <Menu size={24} />
                    </button>

                    <span className="text-sm font-mono tracking-wide text-gray-400 truncate">
                        SESSION / <span className="text-gray-200">{activeChat.title}</span>
                    </span>
                </header>

                {/* MESSAGES */}
                <div className="flex-1 overflow-y-auto p-4 space-y-6">
                    {messages.length === 0 && (
                        <div className="h-full flex flex-col items-center justify-center text-gray-500 gap-2">
                            <p>System Ready.</p>
                        </div>
                    )}
                    
                    {messages.map(msg => (
                        <div
                            key={msg.id}
                            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                        >
                            <div 
                                className={`
                                    max-w-[85%] px-4 py-3 rounded-lg text-sm leading-relaxed
                                    ${msg.role === "user" 
                                        ? "bg-white text-black" 
                                        : "bg-white/10 text-gray-200 border border-white/5"
                                    }
                                `}
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
                            placeholder="Type your instruction..."
                            className="flex-1 bg-white/5 border border-white/10 px-4 py-3 rounded-lg outline-none focus:border-white/30 text-sm transition-colors"
                        />
                        <button
                            onClick={sendMessage}
                            disabled={sending}
                            className="bg-white/10 hover:bg-white/20 text-white px-4 rounded-lg transition-colors disabled:opacity-50"
                        >
                            {sending ? "..." : <Plus className="rotate-90" size={20} />}
                        </button>
                    </div>
                </footer>
            </main>
        </div>
    );
}
