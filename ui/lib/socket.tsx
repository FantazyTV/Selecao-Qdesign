"use client";

import React, { createContext, useContext, useEffect, useRef, useCallback, useState } from "react";
import { io, Socket } from "socket.io-client";
import { useAuthStore, useProjectStore } from "@/lib/stores";
import type { SocketEvent, User, DataPoolItem, GraphNode, GraphEdge, CoScientistStep, Checkpoint } from "@/lib/types";

interface SocketContextType {
  socket: Socket | null;
  isConnected: boolean;
  joinProject: (projectId: string) => void;
  leaveProject: (projectId: string) => void;
  emit: (event: SocketEvent) => void;
  emitPoolAdd: (projectId: string, item: DataPoolItem) => void;
  emitPoolUpdate: (projectId: string, item: DataPoolItem) => void;
  emitPoolRemove: (projectId: string, itemId: string) => void;
  emitGraphNodeAdd: (projectId: string, node: GraphNode) => void;
  emitGraphNodeUpdate: (projectId: string, node: GraphNode) => void;
  emitGraphNodeRemove: (projectId: string, nodeId: string) => void;
  emitGraphEdgeAdd: (projectId: string, edge: GraphEdge) => void;
  emitGraphEdgeRemove: (projectId: string, edgeId: string) => void;
  emitCoScientistStep: (projectId: string, step: CoScientistStep) => void;
  emitCheckpoint: (projectId: string, checkpoint: Checkpoint) => void;
}

const SocketContext = createContext<SocketContextType>({
  socket: null,
  isConnected: false,
  joinProject: () => {},
  leaveProject: () => {},
  emit: () => {},
  emitPoolAdd: () => {},
  emitPoolUpdate: () => {},
  emitPoolRemove: () => {},
  emitGraphNodeAdd: () => {},
  emitGraphNodeUpdate: () => {},
  emitGraphNodeRemove: () => {},
  emitGraphEdgeAdd: () => {},
  emitGraphEdgeRemove: () => {},
  emitCoScientistStep: () => {},
  emitCheckpoint: () => {},
});

