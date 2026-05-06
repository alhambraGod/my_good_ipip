"use client";

import { useParams, useRouter } from "next/navigation";
import { getReportPdfUrl } from "@/lib/api";

export default function PdfPreviewPage() {
  const params = useParams();
  const router = useRouter();
  const assessmentId = params.id as string;
  const pdfUrl = getReportPdfUrl(assessmentId);

  return (
    <main className="min-h-screen bg-slate-900 flex flex-col">
      {/* Top bar */}
      <div className="bg-slate-800 border-b border-slate-700 px-4 py-3 flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.back()}
            className="text-slate-400 hover:text-white transition-colors text-sm flex items-center gap-1"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back
          </button>
          <div className="h-5 w-px bg-slate-700" />
          <h1 className="text-white font-semibold text-sm">
            MindPrism Report Preview
          </h1>
        </div>
        <a
          href={pdfUrl}
          download
          className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm px-5 py-2 rounded-lg transition-colors flex items-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          Download PDF
        </a>
      </div>

      {/* PDF embed */}
      <div className="flex-1 flex items-center justify-center p-4">
        <iframe
          src={pdfUrl}
          className="w-full max-w-4xl h-[calc(100vh-80px)] rounded-lg shadow-2xl bg-white"
          title="MindPrism Report PDF Preview"
        />
      </div>
    </main>
  );
}
