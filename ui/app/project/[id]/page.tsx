"use client";

import React, { useEffect, useState, use, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { v4 as uuidv4 } from "uuid";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Home,
  Database,
  Network,
  Brain,
  Save,
  History,
  Users,
  Share2,
  Settings,
  LogOut,
  Copy,
  Check,
  ArrowRight,
  Loader2,
  ChevronDown,
  Download,
  Eye,
  X,
} from "lucide-react";
import { cn, formatDate } from "@/lib/utils";
import { useProjectStore, useAuthStore, useUIStore } from "@/lib/stores";
import { projectsApi } from "@/lib/api";
import { useSocket } from "@/lib/socket";
import type {
  DataPoolItem,
  KnowledgeGraph,
  CoScientistStep,
  Checkpoint,
  SocketEvent,
} from "@/lib/types";
import { DataPool } from "@/components/workspace/DataPool";
import { KnowledgeGraphView } from "@/components/workspace/KnowledgeGraph";
import { CoScientistSidebar } from "@/components/workspace/CoScientistSidebar";
import {
  FloatingWindow,
  TextViewer,
  PDBViewer,
  PDFViewer,
  ImageViewer,
  SequenceViewer,
} from "@/components/viewers";

type ProjectMode = "pool" | "retrieval" | "coscientist";

interface ViewerWindow {
  id: string;
  type: "pdb" | "pdf" | "image" | "sequence" | "text";
  title: string;
  data: string;
  position: { x: number; y: number };
  size: { width: number; height: number };
  minimized: boolean;
}

async function fetchProject(id: string) {
  const response = await projectsApi.get(id);
  console.log(response);
  return response.project;
}

async function updateProject(id: string, data: Partial<any>) {
  const response = await projectsApi.update(id, data);
  return response.project;
}

async function createCheckpoint(
  id: string,
  checkpoint: { name: string; description?: string }
) {
  return projectsApi.createCheckpoint(id, checkpoint);
}

async function runAnalysis(id: string, options?: { feedback?: string; action?: string }): Promise<{ hasMore?: boolean }> {
  // TODO: This endpoint needs to be implemented in the NestJS backend
  // For now, return a mock response
  console.warn("Analysis endpoint not yet implemented in backend");
  return { hasMore: false };
}

function ModeIndicatorMobile({
  mode,
  onChange,
}: {
  mode: ProjectMode;
  onChange: (mode: ProjectMode) => void;
}) {
  const modes: { key: ProjectMode; label: string; icon: React.ReactNode }[] = [
    { key: "pool", label: "Pool", icon: <Database className="h-4 w-4" /> },
    { key: "retrieval", label: "Graph", icon: <Network className="h-4 w-4" /> },
    { key: "coscientist", label: "AI", icon: <Brain className="h-4 w-4" /> },
  ];

  return (
    <div className="flex items-center gap-1">
      {modes.map((m, idx) => (
        <button
          key={m.key}
          className={cn(
            "flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium transition-all",
            mode === m.key
              ? "bg-green-600 text-gray-900 shadow-lg"
              : "bg-gray-800 text-gray-300 hover:bg-gray-700"
          )}
          onClick={() => onChange(m.key)}
        >
          {m.icon}
          <span className="hidden sm:inline">{m.label}</span>
        </button>
      ))}
    </div>
  );
}

function ModeIndicator({
  mode,
  onChange,
}: {
  mode: ProjectMode;
  onChange: (mode: ProjectMode) => void;
}) {
  const modes: { key: ProjectMode; label: string; icon: React.ReactNode }[] = [
    { key: "pool", label: "Data Pool", icon: <Database className="h-4 w-4" /> },
    { key: "retrieval", label: "Knowledge Graph", icon: <Network className="h-4 w-4" /> },
    { key: "coscientist", label: "Co-Scientist", icon: <Brain className="h-4 w-4" /> },
  ];

  return (
    <div className="flex items-center">
      {modes.map((m, idx) => (
        <React.Fragment key={m.key}>
          <button
            className={cn(
              "flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-all",
              mode === m.key
                ? "bg-green-600 text-gray-900 shadow-lg"
                : "bg-gray-800 text-gray-300 hover:bg-gray-700"
            )}
            onClick={() => onChange(m.key)}
          >
            {m.icon}
            {m.label}
          </button>
          {idx < modes.length - 1 && (
            <ArrowRight className="mx-2 h-4 w-4 text-gray-600" />
          )}
        </React.Fragment>
      ))}
    </div>
  );
}

