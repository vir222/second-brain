import { getToken } from "./auth";
import type { StreamEvent } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

export class ApiError extends Error {
    status: number;
    constructor(status: number, message: string) {
        super(message);
        this.status = status;
    }
}

export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
    const headers = new Headers(options.headers);
    if (typeof options.body === "string") headers.set("Content-Type", "application/json");
    const token = getToken();
    if (token) headers.set("Authorization", `Bearer ${token}`);
    const res = await fetch(`${API_URL}${path}`, { ...options, headers });
    if (!res.ok) throw await toApiError(res);

    if (res.status === 204) return undefined as T;
    return res.json() as Promise<T>;
}

async function toApiError(res: Response): Promise<ApiError> {
    let message = `Request failed (${res.status})`;
    try {
        const data = await res.json();
        if (typeof data.detail === "string") {
            message = data.detail;
        } else if (Array.isArray(data.detail)) {
            message = data.detail.map((e: {msg : string }) => e.msg.join(", "));
        }
    } catch {
        //keep default message no json body
    }
    return new ApiError(res.status, message);
}

export async function apiStream(path : string, body: unknown, onEvent : (event: StreamEvent) => void, signal?: AbortSignal): Promise<void> {
    const headers = new Headers({ "Content-Type" : "application/json"});
    const token = getToken()
    if (token) headers.set("Authorization", `Bearer ${token}`);
    const res = await fetch(`${API_URL}${path}`, {
        method: "POST",
        headers,
        body : JSON.stringify(body),
        signal,
    });
    if (!res.ok) throw await toApiError(res);
    if (!res.body) throw new ApiError(res.status, "No response body");
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
        const {done, value} = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, {stream: true});
        console.log("RAW:", JSON.stringify(buffer));
        const rawEvents = buffer.split("\n\n");
        buffer = rawEvents.pop() ?? "";

        for (const rawEvent of rawEvents) {
            let eventName = "";
            let data = "";
            for (const line of rawEvent.split("\n")) {
                if (line.startsWith("event: ")) eventName = line.slice(7);
                else if (line.startsWith("data: ")) data += line.slice(6);
            }
            if (eventName && data) {
                onEvent({ event: eventName, data: JSON.parse(data)} as StreamEvent);
            }
        }
    }
}