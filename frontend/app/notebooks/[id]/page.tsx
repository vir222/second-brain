import {Suspense} from "react";
import NotebookView from "./NotebookView";

export default function NotebookPage() {
    return (
        <Suspense fallback = {<p className="p-8">Loading...</p>}>
            <NotebookView />
        </Suspense>
    );
}