function CheckpointDialog({
  open,
  onOpenChange,
  onSave,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSave: (name: string, description?: string) => void;
}) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  const handleSave = () => {
    onSave(name, description || undefined);
    setName("");
    setDescription("");
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="bg-gray-900 border-gray-800">
        <DialogHeader>
          <DialogTitle className="text-green-100">Save Checkpoint</DialogTitle>
          <DialogDescription className="text-gray-400">
            Create a checkpoint to save the current state of your project.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="checkpoint-name" className="text-gray-300">Name</Label>
            <Input
              id="checkpoint-name"
              placeholder="e.g., After initial analysis..."
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="checkpoint-desc" className="text-gray-300">Description (optional)</Label>
            <Textarea
              id="checkpoint-desc"
              placeholder="What was achieved at this checkpoint..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} className="border-gray-700 text-gray-300 hover:bg-gray-800">
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={!name.trim()}>
            <Save className="mr-2 h-4 w-4" />
            Save Checkpoint
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function CheckpointHistory({
  checkpoints,
  onRestore,
}: {
  checkpoints: Checkpoint[];
  onRestore: (checkpoint: Checkpoint) => void;
}) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <Button variant="outline" size="sm" onClick={() => setOpen(true)} className="border-gray-700 text-gray-300 hover:bg-gray-800">
        <History className="mr-2 h-4 w-4" />
        History ({checkpoints.length})
      </Button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-w-lg bg-gray-900 border-gray-800">
          <DialogHeader>
            <DialogTitle className="text-green-100">Checkpoint History</DialogTitle>
            <DialogDescription className="text-gray-400">
              Restore your project to a previous state
            </DialogDescription>
          </DialogHeader>
          <ScrollArea className="max-h-96">
            <div className="space-y-2">
              {checkpoints.length === 0 ? (
                <p className="py-8 text-center text-sm text-gray-500">
                  No checkpoints saved yet
                </p>
              ) : (
                checkpoints.map((cp) => (
                  <div
                    key={cp._id || cp.id}
                    className="flex items-center justify-between rounded-lg border border-gray-700 p-3"
                  >
                    <div>
                      <h4 className="font-medium text-green-100">{cp.name}</h4>
                      {cp.description && (
                        <p className="text-xs text-gray-400">{cp.description}</p>
                      )}
                      <div className="mt-1 flex items-center gap-2 text-xs text-gray-500">
                        <span>Mode: {cp.mode}</span>
                        <span>•</span>
                        <span>{formatDate(cp.createdAt)}</span>
                      </div>
                    </div>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        onRestore(cp);
                        setOpen(false);
                      }}
                      className="border-gray-700 text-gray-300 hover:bg-gray-800"
                    >
                      Restore
                    </Button>
                  </div>
                ))
              )}
            </div>
          </ScrollArea>
        </DialogContent>
      </Dialog>
    </>
  );
}

function ShareDialog({
  open,
  onOpenChange,
  joinHash,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  joinHash: string;
}) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(joinHash);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="bg-gray-900 border-gray-800">
        <DialogHeader>
          <DialogTitle className="text-green-100">Share Project</DialogTitle>
          <DialogDescription className="text-gray-400">
            Share this code with collaborators to let them join.
          </DialogDescription>
        </DialogHeader>
        <div className="flex items-center gap-2 py-4">
          <Input value={joinHash} readOnly className="font-mono text-green-300" />
          <Button onClick={handleCopy}>
            {copied ? (
              <Check className="h-4 w-4" />
            ) : (
              <Copy className="h-4 w-4" />
            )}
          </Button>
        </div>
        <p className="text-xs text-slate-500">
          Team members can join using this code from the dashboard.
        </p>
      </DialogContent>
    </Dialog>
  );
}

