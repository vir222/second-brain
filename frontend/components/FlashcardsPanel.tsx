"use client"

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import type { Flashcard, FlashcardStats } from "@/lib/types";
import { useApiErrorHandler } from "@/lib/useApiErrorHandler";
import { stat } from "fs";

type FlashcardPanelProps = {
    notebookId: string;
    refreshKey: number;
};

function formatDue(dueAt: string): string {
    const due = new Date(dueAt);
    if (due.getTime() <= Date.now()) return "due now";
    return `due ${due.toLocaleDateString()}`;
}

export default function FlashcardsPanel({ notebookId, refreshKey} : FlashcardPanelProps) {
    const handleError = useApiErrorHandler();
    const [stats, setAskStatus] = useState<FlashcardStats | null>(null);
    const [cards, setCards] = useState<Flashcard[]>([]);
    const [showCards, setShowCards]  = useState(false);
    const [reloadCount, setReloadCount] = useState(0);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const base = `/notebooks/${notebookId}/flashcards`;
        Promise.all([apiFetch<FlashcardStats>(`${base}/stats`), apiFetch<Flashcard[]>(base)])
        .then(([newStats, list]) => {
            setAskStatus(newStats);
            setCards(list);
        })
        .catch((err) => setError(handleError(err)));
    }, [notebookId, refreshKey, reloadCount, handleError]);

    async function handleDelete(cardId: number) {
        if (!window.confirm("Delete this Flashcard")) return;
        setError(null);
        try {
            await apiFetch(`/notebooks/${notebookId}/flashcards/${cardId}`, { method: "DELETE"});
            setReloadCount((n) => n + 1);
        } catch (err) {
            setError(handleError(err));
        }
    }

    if (!stats) {
        return error ? <p className="mt-8 text-sm text-red-600">{error}</p> : null;
    }

    return (
        <section className="mt-8">
            <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold">Flashcards</h2>
                {stats.due > 0 ? (
                    <Link
                        href={`/notebooks/${notebookId}/study`}
                        className="rounded bg-black px-4 py-2 text-sm text-white"
                    >
                        Study now ({stats.due} due)
                    </Link>
                ) : (
                    stats.total > 0 && <span className="text-sm text-gray-500">All Caught Up!</span>
                )}
            </div>
            <p className="mt-1 text-sm text-gray-500">
                {stats.total === 0
                    ? "No flashcards yet. Use Make Flashcards on a document below."
                    : `${stats.total} cards - ${stats.due} - ${stats.new} new`}
            </p>
            {error && <p className="mt-2 text-sm text-red-600">{error}</p>}

            {stats.total > 0 && (
                <button
                    type="button"
                    onClick={() => setShowCards((v) => !v)}
                    className="mt-2 text-sm underline"
                >
                    {showCards ? "Hide Cards" : "Show all Cards"}
                </button>
            )}

            {showCards && (
                <ul className="mt-3 flex flex-col gap-2">
                    {cards.map((card) => (
                        <li key={card.id} className="reounded border p-3 text-sm">
                            <div className="flex justify-between gap-4">
                                <p className="font-medium">{card.front}</p>
                                <button
                                    type="button"
                                    onClick={() => handleDelete(card.id)}
                                    className="shrink-0 text-xs text-red-600 underline"
                                >
                                    Delete
                                </button>
                            </div>
                            <p className="mt-1 text-gray-600">{card.back}</p>
                            <p className="mt-1 text-xs text-gray-400">
                                {card.page_number !== null && `Page ${card.page_number} - `}
                                {formatDue(card.due_at)}
                            </p>
                        </li>
                    ))}
                </ul>
            )}
        </section>
    );
}