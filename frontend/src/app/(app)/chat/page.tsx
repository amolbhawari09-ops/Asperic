"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { createSupabaseBrowser } from "@/lib/supabase/browser";
import { Plus } from "lucide-react";

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

  const [thinkingMode, setThinkingMode] =
    useState<"practical" | "analytical">("practical");
  const [outputMode, setOutputMode] =
    useState<"simple" | "professional">("simple");

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

  /* ------------ FETCH CHATS (FIXED) ------------ */

  const fetchChats = async (userId: string) => {
    const { data } = await supabase
      .from("chats")
      .select("*")
      .eq("user_id", userId)
      .order("created_at", { ascending: false });

    setChats(data || []);
    
    // ✅ FIX: Restore last active session from localStorage
    const savedChatId = localStorage.getItem("activeChatId");
    
    if (data && data.length > 0) {
      // Check if saved chat still exists
      if (savedChatId && data.find(c => c.id === savedChatId)) {
        setActiveChatId(savedChatId);
      } else {
        setActiveChatId(data[0].id);
        localStorage.setItem("activeChatId", data[0].id);
      }
    } else {
      // ✅ Only create new session if NO chats exist
      createNewSession(userId);
    }

    setLoading(false);
  };

  /* ---------- CREATE SESSION (FIXED) ---------- */

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
    
    // ✅ FIX: Save to localStorage
    localStorage.setItem("activeChatId", data.id);
    
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
    
    // ✅ FIX: Save active chat when it changes
    localStorage.setItem("activeChatId", activeChatId);
    
  }, [activeChatId]);

  /* ------------ SEND MESSAGE (FIXED) ------------ */

  const sendMessage = async () => {
    if (!input.trim() || !activeChatId || !user || sending) return;

    const userText = input.trim();
    setInput("");
    setSending(true);

    try {
      // 1️⃣ Save user message
      const { data: userMsg } = await supabase
        .from("messages")
        .insert({
          chat_id: activeChatId,
          user_id: user.id,
          role: "user",
          content: userText,
        })
        .select()
        .single();

      // ✅ Immediately show user message
      setMessages(prev => [...prev, userMsg]);

      // 2️⃣ Call backend
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          chat_id: activeChatId,
          user_query: userText,
          thinking: thinkingMode,
          output: outputMode,
        }),
      });

      // ✅ FIX: Handle both JSON object and JSON string
      let data;
      const contentType = res.headers.get("content-type");
      
      if (contentType && contentType.includes("application/json")) {
        data = await res.json();
      } else {
        const text = await res.text();
        try {
          data = JSON.parse(text);
        } catch {
          data = { answer: text };
        }
      }

      console.log("📦 API Response:", data); // Debug log

      // ✅ FIXED: Extract answer properly
      let assistantText;
      
      if (typeof data === "string") {
        // If entire response is a string, try to parse it
        try {
          const parsed = JSON.parse(data);
          assistantText = parsed.answer || data;
        } catch {
          assistantText = data;
        }
      } else if (data && typeof data === "object") {
        assistantText = data.answer || JSON.stringify(data);
      } else {
        assistantText = "⚠️ No response generated.";
      }

      // 3️⃣ Save assistant message (TEXT ONLY)
      const { data: assistantMsg } = await supabase
        .from("messages")
        .insert({
          chat_id: activeChatId,
          role: "assistant",
          content: assistantText,
        })
        .select()
        .single();

      // ✅ Immediately show assistant message
      setMessages(prev => [...prev, assistantMsg]);

    } catch (err) {
      console.error("❌ Send message failed:", err);
      
      // ✅ Show error message to user
      setMessages(prev => [
        ...prev,
        {
          id: Date.now().toString(),
          role: "assistant",
          content: "⚠️ Error: Could not get response. Please try again.",
          created_at: new Date().toISOString(),
        } as Message,
      ]);
    } finally {
      setSending(false);
    }
  };

  /* ------------ AUTO SCROLL ------------ */

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  /* ------------ SWITCH CHAT (NEW) ------------ */
  
  const switchChat = (chatId: string) => {
    setActiveChatId(chatId);
    localStorage.setItem("activeChatId", chatId);
  };

  const activeChat =
    chats.find(c => c.id === activeChatId) ||
    ({ title: "New Session" } as Chat);

  /* ---------------- UI ---------------- */

  return (
    <div className="flex h-screen bg-black text-gray-200">

      <main className="flex-1 flex flex-col">

        {/* HEADER */}
        <header className="h-14 border-b border-white/10 flex items-center px-4 gap-4">
          <span className="text-sm font-mono text-gray-400 truncate">
            SESSION / <span className="text-gray-200">{activeChat.title}</span>
          </span>

          <div className="ml-auto flex gap-1 bg-white/5 border border-white/10 rounded-lg p-1">
            {["practical", "analytical"].map(v => (
              <button
                key={v}
                onClick={() => setThinkingMode(v as any)}
                className={`px-3 py-1 text-xs rounded-md ${
                  thinkingMode === v
                    ? "bg-white text-black"
                    : "text-gray-400"
                }`}
              >
                {v}
              </button>
            ))}
          </div>

          <div className="flex gap-1 bg-white/5 border border-white/10 rounded-lg p-1">
            {["simple", "professional"].map(v => (
              <button
                key={v}
                onClick={() => setOutputMode(v as any)}
                className={`px-3 py-1 text-xs rounded-md ${
                  outputMode === v
                    ? "bg-white text-black"
                    : "text-gray-400"
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
              className={`flex ${
                msg.role === "user" ? "justify-end" : "justify-start"
              }`}
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
          {sending && (
            <div className="flex justify-start">
              <div className="bg-white/10 border border-white/5 px-4 py-3 rounded-lg text-sm">
                <span className="animate-pulse">Thinking...</span>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* INPUT */}
        <footer className="p-4 border-t border-white/10">
          <div className="flex gap-2 max-w-4xl mx-auto">
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === "Enter" && !sending && sendMessage()}
              placeholder="Type your instruction…"
              disabled={sending}
              className="flex-1 bg-white/5 border border-white/10 px-4 py-3 rounded-lg outline-none disabled:opacity-50"
            />
            <button
              onClick={sendMessage}
              disabled={sending}
              className="bg-white/10 hover:bg-white/20 px-4 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Plus className="rotate-90" size={20} />
            </button>
          </div>
        </footer>

      </main>
    </div>
  );
}