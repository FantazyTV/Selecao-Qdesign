import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: Date | string): string {
  return new Date(date).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function generateProjectHash(): string {
  return Math.random().toString(36).substring(2, 8).toUpperCase();
}

export function getFileType(filename: string): "pdb" | "pdf" | "image" | "sequence" | "text" | "unknown" {
  const ext = filename.split(".").pop()?.toLowerCase();
  if (["pdb", "cif", "mmcif"].includes(ext || "")) return "pdb";
  if (ext === "pdf") return "pdf";
  if (["png", "jpg", "jpeg", "gif", "webp", "svg"].includes(ext || "")) return "image";
  if (["fasta", "fa", "seq"].includes(ext || "")) return "sequence";
  if (["txt", "md", "json"].includes(ext || "")) return "text";
  return "unknown";
}

export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + "...";
}
