// WebSocket Server for Real-Time Collaboration
// This file should be run as a separate process alongside the Next.js app
// Run with: npx ts-node --esm server/socket.ts

import { Server } from "socket.io";
import { createServer } from "http";

const PORT = process.env.SOCKET_PORT || 3001;

const httpServer = createServer();
const io = new Server(httpServer, {
  cors: {
    origin: process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000",
    methods: ["GET", "POST"],
    credentials: true,
  },
});

// Track connected users per project
const projectRooms = new Map<string, Set<{ socketId: string; userId: string; userName: string }>>();

// Track user cursors for collaborative editing
const userCursors = new Map<string, { x: number; y: number; color: string }>();

// Generate random color for user cursor
function generateCursorColor(): string {
  const colors = [
    "#3B82F6", // blue
    "#10B981", // emerald
    "#8B5CF6", // purple
    "#F59E0B", // amber
    "#EF4444", // red
    "#EC4899", // pink
    "#06B6D4", // cyan
  ];
  return colors[Math.floor(Math.random() * colors.length)];
}

io.on("connection", (socket) => {
  console.log(`Client connected: ${socket.id}`);

  let currentProjectId: string | null = null;
  let currentUserId: string | null = null;
  let currentUserName: string | null = null;
  let cursorColor: string = generateCursorColor();

  // Join a project room
  socket.on("join-project", (data: { projectId: string; userId: string; userName: string }) => {
    const { projectId, userId, userName } = data;

    // Leave previous room if any
    if (currentProjectId) {
      socket.leave(currentProjectId);
      const room = projectRooms.get(currentProjectId);
      if (room) {
        const user = Array.from(room).find((u) => u.socketId === socket.id);
        if (user) room.delete(user);
        if (room.size === 0) {
          projectRooms.delete(currentProjectId);
        }
      }
    }

    // Join new room
    currentProjectId = projectId;
    currentUserId = userId;
    currentUserName = userName;

    socket.join(projectId);

    // Track user in room
    if (!projectRooms.has(projectId)) {
      projectRooms.set(projectId, new Set());
    }
    projectRooms.get(projectId)!.add({
      socketId: socket.id,
      userId,
      userName,
    });

    // Store cursor color
    userCursors.set(socket.id, { x: 0, y: 0, color: cursorColor });

    // Notify others in the room
    socket.to(projectId).emit("user-joined", {
      userId,
      userName,
      color: cursorColor,
    });

    // Send current users to the new member
    const users = Array.from(projectRooms.get(projectId)!).map((u) => ({
      userId: u.userId,
      userName: u.userName,
      color: userCursors.get(u.socketId)?.color || cursorColor,
    }));
    socket.emit("room-users", users);

    console.log(`User ${userName} joined project ${projectId}`);
  });

  // Leave project room
  socket.on("leave-project", () => {
    if (currentProjectId) {
      socket.to(currentProjectId).emit("user-left", {
        userId: currentUserId,
        userName: currentUserName,
      });

      socket.leave(currentProjectId);
      const room = projectRooms.get(currentProjectId);
      if (room) {
        const user = Array.from(room).find((u) => u.socketId === socket.id);
        if (user) room.delete(user);
        if (room.size === 0) {
          projectRooms.delete(currentProjectId);
        }
      }

      console.log(`User ${currentUserName} left project ${currentProjectId}`);
      currentProjectId = null;
    }
  });

  // Data Pool updates
  socket.on("pool-item-added", (data: { projectId: string; item: any }) => {
    socket.to(data.projectId).emit("pool-item-added", data.item);
  });

  socket.on("pool-item-removed", (data: { projectId: string; itemId: string }) => {
    socket.to(data.projectId).emit("pool-item-removed", data.itemId);
  });

  socket.on("pool-item-updated", (data: { projectId: string; item: any }) => {
    socket.to(data.projectId).emit("pool-item-updated", data.item);
  });

  // Knowledge Graph updates
  socket.on("node-added", (data: { projectId: string; node: any }) => {
    socket.to(data.projectId).emit("node-added", data.node);
  });

  socket.on("node-updated", (data: { projectId: string; node: any }) => {
    socket.to(data.projectId).emit("node-updated", data.node);
  });

  socket.on("node-deleted", (data: { projectId: string; nodeId: string }) => {
    socket.to(data.projectId).emit("node-deleted", data.nodeId);
  });

  socket.on("edge-added", (data: { projectId: string; edge: any }) => {
    socket.to(data.projectId).emit("edge-added", data.edge);
  });

  socket.on("edge-updated", (data: { projectId: string; edge: any }) => {
    socket.to(data.projectId).emit("edge-updated", data.edge);
  });

  socket.on("edge-deleted", (data: { projectId: string; edgeId: string }) => {
    socket.to(data.projectId).emit("edge-deleted", data.edgeId);
  });

  // Node position updates (for graph dragging)
  socket.on("node-position", (data: { projectId: string; nodeId: string; position: { x: number; y: number } }) => {
    socket.to(data.projectId).emit("node-position", {
      nodeId: data.nodeId,
      position: data.position,
    });
  });

  // Co-Scientist updates
  socket.on("step-added", (data: { projectId: string; step: any }) => {
    socket.to(data.projectId).emit("step-added", data.step);
  });

  socket.on("step-updated", (data: { projectId: string; step: any }) => {
    socket.to(data.projectId).emit("step-updated", data.step);
  });

  socket.on("comment-added", (data: { projectId: string; stepId: string; comment: any }) => {
    socket.to(data.projectId).emit("comment-added", {
      stepId: data.stepId,
      comment: data.comment,
    });
  });

  // Mode changes
  socket.on("mode-changed", (data: { projectId: string; mode: string }) => {
    socket.to(data.projectId).emit("mode-changed", data.mode);
  });

  // Checkpoint events
  socket.on("checkpoint-created", (data: { projectId: string; checkpoint: any }) => {
    socket.to(data.projectId).emit("checkpoint-created", data.checkpoint);
  });

  socket.on("checkpoint-restored", (data: { projectId: string; checkpointId: string }) => {
    socket.to(data.projectId).emit("checkpoint-restored", data.checkpointId);
  });

  // Cursor tracking for collaborative awareness
  socket.on("cursor-move", (data: { projectId: string; x: number; y: number }) => {
    if (userCursors.has(socket.id)) {
      const cursor = userCursors.get(socket.id)!;
      cursor.x = data.x;
      cursor.y = data.y;

      socket.to(data.projectId).emit("cursor-update", {
        socketId: socket.id,
        userId: currentUserId,
        userName: currentUserName,
        x: data.x,
        y: data.y,
        color: cursor.color,
      });
    }
  });

  // Typing indicator
  socket.on("typing-start", (data: { projectId: string; field: string }) => {
    socket.to(data.projectId).emit("user-typing", {
      userId: currentUserId,
      userName: currentUserName,
      field: data.field,
    });
  });

  socket.on("typing-stop", (data: { projectId: string }) => {
    socket.to(data.projectId).emit("user-stopped-typing", {
      userId: currentUserId,
    });
  });

  // Handle disconnection
  socket.on("disconnect", () => {
    console.log(`Client disconnected: ${socket.id}`);

    if (currentProjectId) {
      socket.to(currentProjectId).emit("user-left", {
        userId: currentUserId,
        userName: currentUserName,
      });

      const room = projectRooms.get(currentProjectId);
      if (room) {
        const user = Array.from(room).find((u) => u.socketId === socket.id);
        if (user) room.delete(user);
        if (room.size === 0) {
          projectRooms.delete(currentProjectId);
        }
      }
    }

    userCursors.delete(socket.id);
  });
});

httpServer.listen(PORT, () => {
  console.log(`🔌 WebSocket server running on port ${PORT}`);
});

export { io, httpServer };
