"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState, useRef } from "react";
import { apiFetch } from "@/lib/api";
import type { Flashcard, Rating } from "@/lib/types";
import { useApiErrorHandler } from "@/lib/useApiErrorHandler";

const RATINGS: { rating: Rating; label: string; key: string; className: string}[] = [
    { rating: "again", label: "Again", key: "1", className: "border-red-300 text-red-700"},
    { rating: "hard", label: "Hard", key: "2", className: "border-amber-300 text-amber-700"},
    { rating: "good", label: "Good", key: "3", className: "border-green-300 text-green-700"},
    { rating: "easy", label: "Easy", key: "4", className: "border-blue-300 text-blue-700"},
];

export default function StudySession() {
    const submittingRef = useRef(false);
    const params = useParams<{ id: string}>();
    const notebookId = params.id
    const handleError = useApiErrorHandler();

    const [queue, setQueue] = useState<Flashcard[] | null>(null);
    const [flipped, setFlipped] = useState(false);
    const [submitting, setSubmitting] = useState(false);
    const [reviewedCount, setReviewedCount] = useState(0);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        apiFetch<Flashcard[]>(`/notebooks/${notebookId}/flashcards/due?limit=20`)
        .then(setQueue)
        .catch((err) => setError(handleError(err)));
    }, [notebookId, handleError]);

    const current = queue?.[0] ?? null;

    async function rate(rating: Rating) {
        if (!current || submittingRef.current) return;
        submittingRef.current = true;
        setSubmitting(true);
        setError(null);
        try {
            await apiFetch<Flashcard>(`/notebooks/${notebookId}/flashcards/${current.id}/review`, {
                method : "POST",
                body : JSON.stringify({ rating }),
            });
            setQueue((prev) => {
                if (!prev) return prev;
                const [first, ...rest] = prev;
                return rating === "again" ? [...rest, first] : rest;
            });
            setReviewedCount((n) => n + 1);
            setFlipped(false);
        } catch (err) {
            setError(handleError(err));
        } finally {
            setSubmitting(false);
            submittingRef.current = false;
        }
    }

    useEffect(() => {
        function onKeyDown(e: KeyboardEvent) {
            if (!current) return;
            if (e.key === " " && !flipped) {
                e.preventDefault()
                setFlipped(true);
                return;
            }
            if (flipped) {
                const match = RATINGS.find((r) => r.key === e.key);
                if (match) rate(match.rating);
            }
        }
        window.addEventListener("keydown", onKeyDown);
    });

    const backLink = (
        <Link href={`/notebooks/${notebookId}`} className="text-sm underline">
            ← Back to notebook
        </Link>
    );

    if (queue === null) {
        return error ? (
            <main className="mx-auto mt-12 max-w-xl px-4">
                {backLink}
                <p className="mt-4 text-red-600">{error}</p>
            </main>
        ) : (
            <p className="p-8">Loading...</p>
        );
    }

    if (!current) {
        return (
            <main className="mx-auto mt-12 max-w-xl px-4">
                {backLink}
                <h1 className="mt-6 text-2x1 font-semibold">
                    {reviewedCount > 0 ? "Session complete!" : "Nothing to study"}
                </h1>
                <p className="mt-2 text-gray-600">
                    {reviewedCount > 0
                        ? `You did ${reviewedCount} reviews. Come back later for more.`
                        : "No cards are due right now. Come back later, or make more flashcards."}
                </p>
            </main>
        );
    }

    return (
        <main className="mx-auto mt-12 max-w-xl px-4">
            <div className="flex items-center justify-between">
                {backLink}
                <span className="text-sm text-gray-500">{queue.length} left</span>
            </div>

            <div className="mt-6 rounded-lg border p-6">
                <p className="text-lg font-medium">{current.front}</p>
                {flipped && (
                    <>
                        <hr className="my-4" />
                        <p className="whitespace-pre-wrap">{current.back}</p>
                        {current.page_number !== null && (
                            <p className="mt-3 text-xs text-gray-400">From page {current.page_number}</p>
                        )}
                    </>
                )}
            </div>

            {error && <p className="mt-4 text-sm text-red-600">{error}</p>}

            {!flipped ? (
                <button
                    type="button"
                    onClick={() => setFlipped(true)}
                    className="mt-4 w-full rounded bg-black px-4 py-3 text-white"
                >
                    Show answer <span className="text-xs opacity-70">(Space)</span>
                </button>
            ) : (
                <div className="mt-4 grid grid-cols-4 gap-2">
                    {RATINGS.map((r) => (
                        <button
                            key={r.rating}
                            type="button"
                            onClick={() => rate(r.rating)}
                            disabled={submitting}
                            className={`rounded border px-2 py-3 text-sm font-medium disabled:opacity-50 ${r.className}`}
                        >
                            {r.label}
                            <span className="block text-xs opacity-60">{r.key}</span>
                        </button>
                    ))}
                </div>
            )}
        </main>
    );
}