"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { createSupabaseBrowser } from "@/lib/supabase/browser";
import {
    Plus,
    MessageSquare,
    Database,
    Settings,
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

    /* -------- AUTO TITLE LOGIC -------- */

    const generateChatTitle = (text: string) => {
        return text
            .replace(/\s+/g, " ")
            .trim()
            .slice(0, 60);
    };

    const maybeUpdateChatTitle = async (chatId: string, content: string) => {
        const chat = chats.find(c => c.id === chatId);
        if (!chat) return;
        if (chat.title !== "New Session") return;

        const newTitle = generateChatTitle(content);

        const { error } = await supabase
            .from("chats")
            .update({ title: newTitle })
            .eq("id", chatId);

        if (!error) {
            setChats(prev =>
                prev.map(c =>
                    c.id === chatId ? { ...c, title: newTitle } : c
                )
            );
        }
    };

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

            await maybeUpdateChatTitle(activeChatId, content);

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
        <div className="flex h-screen bg-black text-gray-200">
            {/* SIDEBAR */}
            <aside className="w-64 border-r border-white/10 p-3">
                <button
                    onClick={() => createNewSession()}
                    className="w-full flex items-center justify-center gap-2 bg-white text-black py-2 rounded"
                >
                    <Plus size={16} /> New Task
                </button>

                <div className="mt-4 space-y-1">
                    {chats.map(chat => (
                        <button
                            key={chat.id}
                            onClick={() => setActiveChatId(chat.id)}
                            className={`w-full text-left px-3 py-2 rounded text-sm ${
                                activeChatId === chat.id
                                    ? "bg-white/10"
                                    : "hover:bg-white/5"
                            }`}
                        >
                            <MessageSquare size={14} className="inline mr-2" />
                            {chat.title}
                        </button>
                    ))}
                </div>

                <div className="mt-auto pt-4">
                    <button className="flex items-center gap-2 text-sm opacity-70">
                        <Database size={14} /> Knowledge Base
                    </button>
                    <button className="flex items-center gap-2 text-sm opacity-70 mt-2">
                        <Settings size={14} /> Settings
                    </button>
                </div>
            </aside>

            {/* MAIN */}
            <main className="flex-1 flex flex-col">
                <header className="h-14 border-b border-white/10 flex items-center px-6">
                    <span className="text-sm tracking-wide">
                        SESSION / {activeChat.title}
                    </span>
                </header>

                <div className="flex-1 overflow-y-auto p-6 space-y-4">
                    {messages.map(msg => (
                        <div
                            key={msg.id}
                            className={
                                msg.role === "user"
                                    ? "text-right"
                                    : "text-left"
                            }
                        >
                            <div className="inline-block max-w-xl px-4 py-2 rounded bg-white/10">
                                {msg.content}
                            </div>
                        </div>
                    ))}
                    <div ref={bottomRef} />
                </div>

                <footer className="p-4 border-t border-white/10 flex gap-2">
                    <input
                        value={input}
                        onChange={e => setInput(e.target.value)}
                        onKeyDown={e => e.key === "Enter" && sendMessage()}
                        placeholder="Type your message..."
                        className="flex-1 bg-white/5 px-4 py-2 rounded outline-none"
                    />
                    <button
                        onClick={sendMessage}
                        disabled={sending}
                        className="bg-white text-black px-4 rounded"
                    >
                        Send
                    </button>
                </footer>
            </main>
        </div>
    );
}