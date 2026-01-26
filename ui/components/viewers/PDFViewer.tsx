"use client";

import React, { useState, useMemo } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import { ChevronLeft, ChevronRight, ZoomIn, ZoomOut, Loader2, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

// Set up PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

interface PDFViewerProps {
  content?: string; // Base64 encoded PDF
  fileUrl?: string;
}

export function PDFViewer({ content, fileUrl }: PDFViewerProps) {
  const [numPages, setNumPages] = useState<number>(0);
  const [pageNumber, setPageNumber] = useState<number>(1);
  const [scale, setScale] = useState<number>(1.0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const onDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
    setNumPages(numPages);
    setIsLoading(false);
  };

  const onDocumentLoadError = (error: Error) => {
    setError(error.message || "Failed to load PDF");
    setIsLoading(false);
  };

  const goToPrevPage = () => {
    setPageNumber((prev) => Math.max(prev - 1, 1));
  };

  const goToNextPage = () => {
    setPageNumber((prev) => Math.min(prev + 1, numPages));
  };

  const handlePageInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const page = parseInt(e.target.value);
    if (!isNaN(page) && page >= 1 && page <= numPages) {
      setPageNumber(page);
    }
  };

  const zoomIn = () => {
    setScale((prev) => Math.min(prev + 0.2, 3));
  };

  const zoomOut = () => {
    setScale((prev) => Math.max(prev - 0.2, 0.5));
  };

  const pdfSource = useMemo(() => {
    return content
      ? { data: atob(content) }
      : fileUrl
      ? { url: fileUrl }
      : null;
  }, [content, fileUrl]);

  if (!pdfSource) {
    return (
      <div className="flex h-full items-center justify-center bg-slate-50">
        <div className="text-center">
          <FileText className="mx-auto h-12 w-12 text-slate-300" />
          <p className="mt-2 text-sm text-slate-500">No PDF data provided</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-full items-center justify-center bg-slate-50">
        <div className="text-center">
          <FileText className="mx-auto h-12 w-12 text-slate-300" />
          <p className="mt-2 text-sm text-slate-500">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      {/* Toolbar */}
      <div className="flex items-center justify-between border-b border-slate-100 bg-slate-50 px-3 py-2">
        <div className="flex items-center gap-2">
          <Button
            size="icon"
            variant="ghost"
            className="h-7 w-7"
            onClick={goToPrevPage}
            disabled={pageNumber <= 1}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <div className="flex items-center gap-1 text-sm">
            <Input
              type="number"
              value={pageNumber}
              onChange={handlePageInputChange}
              className="h-7 w-12 text-center text-xs"
              min={1}
              max={numPages}
            />
            <span className="text-slate-500">/ {numPages}</span>
          </div>
          <Button
            size="icon"
            variant="ghost"
            className="h-7 w-7"
            onClick={goToNextPage}
            disabled={pageNumber >= numPages}
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
        
        <div className="flex items-center gap-1">
          <Button size="icon" variant="ghost" className="h-7 w-7" onClick={zoomOut}>
            <ZoomOut className="h-3.5 w-3.5" />
          </Button>
          <span className="w-12 text-center text-xs text-slate-500">
            {Math.round(scale * 100)}%
          </span>
          <Button size="icon" variant="ghost" className="h-7 w-7" onClick={zoomIn}>
            <ZoomIn className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>
      
      {/* PDF Content */}
      <div className="flex-1 overflow-auto bg-slate-100 p-4">
        <div className="flex justify-center">
          <Document
            file={pdfSource}
            onLoadSuccess={onDocumentLoadSuccess}
            onLoadError={onDocumentLoadError}
            loading={
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
              </div>
            }
          >
            <Page
              pageNumber={pageNumber}
              scale={scale}
              className="shadow-lg"
              renderTextLayer={false}
              renderAnnotationLayer={false}
              loading={
                <div className="flex h-[600px] w-[450px] items-center justify-center bg-white">
                  <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
                </div>
              }
            />
          </Document>
        </div>
      </div>
    </div>
  );
}

// Placeholder component for PDF preview
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
