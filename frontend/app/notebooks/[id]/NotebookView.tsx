"use client";

import Link from "next/link"
import { useParams, useRouter} from "next/navigation";
import { useEffect, useRef, useState, type SyntheticEvent } from "react";
import { apiFetch, ApiError } from "@/lib/api";
import { clearToken, getToken } from "@/lib/auth";
import type { DocumentStatus, Notebook, NotebookDocument} from "@/lib/types";
import SearchPanel from "@/components/SearchPanel";
//import AskPanel from "@/components/AskPanel";
import ChatPanel from "@/components/chat/ChatPanel";

const MAX_UPLOAD_MB = 20;
const POLL_INTERVAL_MS = 2000;

function formatBytes(bytes: number): string{
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes/1024).toFixed(1)} KB`;
    return `${(bytes/ (1024 * 1024)).toFixed(1)} MB`;
}

const STATUS_STYLES: Record<DocumentStatus, string> = {
    pending: "bg-gray-100 text-gray-700",
    processing: "bg-blue-100 text-blue-700",
    ready : "bg-green-100 text-green-700",
    failed : "bg-red-100 text-red-700"
};

function StatusBadge({ status }: { status: DocumentStatus}){
    return (
        <span className={`rounded px-2 py-0.5 text-xs font-medium ${STATUS_STYLES[status]}`}>
            {status}
        </span>
    );
}

export default function NotebookView() {
    const params = useParams<{ id: string}>();
    const notebookId = params.id;
    const router = useRouter();
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [notebook, setNotebook] = useState<Notebook | null>(null);
    const [documents, setDocuments] = useState<NotebookDocument[]>([]);
    const [loadError, setLoadError] = useState<string | null>(null);
    const [actionError, setActionError] = useState<string | null>(null);
    const [uploading, setUploading] = useState(false);

    useEffect(() => {
        if (!getToken()) {
            router.replace("/login");
            return;
        }

        Promise.all([
            apiFetch<Notebook>(`/notebooks/${notebookId}`),
            apiFetch<NotebookDocument[]>(`/notebooks/${notebookId}/documents`),
        ])
            .then(([nb, docs]) => {
                setNotebook(nb);
                setDocuments(docs);
            })
            .catch((err) => {
                if (err instanceof ApiError && err.status === 401) {
                    clearToken();
                    router.replace("/login");
                } else if (err instanceof ApiError && err.status === 404) {
                    setLoadError("Notebook not found");
                } else {
                    setLoadError(err instanceof Error ? err.message : "Something went wrong");
                }
            });
    }, [notebookId, router]);

    const hasActiveDocuments = documents.some(
        (doc) => doc.status === "pending" || doc.status === "processing"
    );
    const hasReadyDocuments = documents.some((doc) => doc.status === "ready");

    useEffect(() => {
        if (!hasActiveDocuments) return;

        const intervalId = setInterval(() => {
            apiFetch<NotebookDocument[]>(`/notebooks/${notebookId}/documents`)
            .then(setDocuments)
            .catch(() => {
                //ignoring and trying again
            });
        }, POLL_INTERVAL_MS);
        return () => clearInterval(intervalId);
    }, [hasActiveDocuments, notebookId]);

    function handleActionError(err: unknown) {
        if (err instanceof ApiError && err.status === 401) {
            clearToken();
            router.replace("login");
            return;
        }
        setActionError(err instanceof Error ? err.message : "Soemthing went wrong");
    }

    async function handleFileChange(e: SyntheticEvent<HTMLInputElement>) {
        const input = e.currentTarget;
        const file = input.files?.[0];
        if (!file) return;
        
        setActionError(null);

        if (file.size > MAX_UPLOAD_MB * 1024 * 1024) {
            setActionError(`file is larget than ${MAX_UPLOAD_MB} MB`);
            input.value = "";
            return;
        }

        setUploading(true);
        try {
            const formData = new FormData();
            formData.append("file", file);
            const created = await apiFetch<NotebookDocument>(`/notebooks/${notebookId}/documents`, {
                method: "POST",
                body: formData,
            });
            setDocuments((prev) => [created, ...prev]);
        } catch (err) {
            handleActionError(err);
        } finally {
            setUploading(false);
            input.value = "";
        }
    }

    async function handleReprocess(documentId: number) {
        setActionError(null);
        try {
            const updated = await apiFetch<NotebookDocument>(
                `/notebooks/${notebookId}/documents/${documentId}/reprocess`,
                { method : "POST"}
            );
            setDocuments((prev) => prev.map((d) => (d.id === documentId ? updated : d)));
        } catch (err) {
            handleActionError(err);
        }
    }

    async function handleDelete(documentId : number) {
        if (!window.confirm("Delete this document? This can not be undone.")) return;
        setActionError(null);
        try {
            await apiFetch(`/notebooks/${notebookId}/documents/${documentId}/`, {method : "DELETE"});
            setDocuments((prev) => prev.filter((d) => d.id !== documentId));
        } catch (err) {
            handleActionError(err);
        }
    }

    if (loadError) {
        return (
            <main className="mx-auto mt-12 max-w-2x1 px-4">
                <p className="text-red-600">{loadError}</p>
                <Link href="/dashboard" className="mt-4 inline-block text-sm underline">
                    ← back to notebooks
                </Link>
            </main>
        );
    }

    if (!notebook) return <p className="p-8">Loading...</p>

    return (
    <main className="mx-auto mt-12 max-w-4xl px-4 pb-12">
      <Link href="/dashboard" className="text-sm underline">
        ← Back to notebooks
      </Link>

      <h1 className="mt-4 text-2xl font-semibold">{notebook.title}</h1>
      {notebook.description && <p className="mt-1 text-gray-600">{notebook.description}</p>}
      <ChatPanel notebookId={notebookId} disabled={!hasReadyDocuments} />
      <SearchPanel notebookId={notebookId} disabled = {!hasReadyDocuments}/>

      <div className="mt-8 flex items-center justify-between">
        <h2 className="text-lg font-semibold">Documents ({documents.length})</h2>
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading}
          className="rounded bg-black px-4 py-2 text-sm text-white disabled:opacity-50"
        >
          {uploading ? "Uploading..." : "Upload file"}
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.txt,.md"
          onChange={handleFileChange}
          className="hidden"
        />
      </div>
      <p className="mt-1 text-xs text-gray-500">PDF, TXT, or Markdown, up to {MAX_UPLOAD_MB} MB</p>

      {actionError && <p className="mt-4 text-sm text-red-600">{actionError}</p>}

      {documents.length === 0 ? (
        <p className="mt-4 text-sm text-gray-500">No documents yet. Upload one to get started.</p>
      ) : (
        <ul className="mt-4 flex flex-col gap-3">
          {documents.map((doc) => (
            <li key={doc.id} className="rounded border p-4">
              <div className="flex items-center justify-between gap-4">
                <div className="min-w-0">
                  <p className="truncate font-medium">{doc.filename}</p>
                  <p className="text-xs text-gray-500">{formatBytes(doc.size_bytes)}</p>
                </div>
                <div className="flex shrink-0 items-center gap-3 text-sm">
                  <StatusBadge status={doc.status} />
                  {doc.status === "failed" && (
                    <button onClick={() => handleReprocess(doc.id)} className="underline">
                      Retry
                    </button>
                  )}
                  <button onClick={() => handleDelete(doc.id)} className="text-red-600 underline">
                    Delete
                  </button>
                </div>
              </div>
              {doc.error_message && (
                <p className="mt-2 text-sm text-red-600">{doc.error_message}</p>
              )}
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}