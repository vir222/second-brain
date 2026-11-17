"use client"

import { useState, type SyntheticEvent} from "react";
import { useRouter } from "next/navigation";
import { apiFetch, ApiError } from "@/lib/api";
import { clearToken } from "@/lib/auth";
import type { SearchResult } from "@/lib/types";

const WEAK_MATCH_SCORE = 0.3;

function ResultItem({ result } : {result : SearchResult}){
    const [expanded, setExpanded] = useState(false);
    const isWeak = result.score < WEAK_MATCH_SCORE;

    return (
        <li className={`rounded border p-4 ${isWeak ? "opacity-60": ""}`}>
            <div className="flex items-center justify-between gap-4 text-xs text-gray-500">
                <span className="truncate">
                    {result.filename}
                    {result.page_number !== null && ` - page ${result.page_number}`}
                </span>
                <span className="shrink-0">
                    {isWeak && "weak match - "}score {result.score.toFixed(2)}
                </span>
            </div>
            <p className={`mt-2 text-sm ${expanded ? "" : "line-clamp-3"}`}>{result.content}</p>
            <button
                type="button"
                onClick={()=>setExpanded((prev) => !prev)}
                className="mt-1 text-xs underline"
            >
                {expanded ? "Show Less" : "Show More"}
            </button>
        </li>
    );
}

type SearchPanelProps = {
    notebookId : string;
    disabled : boolean;
};

export default function SearchPanel({notebookId, disabled}: SearchPanelProps) {
    const router = useRouter()
    const [query, setQuery] = useState("");
    const [results, setResults] = useState<SearchResult[] | null>(null);
    const [searching, setSearching] = useState(false);
    const [error, setError] = useState<string | null>(null);

    async function handleSearch(e : SyntheticEvent<HTMLFormElement>) {
        e.preventDefault()
        const trimmed = query.trim();

        if (!trimmed) return;

        setError(null);
        setSearching(true);
        try {
            const data = await apiFetch<SearchResult[]>(`/notebook/${notebookId}/search`, {
                method : "POST",
                body : JSON.stringify({query: trimmed, limit:5}),       
            });
            setResults(data)
        } catch (err) {
            if (err instanceof ApiError && err.status === 401) {
                clearToken()
                router.replace("/login");
                return;
            }
            setError(err instanceof Error ? err.message : "something went wrong");
        } finally {
            setSearching(false);
        }
    }

    function handleClear() {
        setQuery("");
        setResults(null);
        setError(null);
    }

    const allWeak =
    results !== null &&
    results.length > 0 &&
    results.every((r) => r.score < WEAK_MATCH_SCORE);

    return (
        <section className="mt-8">
            <h2 className="text-lg font-semibold">Search this notebook</h2>
            <form onSubmit={handleSearch} className="mt-2 flex gap-2">
                <input
                    value = {query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder={disabled ? "Upload a document to start searching" : "Ask a question about your documents..."}
                    disabled = {disabled}
                    maxLength = {1000}
                    className="flex-1 rounded border px-3 py-2 disabled:bg-gray-50"
                />
                <button
                    type="submit"
                    disabled = {disabled || searching || !query.trim()}
                    className="rounded bg-black px-4 py-2 text-sm text-white disabled:opacity-50"
                >
                    {searching ? "Searching..." : "Search"}
                </button>
                {results !== null && (
                    <button type = "button" onClick={handleClear} className="text-sm underline">
                        Clear
                    </button>
                )}
            </form>

            {error && <p className="mt-4 text-sm text-red-600">{error}</p>}

            {results !== null &&
                (results.length === 0 ? (
                    <p className="mt-4 text-sm text-gray-500">
                        No results. Make sure your documents finished processing.
                    </p>
                ) : (
                    <>
                        {allWeak && (
                            <p className="mt-4 text-sm text-amber-700">
                                None of the look like strong matches. Your documents may not cover this topic.
                            </p>
                        )}
                        <ul className="mt-4 flex flex-col gap-3">
                            {results.map((result) => (
                                <ResultItem key={result.chunk_id} result={result} />
                            ))}
                        </ul>
                    </>
                ))}
        </section>
    );
}