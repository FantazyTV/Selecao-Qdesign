"use client";

import React, { useMemo, useState } from "react";
import { FileCode, Copy, Download, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";

interface SequenceViewerProps {
  content?: string;
  fileUrl?: string;
}

// Amino acid color scheme (based on physicochemical properties)
const AA_COLORS: Record<string, string> = {
  // Hydrophobic (yellows/oranges)
  A: "#FFD700", L: "#FFA500", I: "#FF8C00", V: "#FF7F00", M: "#FF6347",
  F: "#FF4500", W: "#FF0000", P: "#FFB6C1",
  // Polar (greens)
  S: "#98FB98", T: "#90EE90", N: "#32CD32", Q: "#228B22",
  // Acidic (reds)
  D: "#DC143C", E: "#B22222",
  // Basic (blues)
  K: "#4169E1", R: "#0000FF", H: "#6495ED",
  // Special
  C: "#FFD700", G: "#DCDCDC", Y: "#9ACD32",
};

interface ParsedSequence {
  id: string;
  description: string;
  sequence: string;
}

function parseFastaOrPlain(content: string, maxSequences: number = 50): ParsedSequence[] {
  // If content contains no '>' header, treat as a single plain sequence
  if (!content.trim().startsWith('>')) {
    return [{
      id: 'Sequence',
      description: '',
      sequence: content.replace(/\s+/g, ''), // remove whitespace
    }];
  }
  // Otherwise, parse as FASTA
  const sequences: ParsedSequence[] = [];
  const lines = content.split("\n");
  let currentSeq: ParsedSequence | null = null;
  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith(">")) {
      if (currentSeq) {
        sequences.push(currentSeq);
        if (sequences.length >= maxSequences) break;
      }
      const headerParts = trimmed.substring(1).split(" ");
      currentSeq = {
        id: headerParts[0] || "Unknown",
        description: headerParts.slice(1).join(" "),
        sequence: "",
      };
    } else if (currentSeq && trimmed) {
      // Limit individual sequence length to prevent memory issues
      if (currentSeq.sequence.length < 5000) {
        currentSeq.sequence += trimmed;
      } else if (!currentSeq.sequence.endsWith("...")) {
        currentSeq.sequence += "...";
      }
    }
  }
  if (currentSeq && sequences.length < maxSequences) {
    sequences.push(currentSeq);
  }
  return sequences;
}

