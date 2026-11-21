import { Suspense } from "react";
import StudySession from "./StudySession";

export default function StudyPage() {
    return (
        <Suspense fallback ={<p className="p-8">Loading...</p>}>
            <StudySession />
        </Suspense>
    );
}