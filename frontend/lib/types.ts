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

export type DocumentStatus = "pending" | "processing" | "ready" | "failed"; 

export type NotebookDocument = {
    id: number;
    notebook_id : number;
    filename: string;
    content_type : string;
    size_bytes : number;
    status : DocumentStatus;
    error_message : string | null;
    created_at : string;
};

export type SearchResult = {
    chunk_id : number;
    document_id: number;
    filename : string;
    page_number : number | null;
    content: string;
    score: number;
};

export type Source = SearchResult & {
    number : number;
    cited: boolean;
};

export type StreamEvent =
| {event: "sources"; data : {sources : Source[]}}
| {event : "delta"; data : {text : string}}
| { event : "done"; data : {cited: number[]; message_id?: number}}
| { event : "error"; data : {message : string}}

export type Conversation {
    id: number;
    title: string;
    created_at: string;
    updated_at: string;
};

export type ChatMessage = {
    id: number;
    role : "user" | "assistant";
    content: string;
    sources: Source[] | null;
    created_at: string;
    status?: "streaming" | "stopped" | "error";
};

export type ConversationDetail = Conversation & {
    messages: ChatMessage[];
};
