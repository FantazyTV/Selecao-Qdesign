"use client";

import React, { useMemo } from "react";
import { FileText, Copy, Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";

interface TextViewerProps {
  content?: string;
  fileUrl?: string;
}

export function TextViewer({ content }: TextViewerProps) {
  const displayData = useMemo(() => {
    if (!content) return { text: "", truncated: false, originalSize: 0 };
    
    const maxSize = 100000; // 100KB limit
    const originalSize = content.length;
    const truncated = originalSize > maxSize;
    const text = truncated ? content.substring(0, maxSize) : content;
    
    return { text, truncated, originalSize };
  }, [content]);

  const copyToClipboard = () => {
    if (content) {
      navigator.clipboard.writeText(content);
    }
  };

  const downloadText = () => {
    if (content) {
      const blob = new Blob([content], { type: "text/plain" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "text-file.txt";
      a.click();
      URL.revokeObjectURL(url);
    }
  };

  if (!content) {
    return (
      <div className="flex h-full items-center justify-center bg-slate-50">
        <div className="text-center">
          <FileText className="mx-auto h-12 w-12 text-slate-300" />
          <p className="mt-2 text-sm text-slate-500">No text content provided</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      {/* Toolbar */}
      <div className="flex items-center justify-between border-b border-slate-100 bg-slate-50 px-3 py-2">
        <div className="text-sm text-slate-600">
          {displayData.truncated ? (
            <>
              Showing first {Math.round(displayData.text.length / 1024)}KB of {Math.round(displayData.originalSize / 1024)}KB
            </>
          ) : (
            <>
              {Math.round(displayData.originalSize / 1024)}KB text file
            </>
          )}
        </div>
        <div className="flex items-center gap-1">
          <Button
            size="sm"
            variant="ghost"
            className="h-7 text-xs"
            onClick={copyToClipboard}
          >
            <Copy className="mr-1 h-3 w-3" />
            Copy
          </Button>
          <Button
            size="sm"
            variant="ghost"
            className="h-7 text-xs"
            onClick={downloadText}
          >
            <Download className="mr-1 h-3 w-3" />
            Download
          </Button>
        </div>
      </div>
      
      {/* Content */}
      <ScrollArea className="flex-1">
        <div className="p-4">
          {displayData.truncated && (
            <div className="mb-4 rounded-md bg-yellow-50 border border-yellow-200 p-3">
              <div className="flex items-center">
                <span className="text-sm text-yellow-800">
                  ⚠️ File too large - showing first 100KB only. Use download to get the full file.
                </span>
              </div>
            </div>
          )}
          <pre className="font-mono text-xs leading-relaxed whitespace-pre-wrap break-all text-slate-700">
            {displayData.text}
          </pre>
        </div>
      </ScrollArea>
    </div>
  );
}

export function TextViewerPlaceholder({ title }: { title?: string }) {
  return (
    <div className="flex h-full flex-col items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="relative">
        <FileText className="h-16 w-16 text-slate-300" />
        <div className="absolute -bottom-1 -right-1 rounded-full bg-blue-500 p-1">
          <span className="text-[8px] font-bold text-white">TXT</span>
        </div>
      </div>
      <h3 className="mt-4 text-lg font-medium text-slate-700">Text Document</h3>
      {title && <p className="text-sm text-slate-500">{title}</p>}
      <p className="mt-2 text-center text-xs text-slate-400">
        View and search text content
        <br />
        Copy or download the file
      </p>
    </div>
  );
}