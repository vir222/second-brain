"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import NotebookForm from "@/components/NotebookForm";
import NotebookItem from "@/components/NotebookItem";
import { apiFetch, ApiError } from "@/lib/api";
import { clearToken, getToken } from "@/lib/auth";
import type { Notebook, NotebookChanges, User } from "@/lib/types";

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [notebooks, setNotebooks] = useState<Notebook[]>([]);
  const [showArchived, setShowArchived] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }

    Promise.all([
      apiFetch<User>("/users/me"),
      apiFetch<Notebook[]>(`/notebooks?include_archived=${showArchived}`),
    ])
      .then(([me, list]) => {
        setUser(me);
        setNotebooks(list);
      })
      .catch((err) => {
        if (err instanceof ApiError && err.status === 401) {
          clearToken();
          router.replace("/login");
        } else {
          setLoadError(err instanceof Error ? err.message : "Something went wrong");
        }
      });
  }, [router, showArchived]);

  function handleActionError(err: unknown) {
    if (err instanceof ApiError && err.status === 401) {
      clearToken();
      router.replace("/login");
      return;
    }
    setActionError(err instanceof Error ? err.message : "Something went wrong");
  }

  async function handleCreate(title: string, description: string) {
    const created = await apiFetch<Notebook>("/notebooks", {
      method: "POST",
      body: JSON.stringify({ title, description: description.trim() || null }),
    });
    setNotebooks((prev) => [created, ...prev]);
  }

  async function handleUpdate(id: number, changes: NotebookChanges) {
    setActionError(null);
    try {
      const updated = await apiFetch<Notebook>(`/notebooks/${id}`, {
        method: "PATCH",
        body: JSON.stringify(changes),
      });
      setNotebooks((prev) => {
        if (updated.is_archived && !showArchived) {
          return prev.filter((n) => n.id !== id);
        }
        return prev.map((n) => (n.id === id ? updated : n));
      });
    } catch (err) {
      handleActionError(err);
    }
  }

  async function handleDelete(id: number) {
    if (!window.confirm("Delete this notebook? This can't be undone.")) return;
    setActionError(null);
    try {
      await apiFetch(`/notebooks/${id}`, { method: "DELETE" });
      setNotebooks((prev) => prev.filter((n) => n.id !== id));
    } catch (err) {
      handleActionError(err);
    }
  }

  function handleLogout() {
    clearToken();
    router.push("/login");
  }

  if (loadError) return <p className="p-8 text-red-600">{loadError}</p>;
  if (!user) return <p className="p-8">Loading...</p>;

  return (
    <main className="mx-auto mt-12 max-w-2xl px-4 pb-12">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Your notebooks</h1>
        <button onClick={handleLogout} className="text-sm underline">
          Log out
        </button>
      </div>
      <p className="mt-2 text-sm text-gray-500">Logged in as {user.email}</p>

      <NotebookForm onCreate={handleCreate} />

      <div className="mt-8 flex items-center justify-between">
        <h2 className="text-lg font-semibold">Notebooks ({notebooks.length})</h2>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={showArchived}
            onChange={(e) => setShowArchived(e.target.checked)}
          />
          Show archived
        </label>
      </div>

      {actionError && <p className="mt-4 text-sm text-red-600">{actionError}</p>}

      {notebooks.length === 0 ? (
        <p className="mt-4 text-sm text-gray-500">No notebooks yet. Create your first one above.</p>
      ) : (
        <ul className="mt-4 flex flex-col gap-3">
          {notebooks.map((notebook) => (
            <NotebookItem
              key={notebook.id}
              notebook={notebook}
              onUpdate={handleUpdate}
              onDelete={handleDelete}
            />
          ))}
        </ul>
      )}
    </main>
  );
}