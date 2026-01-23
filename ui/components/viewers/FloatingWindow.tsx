"use client";

import React, { useEffect, useRef, useState } from "react";
import { X, Minimize2, Maximize2, Move } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

interface FloatingWindowProps {
  id: string;
  title: string;
  children: React.ReactNode;
  position: { x: number; y: number };
  size: { width: number; height: number };
  minimized?: boolean;
  onClose: () => void;
  onPositionChange: (position: { x: number; y: number }) => void;
  onSizeChange: (size: { width: number; height: number }) => void;
  onMinimize: () => void;
  onRestore: () => void;
  className?: string;
}

export function FloatingWindow({
  id,
  title,
  children,
  position,
  size,
  minimized = false,
  onClose,
  onPositionChange,
  onSizeChange,
  onMinimize,
  onRestore,
  className,
}: FloatingWindowProps) {
  const windowRef = useRef<HTMLDivElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isResizing, setIsResizing] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (isDragging) {
        onPositionChange({
          x: e.clientX - dragOffset.x,
          y: e.clientY - dragOffset.y,
        });
      }
      if (isResizing && windowRef.current) {
        const rect = windowRef.current.getBoundingClientRect();
        onSizeChange({
          width: Math.max(300, e.clientX - rect.left),
          height: Math.max(200, e.clientY - rect.top),
        });
      }
    };

    const handleMouseUp = () => {
      setIsDragging(false);
      setIsResizing(false);
    };

    if (isDragging || isResizing) {
      document.addEventListener("mousemove", handleMouseMove);
      document.addEventListener("mouseup", handleMouseUp);
    }

    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
    };
  }, [isDragging, isResizing, dragOffset, onPositionChange, onSizeChange]);

  const handleDragStart = (e: React.MouseEvent) => {
    if (windowRef.current) {
      const rect = windowRef.current.getBoundingClientRect();
      setDragOffset({
        x: e.clientX - rect.left,
        y: e.clientY - rect.top,
      });
      setIsDragging(true);
    }
  };

  if (minimized) {
    return (
      <div
        className="fixed bottom-4 right-4 z-50 flex items-center gap-2 rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 shadow-lg"
        style={{ right: `${4 + parseInt(id) * 150}px` }}
      >
        <span className="text-sm font-medium truncate max-w-[100px] text-green-100">{title}</span>
        <Button size="icon" variant="ghost" className="h-6 w-6 text-gray-400 hover:bg-gray-800" onClick={onRestore}>
          <Maximize2 className="h-3 w-3" />
        </Button>
        <Button size="icon" variant="ghost" className="h-6 w-6 text-gray-400 hover:bg-gray-800" onClick={onClose}>
          <X className="h-3 w-3" />
        </Button>
      </div>
    );
  }

  return (
    <div
      ref={windowRef}
      className={cn(
        "fixed z-50 flex flex-col rounded-lg border border-gray-700 bg-gray-900 shadow-xl overflow-hidden",
        isDragging && "cursor-grabbing",
        className
      )}
      style={{
        left: position.x,
        top: position.y,
        width: size.width,
        height: size.height,
      }}
    >
      {/* Header */}
      <div
        className="flex items-center justify-between border-b border-gray-800 bg-gray-800 px-3 py-2 cursor-grab active:cursor-grabbing"
        onMouseDown={handleDragStart}
      >
        <div className="flex items-center gap-2">
          <Move className="h-3 w-3 text-gray-500" />
          <span className="text-sm font-medium truncate max-w-[200px] text-green-100">{title}</span>
        </div>
        <div className="flex items-center gap-1">
          <Button size="icon" variant="ghost" className="h-6 w-6 text-gray-400 hover:bg-gray-700" onClick={onMinimize}>
            <Minimize2 className="h-3 w-3" />
          </Button>
          <Button size="icon" variant="ghost" className="h-6 w-6 text-gray-400 hover:bg-gray-700" onClick={onClose}>
            <X className="h-3 w-3" />
          </Button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto bg-gray-950">{children}</div>

      {/* Resize handle */}
      <div
        className="absolute bottom-0 right-0 h-4 w-4 cursor-se-resize"
        onMouseDown={(e) => {
          e.stopPropagation();
          setIsResizing(true);
        }}
      >
        <svg
          className="absolute bottom-1 right-1 h-2 w-2 text-gray-500"
          fill="currentColor"
          viewBox="0 0 8 8"
        >
          <path d="M6 0v2H4v2H2v2H0v2h2V6h2V4h2V2h2V0H6z" />
        </svg>
      </div>
    </div>
  );
}
