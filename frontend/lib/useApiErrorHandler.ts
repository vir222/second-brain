"use client"
import { useCallback } from "react";
import { useRouter } from "next/navigation";
import { ApiError } from "./api";
import { clearToken } from "./auth";

export function useApiErrorHandler() {
    const router = useRouter();
    return useCallback(
        (err: unknown): string | null => {
            if (err instanceof ApiError && err.status === 401) {
                clearToken();
                router.replace("/login");
                return null;
            }
            return err instanceof Error ? err.message : "Something went wrong";
        },
        [router]
    );
}