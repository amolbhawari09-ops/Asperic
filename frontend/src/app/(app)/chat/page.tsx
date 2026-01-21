"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { createSupabaseBrowser } from "@/lib/supabase/browser";
import {
    Send, Database, LayoutGrid, Settings,
    Terminal, Code2, Globe, Lock,
    Plus, MessageSquare, FolderGit2, Hash,
    MoreHorizontal, Download
} from "lucide-react";

// --- TYPES ---
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

export default function ChatPage() {
    const router = useRouter();
    const supabase = createSupabaseBrowser();
    const bottomRef = useRef<HTMLDivElement>(null);

    // --- STATE ---
    const [user, setUser] = useState<any>(null);
    const [chats, setChats] = useState<Chat[]>([]);
    const [activeChatId, setActiveChatId] = useState<string | null>(null);
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");

    // UI State
    const [loading, setLoading] = useState(true); // Initial load only
    const [sending, setSending] = useState(false);

    // Staged Assistant Feedback State
    type AssistantStage = 'idle' | 'thinking' | 'fetching' | 'responding';
    const [assistantStage, setAssistantStage] = useState<AssistantStage>('idle');

    const [activeMode, setActiveMode] = useState("GENERAL");
    const [showComingSoon, setShowComingSoon] = useState(false);
    const [comingSoonFeature, setComingSoonFeature] = useState("");

    // Knowledge Base Modal State (Engineering Truth)
    const [showMemories, setShowMemories] = useState(false);
    const [memoriesList, setMemoriesList] = useState<any[]>([]);
    const [memoriesLoading, setMemoriesLoading] = useState(false);

    // Fetch Memories from Backend
    const fetchMemories = async () => {
        if (!user) return;
        setMemoriesLoading(true);
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/memories?user_id=${user.id}`);
            const data = await res.json();
            setMemoriesList(data.memories || []);
        } catch (e) {
            console.error("Failed to fetch memories:", e);
            setMemoriesList([]);
        } finally {
            setMemoriesLoading(false);
        }
    };

    // Handler for Knowledge Base button
    const handleKnowledgeBase = () => {
        setShowMemories(true);
        fetchMemories();
    };

    // --- 1. AUTH & INITIAL LOAD ---
    useEffect(() => {
        const checkUser = async () => {
            const { data: { session } } = await supabase.auth.getSession();
            if (!session) {
                router.replace("/login");
                return;
            }
            setUser(session.user);
            fetchChats(session.user.id);
        };
        checkUser();
    }, []);

    // --- 2. FETCH CHATS ---
    const fetchChats = async (userId: string) => {
        try {
            const { data, error } = await supabase
                .from("chats")
                .select("*")
                .eq("user_id", userId)
                .order("created_at", { ascending: false });

            if (error) throw error;

            if (data) {
                setChats(data);
                if (data.length > 0 && !activeChatId) {
                    setActiveChatId(data[0].id);
                } else if (data.length === 0) {
                    // Auto-create first chat if none exists
                    createNewSession(userId);
                }
            }
        } catch (error) {
            console.error("Error fetching chats:", error);
        } finally {
            setLoading(false);
        }
    };

    // --- 3. CREATE SESSION (Session Hygiene) ---
    const createNewSession = async (forceUserId?: string) => {
        const userId = forceUserId || user?.id;
        if (!userId) return;

        // ENGINEERING TRUTH: Session Spam Guard
        // If the most recent session is already empty ("New Session" with no messages), just activate it.
        if (chats.length > 0 && chats[0].title === "New Session" && messages.length === 0) {
            console.log("🛡️ SESSION GUARD: Reusing empty session.");
            setActiveChatId(chats[0].id);
            return;
        }

        try {
            const { data, error } = await supabase
                .from("chats")
                .insert({
                    user_id: userId,
                    title: "New Session"
                })
                .select()
                .single();

            if (error) throw error;

            if (data) {
                setChats([data, ...chats]);
                setActiveChatId(data.id);
                setMessages([]); // Force clear messages for fresh session
            }
        } catch (error) {
            console.error("Error creating session:", error);
        }
    };

    // --- 4. FETCH MESSAGES ---
    useEffect(() => {
        if (!activeChatId) {
            setMessages([]);
            return;
        }

        const fetchMessages = async () => {
            const { data, error } = await supabase
                .from("messages")
                .select("*")
                .eq("chat_id", activeChatId)
                .order("created_at", { ascending: true });

            if (!error && data) {
                setMessages(data);
            }
        };

        fetchMessages();

        // Realtime subscription could go here
    }, [activeChatId]);

    // Scroll to bottom functionality
    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, assistantStage]);

    // --- 5. SEND MESSAGE ---
    const sendMessage = async () => {
        if (!input.trim() || !activeChatId || !user) return;

        const content = input;
        setInput(""); // Optimistic clear
        setSending(true);

        // STAGE 1: THINKING (Immediate Feedback)
        setAssistantStage('thinking');

        try {
            // Insert User Message
            const { error } = await supabase.from("messages").insert({
                chat_id: activeChatId,
                user_id: user.id,
                role: "user",
                content: content
            });

            if (error) throw error;

            // Re-fetch to verify persistence (The "Moment of Truth")
            const { data: updatedMessages } = await supabase
                .from("messages")
                .select("*")
                .eq("chat_id", activeChatId)
                .order("created_at", { ascending: true });

            if (updatedMessages) setMessages(updatedMessages);

            // STAGE 2: FETCHING (API Call)
            setAssistantStage('fetching');

            // ENGINEERING TRUTH: Pass Strict Mode to Backend
            const response = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    chat_id: activeChatId,
                    user_query: content,
                    mode: activeMode // Strict Mode Routing
                })
            });

            if (!response.ok) throw new Error("Assistant unavailable");

            // STAGE 3: RESPONDING (Finalizing)
            setAssistantStage('responding');

            // 7. RE-FETCH (The Assistant has spoken)
            const { data: finalMessages } = await supabase
                .from("messages")
                .select("*")
                .eq("chat_id", activeChatId)
                .order("created_at", { ascending: true });

            if (finalMessages) setMessages(finalMessages);

        } catch (error) {
            console.error("Error sending message:", error);
            alert("Failed to send message. Please try again.");
            setInput(content); // Restore input on error
        } finally {
            setSending(false);
            // RESET TO IDLE
            setAssistantStage('idle');
        }
    };

    const handleComingSoon = (feature: string) => {
        setComingSoonFeature(feature);
        setShowComingSoon(true);
    };

    // Derived State for UI
    const activeChat = chats.find(c => c.id === activeChatId) || { id: "...", title: "Loading...", created_at: "" };

    // --- 6. SMART INPUT BEHAVIOR (Larry Page Upgrade) ---
    const [intentSignal, setIntentSignal] = useState(false);

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const val = e.target.value;
        // Trigger signal only on first keystroke from empty
        if (input.length === 0 && val.length > 0) {
            setIntentSignal(true);
            setTimeout(() => setIntentSignal(false), 1500); // 1.5s to ensure readability (300ms is subliminal, maybe too fast for text reading, but I'll make it fade out)
        }
        setInput(val);
    };

    return (
        <div className="flex h-screen bg-alive text-gray-300 font-sans overflow-hidden relative selection:bg-emerald-500/30">
            {/* AMBIENT LAYERS (Jony Ive Upgrade) */}
            <div className="bg-noise"></div>
            <div className="animate-vignette"></div>

            {/* --- 1. CLEAN SIDEBAR --- */}
            <div className="w-64 bg-[#0d0f13] flex flex-col border-r border-white/5 z-20 backdrop-blur-xl bg-[#0d0f13]/80">

                {/* Brand Header */}
                <div className="h-14 flex items-center px-4 border-b border-white/5 gap-2 group cursor-pointer">
                    <div className="w-5 h-5 bg-gradient-to-br from-emerald-500 via-emerald-600 to-teal-600 rounded-sm shadow-[0_0_10px_rgba(16,185,129,0.3)] group-hover:shadow-[0_0_15px_rgba(16,185,129,0.5)] transition-all"></div>
                    <span className="font-bold tracking-[0.15em] text-gray-100">ASPERIC</span>

                </div>

                {/* Primary Action */}
                <div className="p-3">
                    <button
                        onClick={() => createNewSession()}
                        className="w-full flex items-center justify-center gap-2 bg-white text-black hover:bg-gray-200 transition-colors py-2 rounded font-medium text-sm disabled:opacity-50"
                    >
                        <Plus size={16} /> New Task
                    </button>
                </div>

                {/* Navigation Groups */}
                <div className="flex-1 overflow-y-auto px-3 py-2 space-y-6">
                    {/* GROUP 1: Chats */}
                    <div>
                        <div className="text-[9px] font-extrabold text-gray-600 uppercase tracking-[0.15em] mb-2 px-2 font-mono">Sessions</div>
                        {chats.map(s => (
                            <SessionRow
                                key={s.id}
                                title={s.title}
                                active={activeChatId === s.id}
                                onClick={() => setActiveChatId(s.id)}
                                icon={<MessageSquare size={14} />}
                            />
                        ))}
                        {chats.length === 0 && !loading && (
                            <div className="px-2 text-xs text-gray-600 italic">No sessions yet.</div>
                        )}
                    </div>
                </div>

                {/* System Footer */}
                <div className="p-3 border-t border-white/5 space-y-1">
                    <FooterItem icon={<Database size={14} />} label="Knowledge Base" onClick={handleKnowledgeBase} />
                    <FooterItem icon={<Settings size={14} />} label="Settings" onClick={() => handleComingSoon("Settings")} />
                </div>
            </div>

            {/* --- 2. MAIN INTERFACE --- */}
            <div className="flex-1 flex flex-col min-w-0">

                {/* Top Header (Infrastructure Signals) */}
                <div className="h-14 border-b border-white/5 flex items-center justify-between px-6 bg-[#0a0c10]/80 backdrop-blur-md z-20">
                    <div className="flex items-center gap-2 text-sm">
                        <span className="text-gray-500 font-mono text-xs tracking-wider">SESSION /</span>
                        <span className="text-white font-medium tracking-wide">{activeChat.title}</span>
                    </div>

                    <div className="flex items-center gap-4">
                        {/* SYSTEM STATE BADGES (Jensen Huang Upgrade) */}
                        <div className="flex items-center gap-3">
                            <div className={`flex items-center gap-1.5 px-2 py-1 bg-[#18181b] rounded border transition-colors duration-300 ${assistantStage === 'thinking' ? 'border-emerald-500/50' : 'border-white/5'}`}>
                                <span className={`text-[10px] font-mono uppercase tracking-wider transition-colors ${assistantStage === 'thinking' ? 'text-emerald-400' : 'text-gray-500'}`}>MEM</span>
                                <div className={`w-1.5 h-1.5 rounded-full transition-all duration-300 ${assistantStage === 'thinking' ? 'bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.8)] scale-110' : 'bg-emerald-900/40'}`}></div>
                            </div>
                            <div className={`flex items-center gap-1.5 px-2 py-1 bg-[#18181b] rounded border transition-colors duration-300 ${assistantStage === 'fetching' ? 'border-blue-500/50' : 'border-white/5'}`}>
                                <span className={`text-[10px] font-mono uppercase tracking-wider transition-colors ${assistantStage === 'fetching' ? 'text-blue-400' : 'text-gray-500'}`}>RAG</span>
                                <div className={`w-1.5 h-1.5 rounded-full transition-all duration-300 ${assistantStage === 'fetching' ? 'bg-blue-500 animate-pulse shadow-[0_0_10px_rgba(59,130,246,0.8)]' : 'bg-blue-900/40'}`}></div>
                            </div>
                            <div className={`flex items-center gap-1.5 px-2 py-1 bg-[#18181b] rounded border transition-colors duration-300 ${assistantStage === 'responding' ? 'border-purple-500/50' : 'border-white/5'}`}>
                                <span className={`text-[10px] font-mono uppercase tracking-wider transition-colors ${assistantStage === 'responding' ? 'text-purple-400' : 'text-gray-500'}`}>ENG</span>
                                <div className={`w-1.5 h-1.5 rounded-full transition-all duration-300 ${assistantStage === 'responding' ? 'bg-purple-500 shadow-[0_0_10px_rgba(168,85,247,0.8)]' : 'bg-purple-900/40'}`}></div>
                            </div>
                        </div>

                        <div className="h-4 w-px bg-white/10 mx-2"></div>

                        <div className="flex items-center gap-2 px-3 py-1.5 bg-[#18181b] rounded text-xs font-mono text-gray-400 border border-white/5 group hover:border-white/10 transition-colors cursor-help" title="Session UUID">
                            <Hash size={10} className="text-gray-600 group-hover:text-emerald-500 transition-colors" />
                            <span className="tracking-widest opacity-60 group-hover:opacity-100 transition-opacity">{activeChat.id.slice(0, 8)}</span>
                        </div>
                    </div>
                </div>

                {/* Chat Stream (Transparent to show Ambient BG) */}
                <div className="flex-1 overflow-y-auto p-4 md:p-8 space-y-6 scrollbar-thin scrollbar-thumb-white/10 z-10">
                    {messages.map((msg) => (
                        <div key={msg.id} className={`flex flex-col max-w-3xl mx-auto ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                            <div className={`
                                p-5 rounded-lg text-sm leading-relaxed shadow-sm border
                                ${msg.role === 'user'
                                    ? 'bg-[#18181b]/80 border-white/10 text-gray-100 backdrop-blur-sm'
                                    : 'bg-transparent border-transparent text-white w-full px-0'
                                }
                            `}>
                                {msg.role === 'assistant' && (
                                    <div className="flex items-center gap-2 mb-2 text-emerald-500 font-bold text-xs uppercase tracking-wider">
                                        <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full"></div>
                                        Asperic
                                    </div>
                                )}
                                <div className="whitespace-pre-wrap has-structured-output">
                                    {/* VISUAL ALIGNMENT (Peter Thiel Upgrade) - Styling Headers & Footers */}
                                    {msg.role === 'assistant' ? (
                                        (() => {
                                            const parts = msg.content.split('\n');
                                            const headers = ["PURPOSE", "SUMMARY", "ANALYSIS", "DECISION", "EXECUTION PLAN", "ASSESSMENT"];
                                            const isSystemHeader = headers.includes(parts[0].trim());

                                            if (isSystemHeader) {
                                                const header = parts[0];
                                                const footerIndex = parts.findLastIndex(p => p.trim().startsWith("— "));
                                                const body = parts.slice(1, footerIndex > 0 ? footerIndex : undefined).join('\n');
                                                const footer = footerIndex > 0 ? parts.slice(footerIndex).join('\n') : null;

                                                return (
                                                    <>
                                                        <div className="text-emerald-400 font-bold text-xs tracking-widest mb-3 opacity-90">{header}</div>
                                                        <div className="mb-4 text-gray-200">{body.trim()}</div>
                                                        {footer && <div className="text-[11px] text-gray-500 font-mono opacity-60 border-t border-white/5 pt-2 mt-4">{footer}</div>}
                                                    </>
                                                );
                                            } else {
                                                return <div>{msg.content}</div>;
                                            }
                                        })()
                                    ) : (
                                        <div className="text-gray-100">{msg.content}</div>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}

                    {/* Welcome Message if Empty (Intelligence Signal) */}
                    {messages.length === 0 && !loading && (
                        <div className="text-center mt-24 text-sm animate-in fade-in duration-700">
                            {/* Adjusted Typography: Tighter tracking */}
                            <div className="mb-3 font-mono text-emerald-500 font-bold tracking-[0.1em] text-xs opacity-80">SYSTEM READY</div>

                            {/* Adjusted Typography: Increased Leading */}
                            <div className="text-gray-400 mb-6 flex items-center justify-center gap-2 text-xs font-mono opacity-60 leading-loose">
                                <span>Awaiting instruction</span>
                                <span className="w-1 h-1 bg-gray-600 rounded-full"></span>
                                <span>Memory online</span>
                                <span className="w-1 h-1 bg-gray-600 rounded-full"></span>
                                <span>Reasoning active</span>
                            </div>

                            {/* Micro-Guidance (Professional) */}
                            <div className="flex flex-col gap-2 items-center opacity-40 hover:opacity-100 transition-opacity duration-300">
                                <div className="text-[10px] text-gray-500 font-mono uppercase tracking-widest mb-1">Examples</div>
                                <button className="text-xs text-gray-400 hover:text-emerald-400 transition-colors" onClick={() => { setInput("Summarize my last session"); setIntentSignal(true); setTimeout(() => setIntentSignal(false), 800) }}>
                                    • Summarize my last session
                                </button>
                                <button className="text-xs text-gray-400 hover:text-emerald-400 transition-colors" onClick={() => { setInput("Help me design a system"); setIntentSignal(true); setTimeout(() => setIntentSignal(false), 800) }}>
                                    • Help me design a system
                                </button>
                                <button className="text-xs text-gray-400 hover:text-emerald-400 transition-colors" onClick={() => { setInput("Analyze this problem"); setIntentSignal(true); setTimeout(() => setIntentSignal(false), 800) }}>
                                    • Analyze this problem
                                </button>
                            </div>

                            {/* CAPABILITIES DECLARATION (Peter Thiel Upgrade) */}
                            <div className="mt-8 text-[10px] text-gray-500 font-mono tracking-widest opacity-30 uppercase">
                                Capabilities: Analysis · Decision · Design · Execution
                            </div>
                        </div>
                    )}

                    {/* STAGED FEEDBACK INDICATORS */}
                    {assistantStage !== 'idle' && (
                        <div className="flex flex-col max-w-3xl mx-auto items-start animate-pulse">
                            <div className="flex items-center gap-2 mb-2 text-emerald-500/70 font-bold text-xs uppercase tracking-wider font-mono">
                                <div className="w-1.5 h-1.5 bg-emerald-500/70 rounded-full animate-bounce"></div>
                                {assistantStage === 'thinking' && "Thinking..."}
                                {assistantStage === 'fetching' && "Fetching data..."}
                                {assistantStage === 'responding' && "Finalizing response..."}
                            </div>
                        </div>
                    )}

                    <div ref={bottomRef} />
                </div>

                {/* Input Deck (Glassy) */}
                <div className="p-6 bg-transparent z-20">
                    {/* Intent Signal (Larry Page Upgrade) */}
                    <div className={`
                        max-w-3xl mx-auto mb-2 flex items-center gap-2 text-emerald-500/80 text-[10px] uppercase font-mono tracking-widest transition-opacity duration-500
                        ${intentSignal ? 'opacity-100' : 'opacity-0'}
                    `}>
                        <div className="w-1 h-1 bg-emerald-500 rounded-full animate-pulse"></div>
                        Interpreting intent...
                    </div>

                    <div className={`
                        max-w-3xl mx-auto border rounded-xl bg-[#0f0f11]/80 backdrop-blur-md overflow-hidden transition-all duration-300 shadow-2xl
                        ${intentSignal ? 'border-emerald-500/30 shadow-[0_0_30px_rgba(16,185,129,0.1)]' : 'border-white/10 hover:border-white/20'}
                        focus-within:ring-1 focus-within:ring-white/20
                    `}>
                        {/* Mode Tabs */}
                        <div className="flex items-center gap-1 p-1.5 bg-[#141416]/50 border-b border-white/5">
                            <ModeButton active={activeMode === "GENERAL"} onClick={() => setActiveMode("GENERAL")} icon={<Terminal size={12} />} label="General" />
                            <ModeButton active={activeMode === "RESEARCH"} onClick={() => setActiveMode("RESEARCH")} icon={<Globe size={12} />} label="Research" />
                            <ModeButton active={activeMode === "CODE"} onClick={() => setActiveMode("CODE")} icon={<Code2 size={12} />} label="Code" />
                        </div>

                        <div className="relative">
                            <input
                                type="text"
                                className="w-full bg-transparent p-4 pr-12 text-sm text-white placeholder-gray-600/50 font-light focus:outline-none"
                                placeholder="Type your instruction..."
                                value={input}
                                onChange={handleInputChange}
                                onKeyDown={(e) => e.key === "Enter" && !sending && sendMessage()}
                                disabled={sending}
                                autoFocus
                            />
                            <button
                                onClick={sendMessage}
                                disabled={sending}
                                className="absolute right-2 top-2 p-2 bg-white text-black hover:bg-gray-200 rounded-lg transition-all disabled:opacity-50"
                            >
                                <Send size={16} />
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Coming Soon Modal */}
            {showComingSoon && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50" onClick={() => setShowComingSoon(false)}>
                    <div className="bg-[#0f0f11] border border-white/10 rounded-xl p-8 max-w-md mx-4 shadow-2xl" onClick={(e) => e.stopPropagation()}>
                        <div className="text-center">
                            <div className="w-12 h-12 bg-emerald-500/10 rounded-full flex items-center justify-center mx-auto mb-4">
                                <Lock size={24} className="text-emerald-500" />
                            </div>
                            <h3 className="text-xl font-bold text-white mb-2">{comingSoonFeature}</h3>
                            <p className="text-gray-400 text-sm mb-6">
                                This feature is currently in development and will be available soon.
                            </p>
                            <button
                                onClick={() => setShowComingSoon(false)}
                                className="w-full bg-white text-black hover:bg-gray-200 transition-colors py-2 rounded font-medium text-sm"
                            >
                                Got it
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Knowledge Base Modal (Engineering Truth) */}
            {showMemories && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50" onClick={() => setShowMemories(false)}>
                    <div className="bg-[#0f0f11] border border-white/10 rounded-xl p-8 max-w-lg w-full mx-4 shadow-2xl" onClick={(e) => e.stopPropagation()}>
                        <div className="flex items-center gap-3 mb-6">
                            <div className="w-10 h-10 bg-emerald-500/10 rounded-full flex items-center justify-center">
                                <Database size={20} className="text-emerald-500" />
                            </div>
                            <div>
                                <h3 className="text-xl font-bold text-white">Knowledge Base</h3>
                                <p className="text-gray-500 text-xs font-mono">Long-Term Memory (RAG)</p>
                            </div>
                        </div>

                        <div className="max-h-80 overflow-y-auto space-y-3 scrollbar-thin scrollbar-thumb-white/10">
                            {memoriesLoading && <div className="text-gray-500 text-sm animate-pulse">Loading memories...</div>}
                            {!memoriesLoading && memoriesList.length === 0 && (
                                <div className="text-gray-500 text-sm italic">No memories stored yet. Start a conversation to build knowledge.</div>
                            )}
                            {memoriesList.map((mem: any, idx: number) => (
                                <div key={idx} className="p-3 bg-[#18181b] rounded border border-white/5 text-sm">
                                    <div className="text-emerald-400 font-mono text-[10px] uppercase tracking-widest mb-1">{mem.type || 'FACT'}</div>
                                    <div className="text-gray-200">{mem.content}</div>
                                </div>
                            ))}
                        </div>

                        <button
                            onClick={() => setShowMemories(false)}
                            className="mt-6 w-full bg-white text-black hover:bg-gray-200 transition-colors py-2 rounded font-medium text-sm"
                        >
                            Close
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}

// --- SUB-COMPONENTS ---

function SessionRow({ title, active, onClick, icon }: any) {
    return (
        <button
            onClick={onClick}
            className={`w-full flex items-center gap-3 px-3 py-2 rounded text-sm transition-all group relative ${active
                ? "bg-[#18181b] text-white border-l-2 border-emerald-500"
                : "text-gray-600 hover:text-gray-300 hover:bg-white/5 text-xs"
                }`}
        >
            <span className={active ? "text-white" : "text-gray-600 group-hover:text-gray-400"}>{icon}</span>
            <span className="truncate flex-1 text-left">{title || "Untitled Session"}</span>
            <MoreHorizontal size={12} className="opacity-0 group-hover:opacity-100 text-gray-500 transition-opacity" />
        </button>
    );
}

function FooterItem({ icon, label, onClick }: any) {
    return (
        <button onClick={onClick} className="w-full flex items-center gap-3 px-3 py-2 rounded text-sm text-gray-500 hover:text-gray-300 hover:bg-white/5 transition-colors">
            {icon}
            <span>{label}</span>
        </button>
    );
}

function ModeButton({ active, onClick, icon, label }: any) {
    return (
        <button
            onClick={onClick}
            className={`
        flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all
        ${active ? 'bg-white/10 text-white shadow-sm' : 'text-gray-500 hover:text-gray-300 hover:bg-white/5'}
      `}
        >
            {icon}
            <span>{label}</span>
        </button>
    );
}
