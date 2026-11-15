export type User = {
  id: number;
  email: string;
  created_at: string;
};

export type Token = {
    access_token: string;
    token_type: string;
};

export type Notebook = {
    id: number;
    title: string;
    description: string;
    is_archived: boolean;
    created_at: string;
    updated_at: string;
};

export type NotebookChanges = {
    title?: string;
    description?: string | null;
    is_archived?: boolean;
}