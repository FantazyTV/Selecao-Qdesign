export { FloatingWindow } from "./FloatingWindow";
export { PDBViewer, PDBViewerPlaceholder } from "./PDBViewer";
export { ImageViewer, ImageViewerPlaceholder } from "./ImageViewer";
export { SequenceViewer, SequenceViewerPlaceholder } from "./SequenceViewer";

// Dynamic import for PDFViewer to avoid SSR issues with PDF.js (DOMMatrix not defined)
// We cannot import anything from PDFViewer.tsx statically as it triggers the SSR error
import dynamic from "next/dynamic";
import { FileText } from "lucide-react";

export const PDFViewer = dynamic(
  () => import("./PDFViewer").then((mod) => mod.PDFViewer),
  { 
    ssr: false,
    loading: () => (
      <div className="flex h-full items-center justify-center bg-slate-50">
        <div className="animate-pulse text-slate-400">Loading PDF viewer...</div>
      </div>
    )
  }
);

// Inline placeholder to avoid importing from PDFViewer.tsx
export function PDFViewerPlaceholder({ title }: { title?: string }) {
  return (
    <div className="flex h-full flex-col items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="relative">
        <FileText className="h-16 w-16 text-slate-300" />
        <div className="absolute -bottom-1 -right-1 rounded-full bg-red-500 p-1">
          <span className="text-[8px] font-bold text-white">PDF</span>
        </div>
      </div>
      <h3 className="mt-4 text-lg font-medium text-slate-700">PDF Document</h3>
      {title && <p className="text-sm text-slate-500">{title}</p>}
      <p className="mt-2 text-center text-xs text-slate-400">
        View and navigate through pages
        <br />
        Zoom and search content
      </p>
    </div>
  );
}
