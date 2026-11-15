"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import AuthForm from "@/components/AuthForm";
import { apiFetch } from "@/lib/api";
import { setToken } from "@/lib/auth";
import type { Token } from "@/lib/types";

export default function SignupPage() {
    const router = useRouter();

    async function handleSignup(email: string, password: string) {
        await apiFetch("/auth/signup", {
            method: "POST",
            body: JSON.stringify({ email, password }),
        });
        const data = await apiFetch<Token>("/auth/login", {
            method: "POST",
            body: JSON.stringify({ email, password }),
        });
        setToken(data.access_token);
        router.push("/dashboard");
    }

    return (
        <AuthForm
            title="Create an account"
            submitLabel="Sign up"
            onSubmit={handleSignup}
            footer={<>already have an account? <Link href="/login" className="underline">Log in</Link></>}
        />
    );
}