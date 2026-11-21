"use client";

import { useState, type ReactNode } from "react";
import type { ChatMessage } from "@/lib/types";
const CITATION_SPLIT = /(\[\d+\])/;
const CITATION_EXACT = /^\[(\d+)\]$/;

export default function MessageBubble( { message }: {message: ChatMessage}) {
    const [activeSource, setActiveSource] = useState<number | null>(null);
    if (message.role === "user") {
        return (
            <div className="flex justify-end">
                <p className="max-2-[80%] whitespace-pre-wrap rounded-lg bg-black px-3 py-2 text-sm text-white">
                    {message.content}
                </p>
            </div>
        );
    }

    const isStreaming = message.status === "streaming";
    const citedSources = isStreaming ? [] : (message.sources ?? []).filter((s) => s.cited);
    const citedNumbers = new Set(citedSources.map((s) => s.number));
    
    function handleCitationClick(n: number) {
        setActiveSource(n);
        document.getElementById(`source-${message.id}-${n}`)?.scrollIntoView({ behavior: "smooth", block: "nearest"});
    }
    function renderContent(): ReactNode[] {
        return message.content.split(CITATION_SPLIT).map((part, i) => {
            const match = part.match(CITATION_EXACT);
            if (match && citedNumbers.has(Number(match[1]))) {
                const n = Number(match[1]);
                return (
                    <button
                        key={i}
                        type = "button"
                        onClick={()=> handleCitationClick(n)}
                        className="mx-0.5 rounded bg-blue-50 px-1 text-xs font-medium text-blue-700 hover:bg-blue-100"
                    >
                        {n}
                    </button>
                );
            }
            return <span key={i}>{part}</span>;
        });
    }

    return (
        <div className="flex flex-col gap-2">
            <div className="max-w-[90%] whitespace-pre-wrap rounded-lg bg-gray-800 px-3 py-2 text-sm leading-relaxed text-gray-100">
                {renderContent()}
                {isStreaming && <span className="anitmate-pulse">▍</span>}
            </div>

            {message.status === "stopped" && (
                <p className="text-xs text-gray-500">{"Stopped. This reply wasn't saved."}</p>
            )}
            {message.status === "error" && (
                <p className="text-xs text-red-600">{"This reply failed and wasn't saved."}</p> 
            )}

            {citedSources.length > 0 && (
                <ul className="flex flex-col gap-2">
                    {citedSources.map((s) => (
                        <li
                            key = {s.number}
                            id= {`source-${message.id}-${s.number}`}
                            className={`rounded border p-2 text-xs ${
                                activeSource === s.number ? "border-blue-400 ring-2 ring-blue-200" : ""
                            }`}
                        >
                            <p className="text-gray-500">
                                [{s.number}] {s.filename}
                                {s.page_number !== null && ` - page ${s.page_number}`}
                            </p>
                            <p className={`mt-1 ${activeSource === s.number ? "" : "line-clamp-2"}`}>
                                {s.content}
                            </p>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
}