"use client";
import { useState, type FormEvent, type ReactNode } from "react";

type AuthFormProps = {
    title: string;
    submitLabel: string;
    onSubmit: (email: string, password: string) => Promise<void>;
    footer: ReactNode;
};

export default function AuthForm({ title, submitLabel, onSubmit, footer }: AuthFormProps) {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    async function handleSubmit(e: FormEvent<HTMLFormElement>) {
        e.preventDefault();
        setError(null);
        setLoading(true);
        try {
            await onSubmit(email, password);
        } catch (err) {
            setError(err instanceof Error ? err.message : "something went wrong");
        } finally {
            setLoading(false);
        }
    }
    
    return (
        <main className="mx-auto mt-24 max-w-sm px-4">
            <h1 className="mb-6 text-2xl font-semibold">{title}</h1>
            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
                <input
                    type="email"
                    placeholder="Email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="rounded border px-3 py-2"
                />
                <input
                    type="password"
                    placeholder="Password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    className="rounded border px-3 py-2"
                />
                {error && <p className="text-sm text-red-600">{error}</p>}
                <button
                    type="submit"
                    disabled={loading}
                    className="rounded bg-black px-3 py-2 text-white disabled:opacity-50"
                >
                    {loading ? "Please Wait..." : submitLabel}
                </button>
            </form>
            <p className="mt-4 text-sm">{footer}</p>
        </main>
    );
}