export function SequenceViewer({ content }: SequenceViewerProps) {
  const [isProcessing, setIsProcessing] = useState(false);
  
  const sequences = useMemo(() => {
    if (!content) return [];
    
    // Early size check to prevent crashes
    if (content.length > 300000000) { // 300MB limit
      return [{ 
        id: "⚠️ File Too Large", 
        description: `File size: ${Math.round(content.length / (1024*1024))}MB - too large to display safely. Use download to access the full file.`, 
        sequence: "" 
      }];
    }
    
    // Show processing indicator for large files
    if (content.length > 10000000) { // 10MB+
      setIsProcessing(true);
      // Use setTimeout to allow UI to update before processing
      setTimeout(() => setIsProcessing(false), 500); // Longer timeout for large files
    }
    
    const maxContentLength = 50000000; // 50MB limit for processing
    const truncated = content.length > maxContentLength;
    const displayContent = truncated ? content.substring(0, maxContentLength) : content;
    
    const parsed = parseFastaOrPlain(displayContent, 50); // Show first 50 sequences or plain
    if (truncated) {
      parsed.push({ 
        id: "⚠️ File Truncated", 
        description: `Original file: ${Math.round(content.length / (1024*1024))}MB, showing first 50MB only`, 
        sequence: "" 
      });
    }
    return parsed;
  }, [content]);

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const downloadFasta = () => {
    const blob = new Blob([content || ""], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "sequence.fasta";
    a.click();
    URL.revokeObjectURL(url);
  };

  if (!content) {
    return (
      <div className="flex h-full items-center justify-center bg-slate-50">
        <div className="text-center">
          <FileCode className="mx-auto h-12 w-12 text-slate-300" />
          <p className="mt-2 text-sm text-slate-500">No content provided</p>
        </div>
      </div>
    );
  }

  if (sequences.length === 0) {
    return (
      <div className="flex h-full items-center justify-center bg-slate-50">
        <div className="text-center">
          <FileCode className="mx-auto h-12 w-12 text-slate-300" />
          <p className="mt-2 text-sm text-slate-500">Unable to parse content</p>
          <p className="mt-1 text-xs text-slate-400">Content length: {content.length} chars</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      {/* Toolbar */}
      <div className="flex items-center justify-between border-b border-slate-100 bg-slate-50 px-3 py-2">
        <div className="text-sm text-slate-600">
          {sequences.length} sequence{sequences.length !== 1 ? "s" : ""}
        </div>
        <div className="flex items-center gap-1">
          <Button
            size="sm"
            variant="ghost"
            className="h-7 text-xs"
            onClick={() => copyToClipboard(content || "")}
          >
            <Copy className="mr-1 h-3 w-3" />
            Copy
          </Button>
          <Button
            size="sm"
            variant="ghost"
            className="h-7 text-xs"
            onClick={downloadFasta}
          >
            <Download className="mr-1 h-3 w-3" />
            Download
          </Button>
        </div>
      </div>
      
      {/* Sequences */}
      <ScrollArea className="flex-1">
        {isProcessing && (
          <div className="flex items-center justify-center py-8">
            <div className="text-center">
              <Loader2 className="h-8 w-8 animate-spin text-slate-600 mx-auto" />
              <p className="mt-2 text-sm text-slate-600">Processing large FASTA file...</p>
            </div>
          </div>
        )}
        <div className="p-4 space-y-6">
          {sequences.map((seq, idx) => (
            <div key={idx} className="space-y-2">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-mono text-sm font-semibold text-slate-800">
                    {seq.id}
                  </h4>
                  {seq.description && (
                    <p className="text-xs text-slate-500">{seq.description}</p>
                  )}
                </div>
                <span className="text-xs text-slate-400">
                  {seq.sequence ? `${seq.sequence.length} aa` : 'No sequence'}
                </span>
              </div>
              
              <div className="rounded-md bg-slate-50 p-3">
                <div className="font-mono text-xs leading-6 break-all">
                  {seq.sequence.split("").map((aa, i) => (
                    <span
                      key={i}
                      className="inline-block rounded px-0.5"
                      style={{
                        backgroundColor: AA_COLORS[aa.toUpperCase()] || "#EEEEEE",
                      }}
                      title={`Position ${i + 1}: ${aa}`}
                    >
                      {aa}
                    </span>
                  ))}
                </div>
              </div>
              
              {/* Position ruler */}
              <div className="font-mono text-[10px] text-slate-400 overflow-x-auto">
                  {Array.from({ length: Math.ceil(seq.sequence.length / 10) }).map(
                    (_, i) => (
                      <span key={i} className="inline-block w-[70px]">
                        {(i + 1) * 10}
                      </span>
                    )
                  )}
                </div>
            </div>
          ))}
        </div>
      </ScrollArea>
      
      {/* Legend */}
      <div className="border-t border-slate-100 bg-slate-50 px-3 py-2">
        <div className="flex flex-wrap gap-2 text-[10px]">
          <span className="text-slate-500">Colors:</span>
          <span className="flex items-center gap-1">
            <span className="h-3 w-3 rounded" style={{ backgroundColor: "#FFD700" }} />
            Hydrophobic
          </span>
          <span className="flex items-center gap-1">
            <span className="h-3 w-3 rounded" style={{ backgroundColor: "#98FB98" }} />
            Polar
          </span>
          <span className="flex items-center gap-1">
            <span className="h-3 w-3 rounded" style={{ backgroundColor: "#DC143C" }} />
            Acidic
          </span>
          <span className="flex items-center gap-1">
            <span className="h-3 w-3 rounded" style={{ backgroundColor: "#4169E1" }} />
            Basic
          </span>
        </div>
      </div>
    </div>
  );
}

// Placeholder
export function SequenceViewerPlaceholder({ title }: { title?: string }) {
  return (
    <div className="flex h-full flex-col items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="relative">
        <FileCode className="h-16 w-16 text-slate-300" />
        <div className="absolute -bottom-1 -right-1 rounded-full bg-purple-500 p-1">
          <span className="text-[8px] font-bold text-white">SEQ</span>
        </div>
      </div>
      <h3 className="mt-4 text-lg font-medium text-slate-700">Sequence</h3>
      {title && <p className="text-sm text-slate-500">{title}</p>}
      <p className="mt-2 text-center text-xs text-slate-400">
        Color-coded amino acids
        <br />
        FASTA format support
      </p>
    </div>
  );
}
