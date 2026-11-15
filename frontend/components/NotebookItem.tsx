"use client";

import { useState, type SyntheticEvent } from "react";
import type { Notebook, NotebookChanges} from "@/lib/types";

type NoteBookItemProps = {
    notebook : Notebook;
    onUpdate: (id: number, changes: NotebookChanges) => Promise<void>;
    onDelete: (id: number) => Promise<void>;
};

export default function NotebookItem({ notebook, onUpdate, onDelete}: NoteBookItemProps) {
    const [editing, setEditing] = useState(false);
    const [title, setTitle] = useState(notebook.title);
    async function handleRename(e: SyntheticEvent<HTMLFormElement>) {
        e.preventDefault()
        const trimmed = title.trim()
        if(!trimmed || trimmed == notebook.title) {
            cancelEdit();
            return;
        }
        await onUpdate(notebook.id, {title: trimmed});
        setEditing(false);
    }

    function cancelEdit() {
        setTitle(notebook.title);
        setEditing(false);
    }
    
    return (
        <li className="flex items-center justify-between gap-4 rounded border p-4">
            <div className="min-w-0 flex-1">
                {editing ? (
                <form onSubmit={handleRename} className="flex gap-2">
                    <input
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        autoFocus
                        maxLength={200}
                        className="flex-1 rounded border px-2 py-1"
                    />
                    <button type="submit" className="text-sm underline">Save</button>
                    <button type="button" onClick={cancelEdit} className="text-sm underline">
                        Cancel
                    </button>
                </form>
            ) : (
                <>
                    <h3 className="truncate font-medium">
                        {notebook.title}
                        {notebook.is_archived && (
                            <span className="ml-2 text-xs text-gray-500">(archived)</span>
                        )}
                    </h3>
                    {notebook.description && (
                        <p className="text-sm text-gray-600">{notebook.description}</p>
                    )}
                </>
                )}
            </div>

            {!editing && (
                <div className="flex shrink-0 gap-3 text-sm">
                    <button onClick={() => setEditing(true)} className="underline">
                        Rename
                    </button>
                    <button
                        onClick={() => onUpdate(notebook.id, { is_archived: !notebook.is_archived })}
                        className="underline"
                    >
                        {notebook.is_archived ? "Unarchive" : "Archive"}
                    </button>
                    <button onClick={() => onDelete(notebook.id)} className="text-red-600 underline">
                        Delete
                    </button>
                </div>
            )}
        </li>
    );
}