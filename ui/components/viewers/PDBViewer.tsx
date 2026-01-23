"use client";

import React, { useEffect, useRef, useState } from "react";
import { Loader2, RotateCw, ZoomIn, ZoomOut, Box, Layers } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface PDBViewerProps {
  content?: string;
  fileUrl?: string;
  pdbId?: string;
}

type RepresentationType = "cartoon" | "ball+stick" | "surface" | "ribbon" | "spacefill";

export function PDBViewer({ content, fileUrl, pdbId }: PDBViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const stageRef = useRef<unknown>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [representation, setRepresentation] = useState<RepresentationType>("cartoon");
  const [colorScheme, setColorScheme] = useState("chainid");

  useEffect(() => {
    let isMounted = true;
    
    const loadNGL = async () => {
      try {
        // Dynamically import NGL
        const NGL = await import("ngl");
        
        if (!containerRef.current || !isMounted) return;
        
        // Clear any existing stage
        if (stageRef.current) {
          (stageRef.current as { dispose: () => void }).dispose();
        }
        
        // Create new stage
        const stage = new NGL.Stage(containerRef.current, {
          backgroundColor: "white",
        });
        stageRef.current = stage;
        
        // Handle resize
        const handleResize = () => {
          stage.handleResize();
        };
        window.addEventListener("resize", handleResize);
        
        // Load structure
        let loadPromise;
        if (content) {
          // Load from content string
          const blob = new Blob([content], { type: "text/plain" });
          loadPromise = stage.loadFile(blob, { ext: "pdb" });
        } else if (fileUrl) {
          loadPromise = stage.loadFile(fileUrl);
        } else if (pdbId) {
          loadPromise = stage.loadFile(`rcsb://${pdbId.toUpperCase()}`);
        } else {
          setError("No structure data provided");
          setIsLoading(false);
          return;
        }
        
        loadPromise.then((component: unknown) => {
          if (!isMounted) return;
          const comp = component as { addRepresentation: (type: string, params: object) => void; autoView: () => void };
          comp.addRepresentation(representation, { colorScheme });
          comp.autoView();
          setIsLoading(false);
        }).catch((err: Error) => {
          if (!isMounted) return;
          setError(err.message || "Failed to load structure");
          setIsLoading(false);
        });
        
        return () => {
          window.removeEventListener("resize", handleResize);
        };
      } catch (err) {
        if (!isMounted) return;
        setError("Failed to initialize 3D viewer");
        setIsLoading(false);
      }
    };
    
    loadNGL();
    
    return () => {
      isMounted = false;
      if (stageRef.current) {
        (stageRef.current as { dispose: () => void }).dispose();
      }
    };
  }, [content, fileUrl, pdbId]);

  // Update representation when changed
  useEffect(() => {
    if (stageRef.current) {
      const stage = stageRef.current as { 
        eachComponent: (callback: (comp: { 
          removeAllRepresentations: () => void; 
          addRepresentation: (type: string, params: object) => void;
        }) => void) => void 
      };
      stage.eachComponent((comp) => {
        comp.removeAllRepresentations();
        comp.addRepresentation(representation, { colorScheme });
      });
    }
  }, [representation, colorScheme]);

  const handleZoomIn = () => {
    if (stageRef.current) {
      const stage = stageRef.current as { viewer: { camera: { position: { z: number } }; requestRender: () => void } };
      stage.viewer.camera.position.z *= 0.8;
      stage.viewer.requestRender();
    }
  };

  const handleZoomOut = () => {
    if (stageRef.current) {
      const stage = stageRef.current as { viewer: { camera: { position: { z: number } }; requestRender: () => void } };
      stage.viewer.camera.position.z *= 1.2;
      stage.viewer.requestRender();
    }
  };

  const handleReset = () => {
    if (stageRef.current) {
      const stage = stageRef.current as { autoView: () => void };
      stage.autoView();
    }
  };

  if (error) {
    return (
      <div className="flex h-full items-center justify-center bg-slate-50">
        <div className="text-center">
          <Box className="mx-auto h-12 w-12 text-slate-300" />
          <p className="mt-2 text-sm text-slate-500">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      {/* Toolbar */}
      <div className="flex items-center gap-2 border-b border-slate-100 bg-slate-50 px-3 py-2">
        <Select value={representation} onValueChange={(v) => setRepresentation(v as RepresentationType)}>
          <SelectTrigger className="h-7 w-[120px] text-xs">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="cartoon">Cartoon</SelectItem>
            <SelectItem value="ball+stick">Ball & Stick</SelectItem>
            <SelectItem value="surface">Surface</SelectItem>
            <SelectItem value="ribbon">Ribbon</SelectItem>
            <SelectItem value="spacefill">Spacefill</SelectItem>
          </SelectContent>
        </Select>
        
        <Select value={colorScheme} onValueChange={setColorScheme}>
          <SelectTrigger className="h-7 w-[100px] text-xs">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="chainid">Chain</SelectItem>
            <SelectItem value="residueindex">Residue</SelectItem>
            <SelectItem value="element">Element</SelectItem>
            <SelectItem value="bfactor">B-Factor</SelectItem>
            <SelectItem value="sstruc">Secondary</SelectItem>
          </SelectContent>
        </Select>
        
        <div className="ml-auto flex items-center gap-1">
          <Button size="icon" variant="ghost" className="h-7 w-7" onClick={handleZoomIn}>
            <ZoomIn className="h-3.5 w-3.5" />
          </Button>
          <Button size="icon" variant="ghost" className="h-7 w-7" onClick={handleZoomOut}>
            <ZoomOut className="h-3.5 w-3.5" />
          </Button>
          <Button size="icon" variant="ghost" className="h-7 w-7" onClick={handleReset}>
            <RotateCw className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>
      
      {/* Viewer */}
      <div className="relative flex-1">
        {isLoading && (
          <div className="absolute inset-0 z-10 flex items-center justify-center bg-white/80">
            <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
          </div>
        )}
        <div ref={containerRef} className="h-full w-full" />
      </div>
    </div>
  );
}

// Placeholder component when NGL is not available
export function PDBViewerPlaceholder({ pdbId }: { pdbId?: string }) {
  return (
    <div className="flex h-full flex-col items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="relative">
        <Layers className="h-16 w-16 text-slate-300" />
        <div className="absolute -bottom-1 -right-1 rounded-full bg-emerald-500 p-1">
          <Box className="h-4 w-4 text-white" />
        </div>
      </div>
      <h3 className="mt-4 text-lg font-medium text-slate-700">3D Structure</h3>
      {pdbId && <p className="text-sm text-slate-500">PDB: {pdbId}</p>}
      <p className="mt-2 text-center text-xs text-slate-400">
        Interactive 3D molecular visualization
        <br />
        Rotate, zoom, and explore the structure
      </p>
    </div>
  );
}
