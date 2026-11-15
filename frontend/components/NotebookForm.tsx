"use client"

import { useState, type SyntheticEvent} from "react";

type NotebookFormProps = {
    onCreate: (title: string, description: string) => Promise<void>;
};

export default function NotebookForm({ onCreate }: NotebookFormProps) {
    const [title, setTitle] = useState("");
    const [description, setDescription] = useState("");
    const [error, setError] = useState<string | null>(null);
    const [saving, setSaving] = useState(false)

    async function handleSubmit(e: SyntheticEvent<HTMLFormElement>) {
        e.preventDefault();
        setError(null);
        setSaving(true);
        try {
            await onCreate(title, description);
            setTitle("")
            setDescription("")
        } catch (err) {
            setError(err instanceof Error ? err.message : "something went wrong")
        } finally {
            setSaving(false);
        }
    }

    return (
        <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-2 rounded border p-4">
            <input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Notebook title"
                required
                maxLength={200}
                className="rounded border px-3 py-2"
            />
            <textarea
                value = {description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Description (optional)"
                maxLength={2000}
                rows = {2}
                className="rounded border px-3 py-2"
            />
            {error && <p className="text-sm text-red-600">{error}</p>}
            <button
                type="submit"
                disabled={saving}
                className="self-start rounded bg-black px-4 py-2 text-white disabled:opacity-50"
            >
                {saving ? "Creating...": "Create notebook"}
            </button>
        </form>
    );
}