export function SocketProvider({ children }: { children: React.ReactNode }) {
  const socketRef = useRef<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const currentProjectRef = useRef<string | null>(null);
  const { user } = useAuthStore();
  const {
    addDataPoolItem,
    updateDataPoolItem,
    removeDataPoolItem,
    addGraphNode,
    updateGraphNode,
    removeGraphNode,
    addGraphEdge,
    removeGraphEdge,
    addCoScientistStep,
    updateCoScientistStep,
    addStepComment,
    addCheckpoint,
    addActiveUser,
    removeActiveUser,
    setProject,
  } = useProjectStore();

  useEffect(() => {
    if (!user) return;

    // Connect to socket server
    const socket = io(process.env.NEXT_PUBLIC_SOCKET_URL || "http://localhost:3001", {
      auth: {
        userId: user.id,
        userName: user.name,
      },
    });

    socketRef.current = socket;

    socket.on("connect", () => {
      setIsConnected(true);
      console.log("Socket connected to:", process.env.NEXT_PUBLIC_SOCKET_URL || "http://localhost:3001");
    });

    socket.on("disconnect", () => {
      setIsConnected(false);
      console.log("Socket disconnected");
    });

    // Handle incoming events
    socket.on("project:update", (payload: SocketEvent["payload"]) => {
      if ("_id" in (payload as object)) {
        setProject(payload as unknown as typeof useProjectStore.getState extends () => { project: infer P } ? P : never);
        // Dispatch custom event for React Query invalidation
        if (currentProjectRef.current) {
          window.dispatchEvent(new CustomEvent(`project:${currentProjectRef.current}:update`));
        }
      }
    });

    socket.on("pool:add", (payload: DataPoolItem) => {
      addDataPoolItem(payload);
      if (currentProjectRef.current) {
        window.dispatchEvent(new CustomEvent(`project:${currentProjectRef.current}:update`));
      }
    });

    socket.on("pool:update", (payload: DataPoolItem) => {
      updateDataPoolItem(payload);
      if (currentProjectRef.current) {
        window.dispatchEvent(new CustomEvent(`project:${currentProjectRef.current}:update`));
      }
    });

    socket.on("pool:remove", (payload: { itemId: string }) => {
      removeDataPoolItem(payload.itemId);
      if (currentProjectRef.current) {
        window.dispatchEvent(new CustomEvent(`project:${currentProjectRef.current}:update`));
      }
    });

    socket.on("graph:node:add", (payload: GraphNode) => {
      addGraphNode(payload);
      if (currentProjectRef.current) {
        window.dispatchEvent(new CustomEvent(`project:${currentProjectRef.current}:update`));
      }
    });

    socket.on("graph:node:update", (payload: GraphNode) => {
      updateGraphNode(payload);
      if (currentProjectRef.current) {
        window.dispatchEvent(new CustomEvent(`project:${currentProjectRef.current}:update`));
      }
    });

    socket.on("graph:node:remove", (payload: { nodeId: string }) => {
      removeGraphNode(payload.nodeId);
      if (currentProjectRef.current) {
        window.dispatchEvent(new CustomEvent(`project:${currentProjectRef.current}:update`));
      }
    });

    socket.on("graph:edge:add", (payload: GraphEdge) => {
      addGraphEdge(payload);
      if (currentProjectRef.current) {
        window.dispatchEvent(new CustomEvent(`project:${currentProjectRef.current}:update`));
      }
    });

    socket.on("graph:edge:remove", (payload: { edgeId: string }) => {
      removeGraphEdge(payload.edgeId);
      if (currentProjectRef.current) {
        window.dispatchEvent(new CustomEvent(`project:${currentProjectRef.current}:update`));
      }
    });

    socket.on("coscientist:step:add", (payload: CoScientistStep) => {
      addCoScientistStep(payload);
      if (currentProjectRef.current) {
        window.dispatchEvent(new CustomEvent(`project:${currentProjectRef.current}:update`));
      }
    });

    socket.on("coscientist:step:update", (payload: CoScientistStep) => {
      updateCoScientistStep(payload);
      if (currentProjectRef.current) {
        window.dispatchEvent(new CustomEvent(`project:${currentProjectRef.current}:update`));
      }
    });

    socket.on("coscientist:comment:add", (payload: { stepId: string; comment: CoScientistStep["comments"][0] }) => {
      addStepComment(payload.stepId, payload.comment);
      if (currentProjectRef.current) {
        window.dispatchEvent(new CustomEvent(`project:${currentProjectRef.current}:update`));
      }
    });

    socket.on("checkpoint:create", (payload: Checkpoint) => {
      addCheckpoint(payload);
      if (currentProjectRef.current) {
        window.dispatchEvent(new CustomEvent(`project:${currentProjectRef.current}:update`));
      }
    });

    socket.on("user:joined", (payload: User) => {
      addActiveUser(payload);
    });

    socket.on("user:left", (payload: { userId: string }) => {
      removeActiveUser(payload.userId);
    });

    return () => {
      socket.disconnect();
      socketRef.current = null;
    };
  }, [user, addDataPoolItem, updateDataPoolItem, removeDataPoolItem, addGraphNode, updateGraphNode, removeGraphNode, addGraphEdge, removeGraphEdge, addCoScientistStep, updateCoScientistStep, addStepComment, addCheckpoint, addActiveUser, removeActiveUser, setProject]);

  const joinProject = useCallback((projectId: string) => {
    if (socketRef.current) {
      socketRef.current.emit("project:join", { projectId });
      currentProjectRef.current = projectId;
    }
  }, []);

  const leaveProject = useCallback((projectId: string) => {
    if (socketRef.current) {
      socketRef.current.emit("project:leave", { projectId });
      currentProjectRef.current = null;
    }
  }, []);

  const emit = useCallback((event: SocketEvent) => {
    if (socketRef.current) {
      socketRef.current.emit(event.type, event.payload);
    }
  }, []);

  // Helper functions for emitting specific events
  const emitPoolAdd = useCallback((projectId: string, item: DataPoolItem) => {
    console.log('[DEBUG] Socket context: emitPoolAdd called with:', { projectId, item });
    if (socketRef.current) {
      console.log('[DEBUG] Socket context: Socket exists, emitting pool:add');
      socketRef.current.emit("pool:add", { projectId, item });
    } else {
      console.log('[DEBUG] Socket context: No socket connection!');
    }
  }, []);

  const emitPoolUpdate = useCallback((projectId: string, item: DataPoolItem) => {
    if (socketRef.current) {
      socketRef.current.emit("pool:update", { projectId, item });
    }
  }, []);

  const emitPoolRemove = useCallback((projectId: string, itemId: string) => {
    console.log('[DEBUG] Socket context: emitPoolRemove called with:', { projectId, itemId });
    if (socketRef.current) {
      console.log('[DEBUG] Socket context: Socket exists, emitting pool:remove');
      socketRef.current.emit("pool:remove", { projectId, itemId });
    } else {
      console.log('[DEBUG] Socket context: No socket connection!');
    }
  }, []);

  const emitGraphNodeAdd = useCallback((projectId: string, node: GraphNode) => {
    if (socketRef.current) {
      socketRef.current.emit("graph:node:add", { projectId, node });
    }
  }, []);

  const emitGraphNodeUpdate = useCallback((projectId: string, node: GraphNode) => {
    if (socketRef.current) {
      socketRef.current.emit("graph:node:update", { projectId, node });
    }
  }, []);

  const emitGraphNodeRemove = useCallback((projectId: string, nodeId: string) => {
    if (socketRef.current) {
      socketRef.current.emit("graph:node:remove", { projectId, nodeId });
    }
  }, []);

  const emitGraphEdgeAdd = useCallback((projectId: string, edge: GraphEdge) => {
    if (socketRef.current) {
      socketRef.current.emit("graph:edge:add", { projectId, edge });
    }
  }, []);

  const emitGraphEdgeRemove = useCallback((projectId: string, edgeId: string) => {
    if (socketRef.current) {
      socketRef.current.emit("graph:edge:remove", { projectId, edgeId });
    }
  }, []);

  const emitCoScientistStep = useCallback((projectId: string, step: CoScientistStep) => {
    if (socketRef.current) {
      socketRef.current.emit("coscientist:step:add", { projectId, step });
    }
  }, []);

  const emitCheckpoint = useCallback((projectId: string, checkpoint: Checkpoint) => {
    if (socketRef.current) {
      socketRef.current.emit("checkpoint:create", { projectId, checkpoint });
    }
  }, []);

  return (
    <SocketContext.Provider
      value={{
        socket: socketRef.current,
        isConnected,
        joinProject,
        leaveProject,
        emit,
        emitPoolAdd,
        emitPoolUpdate,
        emitPoolRemove,
        emitGraphNodeAdd,
        emitGraphNodeUpdate,
        emitGraphNodeRemove,
        emitGraphEdgeAdd,
        emitGraphEdgeRemove,
        emitCoScientistStep,
        emitCheckpoint,
      }}
    >
      {children}
    </SocketContext.Provider>
  );
}

export function useSocket() {
  return useContext(SocketContext);
}
