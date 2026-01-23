"use client";

import React, { useMemo } from "react";
import { FileCode, Copy, Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";

interface SequenceViewerProps {
  content?: string;
  fileUrl?: string;
  format?: "fasta" | "raw";
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

function parseFasta(content: string): ParsedSequence[] {
  const sequences: ParsedSequence[] = [];
  const lines = content.split("\n");
  let currentSeq: ParsedSequence | null = null;
  
  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith(">")) {
      if (currentSeq) {
        sequences.push(currentSeq);
      }
      const headerParts = trimmed.substring(1).split(" ");
      currentSeq = {
        id: headerParts[0] || "Unknown",
        description: headerParts.slice(1).join(" "),
        sequence: "",
      };
    } else if (currentSeq && trimmed) {
      currentSeq.sequence += trimmed;
    }
  }
  
  if (currentSeq) {
    sequences.push(currentSeq);
  }
  
  return sequences;
}

export function SequenceViewer({ content, format = "fasta" }: SequenceViewerProps) {
  const sequences = useMemo(() => {
    if (!content) return [];
    if (format === "fasta") {
      return parseFasta(content);
    }
    return [{ id: "Sequence", description: "", sequence: content }];
  }, [content, format]);

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

  if (!content || sequences.length === 0) {
    return (
      <div className="flex h-full items-center justify-center bg-slate-50">
        <div className="text-center">
          <FileCode className="mx-auto h-12 w-12 text-slate-300" />
          <p className="mt-2 text-sm text-slate-500">No sequence data provided</p>
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
                  {seq.sequence.length} aa
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
