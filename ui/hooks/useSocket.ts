"use client";

import { useEffect, useCallback, useRef } from "react";
import { io, Socket } from "socket.io-client";
import { useAuthStore } from "@/lib/stores";

const SOCKET_URL = process.env.NEXT_PUBLIC_SOCKET_URL || "http://localhost:3001";

let socket: Socket | null = null;

function getSocket(): Socket {
  if (!socket) {
    socket = io(SOCKET_URL, {
      autoConnect: false,
      withCredentials: true,
    });
  }
  return socket;
}

export function useSocket(projectId: string | null) {
  const { user } = useAuthStore();
  const socketRef = useRef<Socket | null>(null);

  useEffect(() => {
    if (!projectId || !user) return;

    const socket = getSocket();
    socketRef.current = socket;

    if (!socket.connected) {
      socket.connect();
    }

    socket.emit("join-project", {
      projectId,
      userId: user.id,
      userName: user.name || user.email,
    });

    return () => {
      socket.emit("leave-project");
    };
  }, [projectId, user]);

  // Emit events
  const emit = useCallback(
    (event: string, data: any) => {
      if (socketRef.current && projectId) {
        socketRef.current.emit(event, { projectId, ...data });
      }
    },
    [projectId]
  );

  // Subscribe to events
  const on = useCallback(
    (event: string, callback: (...args: any[]) => void) => {
      const socket = socketRef.current;
      if (socket) {
        socket.on(event, callback);
        return () => {
          socket.off(event, callback);
        };
      }
      return () => {};
    },
    []
  );

  // Off event
  const off = useCallback((event: string, callback?: (...args: any[]) => void) => {
    const socket = socketRef.current;
    if (socket) {
      if (callback) {
        socket.off(event, callback);
      } else {
        socket.off(event);
      }
    }
  }, []);

  return {
    socket: socketRef.current,
    emit,
    on,
    off,
    isConnected: socketRef.current?.connected || false,
  };
}

// Specific hooks for different features
export function useRealTimeDataPool(
  projectId: string | null,
  callbacks: {
    onItemAdded?: (item: any) => void;
    onItemRemoved?: (itemId: string) => void;
    onItemUpdated?: (item: any) => void;
  }
) {
  const { on, emit } = useSocket(projectId);

  useEffect(() => {
    const unsubscribers: (() => void)[] = [];

    if (callbacks.onItemAdded) {
      unsubscribers.push(on("pool-item-added", callbacks.onItemAdded));
    }
    if (callbacks.onItemRemoved) {
      unsubscribers.push(on("pool-item-removed", callbacks.onItemRemoved));
    }
    if (callbacks.onItemUpdated) {
      unsubscribers.push(on("pool-item-updated", callbacks.onItemUpdated));
    }

    return () => {
      unsubscribers.forEach((unsub) => unsub());
    };
  }, [on, callbacks]);

  return {
    emitItemAdded: (item: any) => emit("pool-item-added", { item }),
    emitItemRemoved: (itemId: string) => emit("pool-item-removed", { itemId }),
    emitItemUpdated: (item: any) => emit("pool-item-updated", { item }),
  };
}