export default function ProjectWorkspace({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = use(params);
  const projectId = resolvedParams.id;
  const router = useRouter();
  const queryClient = useQueryClient();

  const { user, logout, isInitialized, isLoading: authLoading } = useAuthStore();
  const { 
    joinProject, 
    leaveProject, 
    isConnected,
    emit,
    emitPoolAdd,
    emitPoolRemove,
    emitGraphNodeAdd,
    emitGraphNodeUpdate,
    emitGraphNodeRemove,
    emitGraphEdgeAdd,
    emitGraphEdgeRemove,
  } = useSocket();
  const [mode, setMode] = useState<ProjectMode>("pool");
  const [showCheckpointDialog, setShowCheckpointDialog] = useState(false);
  const [showShareDialog, setShowShareDialog] = useState(false);
  const [showCoScientist, setShowCoScientist] = useState(false);
  const [isCoScientistRunning, setIsCoScientistRunning] = useState(false);
  const [viewers, setViewers] = useState<ViewerWindow[]>([]);

  // Fetch project data
  const { data: project, isLoading, error } = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => fetchProject(projectId),
  });

  // Join/leave project room for real-time updates
  useEffect(() => {
    if (isConnected && projectId) {
      joinProject(projectId);
      return () => {
        leaveProject(projectId);
      };
    }
  }, [isConnected, projectId, joinProject, leaveProject]);

  // Refetch project when socket receives updates
  useEffect(() => {
    // Subscribe to project updates via query invalidation
    const handleProjectUpdate = () => {
      queryClient.invalidateQueries({ queryKey: ["project", projectId] });
    };

    // Listen for socket-driven invalidation
    window.addEventListener(`project:${projectId}:update`, handleProjectUpdate);
    return () => {
      window.removeEventListener(`project:${projectId}:update`, handleProjectUpdate);
    };
  }, [projectId, queryClient]);

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: (data: Partial<any>) => updateProject(projectId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["project", projectId] });
    },
  });

  // Checkpoint mutation
  const checkpointMutation = useMutation({
    mutationFn: (data: { name: string; description?: string }) =>
      createCheckpoint(projectId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["project", projectId] });
    },
  });

  // AI Analysis mutation (TODO: implement in backend)
  const analysisMutation = useMutation({
    mutationFn: (options?: { feedback?: string; action?: string }) =>
      runAnalysis(projectId, options),
    onSuccess: (data: { hasMore?: boolean }) => {
      queryClient.invalidateQueries({ queryKey: ["project", projectId] });
      // Continue analysis if there are more steps
      if (data.hasMore && isCoScientistRunning) {
        setTimeout(() => {
          analysisMutation.mutate({ action: "continue" });
        }, 1500); // Small delay between steps for UX
      } else {
        setIsCoScientistRunning(false);
      }
    },
    onError: () => {
      setIsCoScientistRunning(false);
    },
  });

  // Redirect if not authenticated - only after initialization
  useEffect(() => {
    if (isInitialized && !authLoading && !user) {
      router.push("/login");
    }
  }, [user, isInitialized, authLoading, router]);

  // Open viewer window
  const openViewer = (item: DataPoolItem) => {
    const existingViewer = viewers.find(
      (v) => v.data === item.content || v.data === item.fileUrl
    );
    if (existingViewer) return;

    const newViewer: ViewerWindow = {
      id: uuidv4(),
      type: item.type as ViewerWindow["type"],
      title: item.name,
      data: item.content || item.fileUrl || "",
      position: { x: 100 + viewers.length * 30, y: 100 + viewers.length * 30 },
      size: { width: 600, height: 500 },
      minimized: false,
    };
    setViewers([...viewers, newViewer]);
  };

  const closeViewer = useCallback((id: string) => {
    setViewers(viewers.filter((v) => v.id !== id));
  }, [viewers]);

  const updateViewerPosition = useCallback((id: string, position: { x: number; y: number }) => {
    setViewers(viewers.map((v) => (v.id === id ? { ...v, position } : v)));
  }, [viewers]);

  const updateViewerSize = useCallback((id: string, size: { width: number; height: number }) => {
    setViewers(viewers.map((v) => (v.id === id ? { ...v, size } : v)));
  }, [viewers]);

  const minimizeViewer = useCallback((id: string) => {
    setViewers(viewers.map((v) => (v.id === id ? { ...v, minimized: true } : v)));
  }, [viewers]);

  const restoreViewer = useCallback((id: string) => {
    setViewers(viewers.map((v) => (v.id === id ? { ...v, minimized: false } : v)));
  }, [viewers]);

  // Data pool handlers
  const handleAddPoolItem = async (item: Omit<DataPoolItem, "_id" | "addedBy" | "addedAt">) => {
    console.log('[DEBUG] handleAddPoolItem called with:', item);
    console.log('[DEBUG] Item content length:', item.content?.length);
    
    const newItem: DataPoolItem = {
      ...item,
      _id: uuidv4(),
      addedBy: user?.id || "",
      addedAt: new Date().toISOString(),
    };
    
    console.log('[DEBUG] Created new item:', { ...newItem, content: newItem.content?.substring(0, 100) + '...' });
    
    const updatedPool = [...(project?.dataPool || []), newItem];
    console.log('[DEBUG] Updated pool length:', updatedPool.length);
    
    try {
      console.log('[DEBUG] Calling updateMutation.mutate');
      await updateMutation.mutateAsync({ dataPool: updatedPool });
      console.log('[DEBUG] updateMutation completed successfully');
      
      // Emit socket event for real-time sync
      console.log('[DEBUG] Frontend: About to emit pool:add with:', { projectId, newItem });
      emitPoolAdd(projectId, newItem);
      console.log('[DEBUG] Frontend: Emitted pool:add');
    } catch (error) {
      console.error('[DEBUG] updateMutation failed:', error);
      throw error;
    }
  };

  const handleRemovePoolItem = async (id: string) => {
    const updatedPool = (project?.dataPool || []).filter(
      (item: DataPoolItem) => item._id !== id
    );
    updateMutation.mutate({ dataPool: updatedPool });
    // Emit socket event for real-time sync
    console.log('[DEBUG] Frontend: About to emit pool:remove with:', { projectId, id });
    emitPoolRemove(projectId, id);
    console.log('[DEBUG] Frontend: Emitted pool:remove');
  };

  // Knowledge graph handlers
  const handleAddNode = (node: KnowledgeGraph["nodes"][0]) => {
    const updatedGraph = {
      ...project?.knowledgeGraph,
      nodes: [...(project?.knowledgeGraph?.nodes || []), node],
    };
    updateMutation.mutate({ knowledgeGraph: updatedGraph });
    // Emit socket event for real-time sync
    emitGraphNodeAdd(projectId, node);
  };

  const handleUpdateNode = (node: KnowledgeGraph["nodes"][0]) => {
    const updatedNodes = (project?.knowledgeGraph?.nodes || []).map((n: any) =>
      n.id === node.id ? node : n
    );
    updateMutation.mutate({
      knowledgeGraph: { ...project?.knowledgeGraph, nodes: updatedNodes },
    });
    // Emit socket event for real-time sync
    emitGraphNodeUpdate(projectId, node);
  };

  const handleDeleteNode = (nodeId: string) => {
    const updatedNodes = (project?.knowledgeGraph?.nodes || []).filter(
      (n: any) => n.id !== nodeId
    );
    const updatedEdges = (project?.knowledgeGraph?.edges || []).filter(
      (e: any) => e.source !== nodeId && e.target !== nodeId
    );
    updateMutation.mutate({
      knowledgeGraph: { nodes: updatedNodes, edges: updatedEdges },
    });
    // Emit socket event for real-time sync
    emitGraphNodeRemove(projectId, nodeId);
  };

  const handleAddEdge = (edge: KnowledgeGraph["edges"][0]) => {
    const updatedGraph = {
      ...project?.knowledgeGraph,
      edges: [...(project?.knowledgeGraph?.edges || []), edge],
    };
    updateMutation.mutate({ knowledgeGraph: updatedGraph });
    // Emit socket event for real-time sync
    emitGraphEdgeAdd(projectId, edge);
  };

  const handleUpdateEdge = (edge: KnowledgeGraph["edges"][0]) => {
    const updatedEdges = (project?.knowledgeGraph?.edges || []).map((e: any) =>
      e.id === edge.id ? edge : e
    );
    updateMutation.mutate({
      knowledgeGraph: { ...project?.knowledgeGraph, edges: updatedEdges },
    });
  };

  const handleDeleteEdge = (edgeId: string) => {
    const updatedEdges = (project?.knowledgeGraph?.edges || []).filter(
      (e: any) => e.id !== edgeId
    );
    updateMutation.mutate({
      knowledgeGraph: { ...project?.knowledgeGraph, edges: updatedEdges },
    });
    // Emit socket event for real-time sync
    emitGraphEdgeRemove(projectId, edgeId);
  };

  // Co-scientist handlers
  const handleAddStep = (step: CoScientistStep) => {
    const updatedSteps = [...(project?.coScientistSteps || []), step];
    updateMutation.mutate({ coScientistSteps: updatedSteps });
    // Emit socket event for real-time sync
    emit({ type: "coscientist:step:add", payload: step });
  };

  const handleUpdateStep = (step: CoScientistStep) => {
    const updatedSteps = (project?.coScientistSteps || []).map((s: any) =>
      s.id === step.id ? step : s
    );
    updateMutation.mutate({ coScientistSteps: updatedSteps });
    // Emit socket event for real-time sync
    emit({ type: "coscientist:step:update", payload: step });
  };

  const handleAddComment = (stepId: string, comment: string) => {
    const newComment = { id: uuidv4(), text: comment, author: user?.name || "Unknown", createdAt: new Date().toISOString() };
    const updatedSteps = (project?.coScientistSteps || []).map((s: any) =>
      s.id === stepId
        ? {
            ...s,
            comments: [...s.comments, newComment],
          }
        : s
    );
    updateMutation.mutate({ coScientistSteps: updatedSteps });
    // Emit socket event for real-time sync
    emit({ type: "coscientist:comment:add", payload: { stepId, comment: newComment } });
  };

  // Checkpoint handlers
  const handleSaveCheckpoint = (name: string, description?: string) => {
    checkpointMutation.mutate({ name, description });
  };

  const handleRestoreCheckpoint = (checkpoint: Checkpoint) => {
    updateMutation.mutate({
      dataPool: checkpoint.dataPool,
      knowledgeGraph: checkpoint.knowledgeGraph,
      coScientistSteps: checkpoint.coScientistSteps,
      currentMode: checkpoint.mode,
    });
    setMode(checkpoint.mode);
  };

  // Export to PDF
  const handleExportPDF = async () => {
    // TODO: Implement IEEE-format PDF export
    console.log("Exporting to IEEE PDF format...");
  };

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-950">
        <Loader2 className="h-8 w-8 animate-spin text-green-500" />
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="flex h-screen flex-col items-center justify-center bg-gray-950">
        <p className="text-lg text-gray-400">Project not found</p>
        <Button className="mt-4" onClick={() => router.push("/dashboard")}>
          Go to Dashboard
        </Button>
      </div>
    );
  }

  return (
    <TooltipProvider>
      <div className="flex h-screen flex-col bg-gray-950">
        {/* Header */}
        <header className="flex flex-wrap items-center justify-between gap-4 border-b border-gray-800 bg-gray-900 px-6 py-3">
          <div className="flex min-w-0 flex-1 items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => router.push("/dashboard")}
              className="text-gray-300 hover:bg-gray-800"
            >
              <Home className="h-4 w-4" />
            </Button>
            <div className="min-w-0">
              <h1 className="truncate text-lg font-semibold text-green-100">
                {project.name}
              </h1>
              <p className="truncate text-xs text-gray-400">{project.description}</p>
            </div>
            <Badge variant="outline" className="hidden sm:block border-green-700 text-green-400">
              {project.members?.length || 1} member
              {project.members?.length !== 1 ? "s" : ""}
            </Badge>
          </div>

          {/* Mode Indicator */}
          <div className="hidden lg:block">
            <ModeIndicator mode={mode} onChange={setMode} />
          </div>
          <div className="block lg:hidden">
            <ModeIndicatorMobile mode={mode} onChange={setMode} />
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2">
            <div className="hidden sm:block">
              <CheckpointHistory
                checkpoints={project.checkpoints || []}
                onRestore={handleRestoreCheckpoint}
              />
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowCheckpointDialog(true)}
              className="border-gray-700 text-gray-300 hover:bg-gray-800"
            >
              <Save className="h-4 w-4 sm:mr-2" />
              <span className="hidden sm:inline">Save</span>
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowShareDialog(true)}
              className="border-gray-700 text-gray-300 hover:bg-gray-800"
            >
              <Share2 className="h-4 w-4 sm:mr-2" />
              <span className="hidden sm:inline">Share</span>
            </Button>

            {/* Team Avatars */}
            <div className="ml-2 hidden md:flex -space-x-2">
              {(project.members || []).slice(0, 3).map((member: any, idx: number) => (
                <Tooltip key={member.user.id}>
                  <TooltipTrigger asChild>
                    <Avatar className="h-8 w-8 border-2 border-gray-800">
                      <AvatarFallback
                        className={cn(
                          "text-xs",
                          idx === 0 && "bg-green-950 text-green-400",
                          idx === 1 && "bg-emerald-950 text-emerald-400",
                          idx === 2 && "bg-teal-950 text-teal-400"
                        )}
                      >
                        {member.user.name?.charAt(0) || "U"}
                      </AvatarFallback>
                    </Avatar>
                  </TooltipTrigger>
                  <TooltipContent>{member.user.name || "User"}</TooltipContent>
                </Tooltip>
              ))}
            </div>

            {/* User Menu */}
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => {
                    logout();
                    router.push("/login");
                  }}
                  className="text-gray-300 hover:bg-gray-800"
                >
                  <LogOut className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Sign out</TooltipContent>
            </Tooltip>
          </div>
        </header>

        {/* Main Content */}
        <main className="relative flex-1 overflow-auto">
          {/* Data Pool Mode */}
          {mode === "pool" && (
            <DataPool
              items={project.dataPool || []}
              onAddItem={handleAddPoolItem}
              onRemoveItem={handleRemovePoolItem}
              onViewItem={openViewer}
              projectId={projectId}
              project={project}
              onUpdateProject={async (data) => updateMutation.mutate(data)}
            />
          )}

          {/* Knowledge Graph Mode */}
          {mode === "retrieval" && (
            <KnowledgeGraphView
              graph={project.knowledgeGraph || { nodes: [], edges: [], groups: [] }}
              onNodeAdd={handleAddNode}
              onNodeUpdate={handleUpdateNode}
              onNodeRemove={(nodeId) => handleDeleteNode(nodeId)}
              onEdgeAdd={handleAddEdge}
              onEdgeRemove={handleDeleteEdge}
              onNodeView={(node) => {
                const poolItem = (project.dataPool || []).find(
                  (item: DataPoolItem) => item._id === node.id || item.name === node.label
                );
                if (poolItem) openViewer(poolItem);
              }}
            />
          )}

          {/* Co-Scientist Mode */}
          {mode === "coscientist" && (
            <div className="flex h-full items-center justify-center">
              <div className="max-w-md text-center">
                <Brain className="mx-auto h-16 w-16 text-green-400" />
                <h2 className="mt-4 text-xl font-semibold text-green-100">
                  AI Co-Scientist
                </h2>
                <p className="mt-2 text-gray-400">
                  Let the AI analyze your data pool and knowledge graph to
                  generate insights and design suggestions.
                </p>
                <Button
                  className="mt-6"
                  onClick={() => setShowCoScientist(true)}
                >
                  <Brain className="mr-2 h-4 w-4" />
                  Open Co-Scientist
                </Button>
              </div>
            </div>
          )}

          {/* Co-Scientist Sidebar */}
          <CoScientistSidebar
            steps={project.coScientistSteps || []}
            dataPool={project.dataPool || []}
            knowledgeGraph={project.knowledgeGraph || { nodes: [], edges: [], groups: [] }}
            onAddStep={handleAddStep}
            onUpdateStep={handleUpdateStep}
            onAddComment={handleAddComment}
            onViewAttachment={(attachment: { dataPoolItemId?: string; name: string }) => {
              const poolItem = (project.dataPool || []).find(
                (item: DataPoolItem) => item._id === attachment.dataPoolItemId
              );
              if (poolItem) openViewer(poolItem);
            }}
            onExport={handleExportPDF}
            onStart={() => {
              setIsCoScientistRunning(true);
              analysisMutation.mutate({ action: "start" });
            }}
            onPause={() => setIsCoScientistRunning(false)}
            onRestart={() => {
              setIsCoScientistRunning(false);
              updateMutation.mutate({ coScientistSteps: [] });
            }}
            onSendFeedback={(feedback: string) => {
              analysisMutation.mutate({ feedback, action: "feedback" });
            }}
            isRunning={isCoScientistRunning || analysisMutation.isPending}
            isOpen={showCoScientist || mode === "coscientist"}
            onClose={() => {
              setShowCoScientist(false);
              if (mode === "coscientist") setMode("retrieval");
            }}
          />

          {/* Floating Viewers */}
          {viewers.map((viewer, index) => {
            // Determine if data is a URL or base64 content
            const isUrl = viewer.data.startsWith('http://') || viewer.data.startsWith('https://') || viewer.data.startsWith('/');
            
            return (
              <FloatingWindow
                key={viewer.id}
                id={viewer.id}
                title={viewer.title}
                position={viewer.position}
                size={viewer.size}
                minimized={viewer.minimized}
                onClose={() => closeViewer(viewer.id)}
                onPositionChange={(pos) => updateViewerPosition(viewer.id, pos)}
                onSizeChange={(size) => updateViewerSize(viewer.id, size)}
                onMinimize={() => minimizeViewer(viewer.id)}
                onRestore={() => restoreViewer(viewer.id)}
              >
                {viewer.type === "pdb" && <PDBViewer content={viewer.data} />}
                {viewer.type === "pdf" && (
                  isUrl 
                    ? <PDFViewer fileUrl={viewer.data} />
                    : <PDFViewer content={viewer.data} />
                )}
                {viewer.type === "image" && (
                  isUrl
                    ? <ImageViewer fileUrl={viewer.data} />
                    : <ImageViewer content={viewer.data} />
                )}
                {viewer.type === "sequence" && (
                  <SequenceViewer content={viewer.data} />
                )}
                {viewer.type === "text" && (
                  <TextViewer content={viewer.data} />
                )}
              </FloatingWindow>
            );
          })}
        </main>

        {/* Dialogs */}
        <CheckpointDialog
          open={showCheckpointDialog}
          onOpenChange={setShowCheckpointDialog}
          onSave={handleSaveCheckpoint}
        />

        <ShareDialog
          open={showShareDialog}
          onOpenChange={setShowShareDialog}
          joinHash={project.joinHash || ""}
        />
      </div>
    </TooltipProvider>
  );
}
