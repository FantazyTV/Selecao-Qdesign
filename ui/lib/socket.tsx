"use client";

import React, { createContext, useContext, useEffect, useRef, useCallback } from "react";
import { io, Socket } from "socket.io-client";
import { useAuthStore, useProjectStore } from "@/lib/stores";
import type { SocketEvent, User, DataPoolItem, GraphNode, GraphEdge, CoScientistStep, Checkpoint } from "@/lib/types";

interface SocketContextType {
  socket: Socket | null;
  isConnected: boolean;
  joinProject: (projectId: string) => void;
  leaveProject: (projectId: string) => void;
  emit: (event: SocketEvent) => void;
}

const SocketContext = createContext<SocketContextType>({
  socket: null,
  isConnected: false,
  joinProject: () => {},
  leaveProject: () => {},
  emit: () => {},
});

export function SocketProvider({ children }: { children: React.ReactNode }) {
  const socketRef = useRef<Socket | null>(null);
  const [isConnected, setIsConnected] = React.useState(false);
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
      console.log("Socket connected");
    });

    socket.on("disconnect", () => {
      setIsConnected(false);
      console.log("Socket disconnected");
    });

    // Handle incoming events
    socket.on("project:update", (payload: SocketEvent["payload"]) => {
      if ("_id" in (payload as object)) {
        setProject(payload as unknown as typeof useProjectStore.getState extends () => { project: infer P } ? P : never);
      }
    });

    socket.on("pool:add", (payload: DataPoolItem) => {
      addDataPoolItem(payload);
    });

    socket.on("pool:update", (payload: DataPoolItem) => {
      updateDataPoolItem(payload);
    });

    socket.on("pool:remove", (payload: { itemId: string }) => {
      removeDataPoolItem(payload.itemId);
    });

    socket.on("graph:node:add", (payload: GraphNode) => {
      addGraphNode(payload);
    });

    socket.on("graph:node:update", (payload: GraphNode) => {
      updateGraphNode(payload);
    });

    socket.on("graph:node:remove", (payload: { nodeId: string }) => {
      removeGraphNode(payload.nodeId);
    });

    socket.on("graph:edge:add", (payload: GraphEdge) => {
      addGraphEdge(payload);
    });

    socket.on("graph:edge:remove", (payload: { edgeId: string }) => {
      removeGraphEdge(payload.edgeId);
    });

    socket.on("coscientist:step:add", (payload: CoScientistStep) => {
      addCoScientistStep(payload);
    });

    socket.on("coscientist:step:update", (payload: CoScientistStep) => {
      updateCoScientistStep(payload);
    });

    socket.on("coscientist:comment:add", (payload: { stepId: string; comment: CoScientistStep["comments"][0] }) => {
      addStepComment(payload.stepId, payload.comment);
    });

    socket.on("checkpoint:create", (payload: Checkpoint) => {
      addCheckpoint(payload);
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
    }
  }, []);

  const leaveProject = useCallback((projectId: string) => {
    if (socketRef.current) {
      socketRef.current.emit("project:leave", { projectId });
    }
  }, []);

  const emit = useCallback((event: SocketEvent) => {
    if (socketRef.current) {
      socketRef.current.emit(event.type, event.payload);
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
      }}
    >
      {children}
    </SocketContext.Provider>
  );
}

export function useSocket() {
  return useContext(SocketContext);
}