export function useRealTimeGraph(
  projectId: string | null,
  callbacks: {
    onNodeAdded?: (node: any) => void;
    onNodeUpdated?: (node: any) => void;
    onNodeDeleted?: (nodeId: string) => void;
    onEdgeAdded?: (edge: any) => void;
    onEdgeUpdated?: (edge: any) => void;
    onEdgeDeleted?: (edgeId: string) => void;
    onNodePosition?: (data: { nodeId: string; position: { x: number; y: number } }) => void;
  }
) {
  const { on, emit } = useSocket(projectId);

  useEffect(() => {
    const unsubscribers: (() => void)[] = [];

    if (callbacks.onNodeAdded) {
      unsubscribers.push(on("node-added", callbacks.onNodeAdded));
    }
    if (callbacks.onNodeUpdated) {
      unsubscribers.push(on("node-updated", callbacks.onNodeUpdated));
    }
    if (callbacks.onNodeDeleted) {
      unsubscribers.push(on("node-deleted", callbacks.onNodeDeleted));
    }
    if (callbacks.onEdgeAdded) {
      unsubscribers.push(on("edge-added", callbacks.onEdgeAdded));
    }
    if (callbacks.onEdgeUpdated) {
      unsubscribers.push(on("edge-updated", callbacks.onEdgeUpdated));
    }
    if (callbacks.onEdgeDeleted) {
      unsubscribers.push(on("edge-deleted", callbacks.onEdgeDeleted));
    }
    if (callbacks.onNodePosition) {
      unsubscribers.push(on("node-position", callbacks.onNodePosition));
    }

    return () => {
      unsubscribers.forEach((unsub) => unsub());
    };
  }, [on, callbacks]);

  return {
    emitNodeAdded: (node: any) => emit("node-added", { node }),
    emitNodeUpdated: (node: any) => emit("node-updated", { node }),
    emitNodeDeleted: (nodeId: string) => emit("node-deleted", { nodeId }),
    emitEdgeAdded: (edge: any) => emit("edge-added", { edge }),
    emitEdgeUpdated: (edge: any) => emit("edge-updated", { edge }),
    emitEdgeDeleted: (edgeId: string) => emit("edge-deleted", { edgeId }),
    emitNodePosition: (nodeId: string, position: { x: number; y: number }) =>
      emit("node-position", { nodeId, position }),
  };
}

export function useRealTimeCoScientist(
  projectId: string | null,
  callbacks: {
    onStepAdded?: (step: any) => void;
    onStepUpdated?: (step: any) => void;
    onCommentAdded?: (data: { stepId: string; comment: any }) => void;
  }
) {
  const { on, emit } = useSocket(projectId);

  useEffect(() => {
    const unsubscribers: (() => void)[] = [];

    if (callbacks.onStepAdded) {
      unsubscribers.push(on("step-added", callbacks.onStepAdded));
    }
    if (callbacks.onStepUpdated) {
      unsubscribers.push(on("step-updated", callbacks.onStepUpdated));
    }
    if (callbacks.onCommentAdded) {
      unsubscribers.push(on("comment-added", callbacks.onCommentAdded));
    }

    return () => {
      unsubscribers.forEach((unsub) => unsub());
    };
  }, [on, callbacks]);

  return {
    emitStepAdded: (step: any) => emit("step-added", { step }),
    emitStepUpdated: (step: any) => emit("step-updated", { step }),
    emitCommentAdded: (stepId: string, comment: any) =>
      emit("comment-added", { stepId, comment }),
  };
}

export function useCollaborativeAwareness(
  projectId: string | null,
  callbacks: {
    onUserJoined?: (user: { userId: string; userName: string; color: string }) => void;
    onUserLeft?: (user: { userId: string; userName: string }) => void;
    onRoomUsers?: (users: { userId: string; userName: string; color: string }[]) => void;
    onCursorUpdate?: (data: {
      socketId: string;
      userId: string;
      userName: string;
      x: number;
      y: number;
      color: string;
    }) => void;
    onUserTyping?: (data: { userId: string; userName: string; field: string }) => void;
    onUserStoppedTyping?: (data: { userId: string }) => void;
  }
) {
  const { on, emit } = useSocket(projectId);

  useEffect(() => {
    const unsubscribers: (() => void)[] = [];

    if (callbacks.onUserJoined) {
      unsubscribers.push(on("user-joined", callbacks.onUserJoined));
    }
    if (callbacks.onUserLeft) {
      unsubscribers.push(on("user-left", callbacks.onUserLeft));
    }
    if (callbacks.onRoomUsers) {
      unsubscribers.push(on("room-users", callbacks.onRoomUsers));
    }
    if (callbacks.onCursorUpdate) {
      unsubscribers.push(on("cursor-update", callbacks.onCursorUpdate));
    }
    if (callbacks.onUserTyping) {
      unsubscribers.push(on("user-typing", callbacks.onUserTyping));
    }
    if (callbacks.onUserStoppedTyping) {
      unsubscribers.push(on("user-stopped-typing", callbacks.onUserStoppedTyping));
    }

    return () => {
      unsubscribers.forEach((unsub) => unsub());
    };
  }, [on, callbacks]);

  return {
    emitCursorMove: (x: number, y: number) => emit("cursor-move", { x, y }),
    emitTypingStart: (field: string) => emit("typing-start", { field }),
    emitTypingStop: () => emit("typing-stop", {}),
  };
}
