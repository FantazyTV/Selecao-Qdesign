"use client";

import React, { useState } from "react";
import Image from "next/image";
import { ZoomIn, ZoomOut, RotateCw, Maximize2, ImageIcon } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ImageViewerProps {
  content?: string; // Base64 encoded image
  fileUrl?: string;
  alt?: string;
}

export function ImageViewer({ content, fileUrl, alt = "Image" }: ImageViewerProps) {
  const [scale, setScale] = useState(1);
  const [rotation, setRotation] = useState(0);
  const [isFullscreen, setIsFullscreen] = useState(false);

  const imageSrc = content ? (content.startsWith('data:') ? content : `data:image/png;base64,${content}`) : fileUrl || "";

  const zoomIn = () => {
    setScale((prev) => Math.min(prev + 0.25, 4));
  };

  const zoomOut = () => {
    setScale((prev) => Math.max(prev - 0.25, 0.25));
  };

  const rotate = () => {
    setRotation((prev) => (prev + 90) % 360);
  };

  const toggleFullscreen = () => {
    setIsFullscreen((prev) => !prev);
  };

  const resetView = () => {
    setScale(1);
    setRotation(0);
  };

  if (!imageSrc) {
    return (
      <div className="flex h-full items-center justify-center bg-slate-50">
        <div className="text-center">
          <ImageIcon className="mx-auto h-12 w-12 text-slate-300" />
          <p className="mt-2 text-sm text-slate-500">No image data provided</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      {/* Toolbar */}
      <div className="flex items-center justify-between border-b border-slate-100 bg-slate-50 px-3 py-2">
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
        
        <div className="flex items-center gap-1">
          <Button size="icon" variant="ghost" className="h-7 w-7" onClick={rotate}>
            <RotateCw className="h-3.5 w-3.5" />
          </Button>
          <Button size="icon" variant="ghost" className="h-7 w-7" onClick={toggleFullscreen}>
            <Maximize2 className="h-3.5 w-3.5" />
          </Button>
          <Button size="sm" variant="ghost" className="h-7 text-xs" onClick={resetView}>
            Reset
          </Button>
        </div>
      </div>
      
      {/* Image Content */}
      <div className="flex-1 overflow-auto bg-slate-100">
        <div className="flex min-h-full items-center justify-center p-4">
          <div
            className="transition-transform duration-200"
            style={{
              transform: `scale(${scale}) rotate(${rotation}deg)`,
            }}
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={imageSrc}
              alt={alt}
              className="max-w-none rounded shadow-lg"
              style={{ maxHeight: isFullscreen ? "90vh" : "auto" }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

// Placeholder component
export function ImageViewerPlaceholder({ title }: { title?: string }) {
  return (
    <div className="flex h-full flex-col items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="relative">
        <ImageIcon className="h-16 w-16 text-slate-300" />
        <div className="absolute -bottom-1 -right-1 rounded-full bg-blue-500 p-1">
          <span className="text-[8px] font-bold text-white">IMG</span>
        </div>
      </div>
      <h3 className="mt-4 text-lg font-medium text-slate-700">Image</h3>
      {title && <p className="text-sm text-slate-500">{title}</p>}
      <p className="mt-2 text-center text-xs text-slate-400">
        Zoom, rotate, and inspect
        <br />
        High-resolution image viewer
      </p>
    </div>
  );
}
