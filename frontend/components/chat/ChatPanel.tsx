"use client";

import { useEffect, useRef, useState, type SyntheticEvent } from "react";
import MessageBubble from "./MessageBubble";
import { apiFetch, apiStream } from "@/lib/api";
import type { ChatMessage, Conversation, ConversationDetail, StreamEvent } from "@/lib/types";
import { useApiErrorHandler } from "@/lib/useApiErrorHandler";

type ChatPanelProps = {
    notebookId : string;
    disabled : boolean;
};
let nextTempId = -1;

export default function ChatPanel ({ notebookId, disabled}: ChatPanelProps) {
    const handleError = useApiErrorHandler();
    const controllerRef = useRef<AbortController | null>(null);
    const threadRef = useRef<HTMLDivElement>(null);
    const loadRequestRef = useRef(0);
    const [conversations, setConversations] = useState<Conversation[]>([]);
    const [activeId, setActiveId] = useState<number | null>(null);
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [input, setInput] = useState("");
    const [streaming, setStreaming] = useState(false);
    const [loadingThread, setLoadingThread] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const conversationsPath = `/notebooks/${notebookId}/conversations`;

    useEffect(() => {
        apiFetch<Conversation[]>(`/notebooks/${notebookId}/conversations`)
        .then(setConversations)
        .catch((err) => setError(handleError(err)));
    }, [notebookId, handleError]);

    useEffect(() => {
        return () => controllerRef.current?.abort();
    }, []);

    useEffect(() => {
        const thread = threadRef.current;
        if (thread) thread.scrollTop = thread.scrollHeight;
    }, [messages]);

    function refreshConversations() {
        apiFetch<Conversation[]>(conversationsPath)
        .then(setConversations)
        .catch(() => {})
    }

    function startNewConversation() {
        setActiveId(null);
        setMessages([]);
        setError(null);
    }

    async function openConversation(id: number) {
        setActiveId(id);
        setMessages([]);
        setError(null);
        setLoadingThread(true);
        const requestId = ++loadRequestRef.current;

        try {
            const detail = await apiFetch<ConversationDetail>(`${conversationsPath}/${id}`);
            if (requestId === loadRequestRef.current) setMessages(detail.messages);
        } catch (err) {
            if (requestId === loadRequestRef.current) setError(handleError(err));
        } finally {
            if (requestId === loadRequestRef.current) setLoadingThread(false);
        }
    }

    async function deleteConversation(id: number) {
        if (!window.confirm("Delete this conversation?")) return;
        try {
            await apiFetch(`${conversationsPath}/${id}`, {method: "DELETE"});
            setConversations((prev) => prev.filter((c) => c.id !== id));
            if (activeId === id) startNewConversation();
        } catch (err) {
            setError(handleError(err));
        }
    }

    async function handleSend(e: SyntheticEvent<HTMLFormElement>) {
        e.preventDefault();
        const content = input.trim();
        if (!content || streaming) return;

        setError(null);
        setStreaming(true);

        let conversationId = activeId;
        if (conversationId == null) {
            try {
                const created = await apiFetch<Conversation>(conversationsPath, {
                    method : "POST",
                    body: JSON.stringify({}),
                });
                conversationId = created.id;
                setActiveId(created.id);
                setConversations((prev) => [created, ...prev]);
            } catch (err) {
                setError(handleError(err));
                setStreaming(false);
                return;
            }
        }

        const userTempId = nextTempId--;
        const assistantTempID = nextTempId--;
        const now = new Date().toISOString();

        setMessages((prev) => [
            ...prev,
            {id: userTempId, role: "user", content, sources: null, created_at: now},
            {id: assistantTempID, role : "assistant", content: "", sources: [], created_at: now, status: "streaming"},
        ]);
        setInput("");

        function updateAssistant(update: (m: ChatMessage) => ChatMessage) {
            setMessages((prev) => prev.map((m) => (m.id === assistantTempID ? update(m) : m)))
        }

        function handleEvent(evt: StreamEvent) {
            switch (evt.event) {
                case "sources": {
                    const sources = evt.data.sources;
                    updateAssistant((m) => ({ ...m, sources }));
                    break;
                }
                case "delta": {
                    const text = evt.data.text;
                    updateAssistant((m) => ({ ...m, content: m.content + text}));
                    break;
                }
                case "done": {
                    const {cited, message_id } = evt.data;
                    updateAssistant((m) => ({
                        ...m,
                        id: message_id ?? m.id,
                        status: undefined,
                        sources: (m.sources ?? []).map((s) => ({ ...s, cited: cited.includes(s.number)})),
                    }));
                    break;
                }
                case "error": {
                    const message = evt.data.message;
                    updateAssistant((m) => ({ ...m, status: "error"}));
                    setError(message);
                    break;
                }
            }
        }

        const controller = new AbortController();
        controllerRef.current = controller;

        try {
            await apiStream(`${conversationsPath}/${conversationId}/messages/stream`, { content }, handleEvent, controller.signal);
        } catch (err) {
            if (controller.signal.aborted) {
                updateAssistant((m) => ({ ...m, status: "stopped" }));
            } else {
                updateAssistant((m) => ({ ...m, status: "error" }));
                setError(handleError(err)); 
            }
        } finally {
            controllerRef.current = null;
            setStreaming(false);
            refreshConversations();
        }
    }

    function handleStop() {
        controllerRef.current?.abort();
    }

    return (
        <section className="mt-8">
            <h2 className="text-lg font-semibold">Chat with your documents</h2>

            <div className="mt-2 flex flex-col rounded border md:flex-row">
                <aside className="border-b p-3 md: w-56 md:shrink-0 md:border-b-0 md:border.r">
                    <button
                        type="button"
                        onClick={startNewConversation}
                        disabled={streaming}
                        className="w-full rounded border px-3 py-1.5 text-sm disabled:opacity-50"
                    >
                        + New conversation
                    </button>
                    <ul className="mt-3 flex max-h-40 flex-col gap-1 overflow-y-auto md:max-h-[28rem]">
                        {conversations.map((c) => (
                            <li key={c.id} className="flex items-center gap-1">
                                <button
                                    type="button"
                                    onClick={()=> openConversation(c.id)}
                                    disabled = {streaming}
                                    className={`min-w-0 flex-1 truncate rounded px-2 py-1 text-left text-sm disabled:opacity-50 ${
                                        c.id === activeId ? "bg-gray-600 font-medium" : "hover:bg-gray-500"
                                    }`}
                                >
                                    {c.title}
                                </button>
                                <button
                                    type="button"
                                    onClick={() => deleteConversation(c.id)}
                                    disabled={streaming}
                                    aria-label="Delete Conversation"
                                    className="px-1 text-xs text-gray-400 hover:text-red-600 disabled:opacity-50"
                                >
                                    ✕
                                </button>
                            </li>
                        ))}
                    </ul>
                </aside>

                <div className="flex min-w-0 flex-1 flex-col p-3">
                    <div ref={threadRef} className="h-[28rem] overflow-y-auto pr-1">
                        {loadingThread ? (
                            <p className="text-sm text-gray-500">Loading...</p>
                        ) : messages.length === 0 ? (
                            <p className="text-sm text-gray-500">
                                {disabled
                                    ? "Upload a document to start chatting"
                                    : "Ask a question to start a new conversation."}
                            </p>
                        ) : (
                            <div className="flex flex-col gap-4">
                                {messages.map((m) => (
                                    <MessageBubble key={m.id} message={m} />
                                ))}
                            </div>
                        )}
                    </div>
                    {error && <p className="mt-2 text-sm text-red-600">{error}</p>}

                    <form onSubmit={handleSend} className="mt-3 flex gap-2">
                        <input
                            value = {input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder={disabled ? "Upload a document first" : "Ask a question..."}
                            disabled = {disabled || streaming}
                            maxLength={2000}
                            className="min-w-0 flex-1 rounded border px-3 py-2 text-sm disabled:bg-gray-50"
                        />
                        {streaming ? (
                            <button type="button" onClick={handleStop} className="rounded border px-4 py-2 text-sm">
                                Stop
                            </button>
                        ) : (
                            <button
                                type="submit"
                                disabled = {disabled || !input.trim()}
                                className="rounded bg-black px-4 py-2 text-sm text-white disabled:opacity-50"
                            >
                                Send
                            </button>
                        )}
                    </form>
                </div>
            </div>
        </section>
    );
}