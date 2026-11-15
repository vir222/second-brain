"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import AuthForm from "@/components/AuthForm";
import { apiFetch } from "@/lib/api";
import { setToken } from "@/lib/auth";
import type { Token } from "@/lib/types";

export default function LoginPage() {
    const router = useRouter();

    async function handleLogin(email: string, password: string) {
        const data = await apiFetch<Token>("/auth/login", {
            method: "POST",
            body: JSON.stringify({ email, password }),
        });
        setToken(data.access_token);
        router.push("/dashboard");
    }

    return (
        <AuthForm
            title="Login"
            submitLabel="Log in"
            onSubmit={handleLogin}
            footer={<>no account? <Link href="/signup" className="underline">sign up</Link></>}
        />
    );
}   