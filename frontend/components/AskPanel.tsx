"use client"

import { useEffect, useRef, useState, type SyntheticEvent } from "react";
import { useRouter } from "next/navigation";
import { apiStream, ApiError } from "@/lib/api";
import { clearToken } from "@/lib/auth";
import type { Source, StreamEvent} from "@/lib/types";

type AskStatus = "idle" | "streaming" | "done" | "error";

type AskPanelProps = {
    notebookId : string;
    disabled : boolean;
};

export default function AskPanel( {notebookId, disabled} : AskPanelProps) {
    const router = useRouter();
    const controllerRef = useRef<AbortController | null>(null);

    const [question, setQuestion] = useState("");
    const [answer, setAnswer] = useState("");
    const [sources, setSources] = useState<Source[]>([]);
    const [askStatus, setAskStatus] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        return () => controllerRef.current?.abort();
    }, []);

    function handleEvent(e: StreamEvent) {
        switch (e.event) {
            case "sources":
                setSources(e.data.sources);
                break;
            case "delta":
                setAnswer((prev) => prev + e.data.text);
                break;
            case "done":
                setSources((prev) => prev.map((s) => ({...s, cited : e.data.cited.includes(s.number)}))
            );
                setAskStatus("done");
                break;
            case "error":
                setError(e.data.message);
                setAskStatus("error");
                break; 
        }
    }

    async function handleAsk(e : SyntheticEvent<HTMLFormElement>) {
        e.preventDefault()
        const trimmed = question.trim();
        if (!trimmed) return;

        const controller = new AbortController();
        controllerRef.current = controller;

        setAnswer("");
        setSources([]);
        setError(null);
        setAskStatus("streaming");
        try {
            await apiStream(
                `/notebooks/${notebookId}/ask/stream`,
                { question : trimmed },
                handleEvent,
                controller.signal
            );
        } catch (err) {
            if (controller.signal.aborted) {
                setAskStatus("done");
                return;
            }
            if (err instanceof ApiError && err.status == 401) {
                clearToken();
                router.replace("/login");
                return;
            }
            setError(err instanceof Error ? err.message : "Something went wrong");
            setAskStatus("error");
        } finally {
            controllerRef.current = null;
        }
    }

    function handleStop() {
        controllerRef.current?.abort();
    }
    const streaming = askStatus === "streaming";

    return (
        <section className="mt-8">
            <h2 className="text-lg font-semibold">Ask your documents</h2>

            <form onSubmit={handleAsk} className="my-2 flex gap-2">
                <input
                    value = {question}
                    onChange={(e) => setQuestion(e.target.value)}
                    placeholder = {disabled ? "Upload a document to start asking" : "Ask a question..."}
                    disabled = {disabled || streaming}
                    maxLength={2000}
                    className="flex-1 rounded border px-3 py-2 disabled:bg-gray-50"
                />
                {streaming ? (
                    <button type="button" onClick={handleStop} className="rounded border px-4 py-2 text-sm">
                       Stop 
                    </button>
                    ) : (
                        <button
                            type = "submit"
                            disabled = {disabled || !question.trim()}
                            className="rounded bg-black px-4 py-2 text-sm text-white disabled:opacity-50"
                        >
                            Ask
                        </button>
                    )}
            </form>

            {error && <p className="mt-4 text-sm text-red-600">{error}</p>}

            {(answer || streaming) && (
                <div className="mt-4 rounded border p-4">
                    <p className="whitespace-pre-wrap text-sm leading-relaxed">
                        {answer}
                        {streaming && <span className="animate-pulse">▍</span>}
                    </p>
                </div>
            )}
            {sources.length > 0 && (
                <div className="mt-4">
                    <h3 className="text-sm font-medium text-gray-700">Sources</h3>
                    <ul className="mt-2 flex flex-col gap-2">
                        {sources.map((source) => (
                            <li
                                key = {source.chunk_id}
                                className={`rounded border p-4 text-sm ${
                                    askStatus === "done" && !source.cited ? "opacity-50" : ""
                                }`}
                            >
                                <p className="text-xs text-gray-500">
                                    [{source.number}] {source.filename}
                                    {source.page_number !== null && ` - page ${source.page_number}`}
                                </p>
                                <p className="mt-1 line-clamp-2">{source.content}</p>   
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </section>
    );
}