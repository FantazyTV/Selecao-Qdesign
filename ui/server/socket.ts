// WebSocket Server for Real-Time Collaboration
// This file should be run as a separate process alongside the Next.js app
// Run with: npx ts-node --esm server/socket.ts

import { Server } from "socket.io";
import { createServer } from "http";

const PORT = process.env.SOCKET_PORT || 3002;

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

  // Join a project room - support both event name formats
  socket.on("project:join", (data: { projectId: string }) => {
    const { projectId } = data;
    const userId = (socket.handshake.auth as any).userId || socket.id;
    const userName = (socket.handshake.auth as any).userName || "Anonymous";

    handleJoinProject(socket, projectId, userId, userName);
  });

  socket.on("join-project", (data: { projectId: string; userId: string; userName: string }) => {
    const { projectId, userId, userName } = data;
    handleJoinProject(socket, projectId, userId, userName);
  });

  function handleJoinProject(socket: any, projectId: string, userId: string, userName: string) {
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
    socket.to(projectId).emit("user:joined", {
      id: userId,
      name: userName,
      color: cursorColor,
    });

    // Send current users to the new member
    const users = Array.from(projectRooms.get(projectId)!).map((u) => ({
      id: u.userId,
      name: u.userName,
      color: userCursors.get(u.socketId)?.color || cursorColor,
    }));
    socket.emit("room-users", users);

    console.log(`User ${userName} joined project ${projectId}`);
  }

  // Leave project room - support both formats
  socket.on("project:leave", (data: { projectId: string }) => {
    handleLeaveProject(socket);
  });

  socket.on("leave-project", () => {
    handleLeaveProject(socket);
  });

  function handleLeaveProject(socket: any) {
    if (currentProjectId) {
      socket.to(currentProjectId).emit("user:left", {
        userId: currentUserId,
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
  }

  // Data Pool updates - support new event format
  socket.on("pool:add", (data: { projectId?: string; item?: any; payload?: any }) => {
    console.log(`[DEBUG] pool:add received:`, data);
    const projectId = data.projectId || currentProjectId;
    const item = data.item || data.payload;
    console.log(`[DEBUG] Extracted projectId: ${projectId}, item exists: ${!!item}`);
    if (projectId && item) {
      console.log(`[DEBUG] Broadcasting pool:add to room ${projectId}`);
      socket.to(projectId).emit("pool:add", item);
    } else {
      console.log(`[DEBUG] Missing projectId or item, not broadcasting`);
    }
  });

  socket.on("pool:remove", (data: { projectId?: string; itemId?: string; payload?: { itemId: string } }) => {
    console.log(`[DEBUG] pool:remove received:`, data);
    const projectId = data.projectId || currentProjectId;
    const itemId = data.itemId || data.payload?.itemId;
    console.log(`[DEBUG] Extracted projectId: ${projectId}, itemId: ${itemId}`);
    if (projectId && itemId) {
      console.log(`[DEBUG] Broadcasting pool:remove to room ${projectId}`);
      socket.to(projectId).emit("pool:remove", { itemId });
    } else {
      console.log(`[DEBUG] Missing projectId or itemId, not broadcasting`);
    }
  });

  socket.on("pool:update", (data: { projectId?: string; item?: any; payload?: any }) => {
    const projectId = data.projectId || currentProjectId;
    const item = data.item || data.payload;
    if (projectId && item) {
      socket.to(projectId).emit("pool:update", item);
    }
  });

  // Legacy event handlers for backwards compatibility
  socket.on("pool-item-added", (data: { projectId: string; item: any }) => {
    socket.to(data.projectId).emit("pool:add", data.item);
  });

  socket.on("pool-item-removed", (data: { projectId: string; itemId: string }) => {
    socket.to(data.projectId).emit("pool:remove", { itemId: data.itemId });
  });

  socket.on("pool-item-updated", (data: { projectId: string; item: any }) => {
    socket.to(data.projectId).emit("pool:update", data.item);
  });

  // Knowledge Graph updates - support new event format
  socket.on("graph:node:add", (data: { projectId?: string; node?: any; payload?: any }) => {
    const projectId = data.projectId || currentProjectId;
    const node = data.node || data.payload;
    if (projectId && node) {
      socket.to(projectId).emit("graph:node:add", node);
    }
  });

  socket.on("graph:node:update", (data: { projectId?: string; node?: any; payload?: any }) => {
    const projectId = data.projectId || currentProjectId;
    const node = data.node || data.payload;
    if (projectId && node) {
      socket.to(projectId).emit("graph:node:update", node);
    }
  });

  socket.on("graph:node:remove", (data: { projectId?: string; nodeId?: string; payload?: { nodeId: string } }) => {
    const projectId = data.projectId || currentProjectId;
    const nodeId = data.nodeId || data.payload?.nodeId;
    if (projectId && nodeId) {
      socket.to(projectId).emit("graph:node:remove", { nodeId });
    }
  });

  socket.on("graph:edge:add", (data: { projectId?: string; edge?: any; payload?: any }) => {
    const projectId = data.projectId || currentProjectId;
    const edge = data.edge || data.payload;
    if (projectId && edge) {
      socket.to(projectId).emit("graph:edge:add", edge);
    }
  });

  socket.on("graph:edge:remove", (data: { projectId?: string; edgeId?: string; payload?: { edgeId: string } }) => {
    const projectId = data.projectId || currentProjectId;
    const edgeId = data.edgeId || data.payload?.edgeId;
    if (projectId && edgeId) {
      socket.to(projectId).emit("graph:edge:remove", { edgeId });
    }
  });

  // Legacy graph event handlers
  socket.on("node-added", (data: { projectId: string; node: any }) => {
    socket.to(data.projectId).emit("graph:node:add", data.node);
  });

  socket.on("node-updated", (data: { projectId: string; node: any }) => {
    socket.to(data.projectId).emit("graph:node:update", data.node);
  });

  socket.on("node-deleted", (data: { projectId: string; nodeId: string }) => {
    socket.to(data.projectId).emit("graph:node:remove", { nodeId: data.nodeId });
  });

  socket.on("edge-added", (data: { projectId: string; edge: any }) => {
    socket.to(data.projectId).emit("graph:edge:add", data.edge);
  });

  socket.on("edge-updated", (data: { projectId: string; edge: any }) => {
    socket.to(data.projectId).emit("graph:edge:update", data.edge);
  });

  socket.on("edge-deleted", (data: { projectId: string; edgeId: string }) => {
    socket.to(data.projectId).emit("graph:edge:remove", { edgeId: data.edgeId });
  });

  // Node position updates (for graph dragging)
  socket.on("node-position", (data: { projectId: string; nodeId: string; position: { x: number; y: number } }) => {
    socket.to(data.projectId).emit("node-position", {
      nodeId: data.nodeId,
      position: data.position,
    });
  });

  // Co-Scientist updates - support new event format
  socket.on("coscientist:step:add", (data: { projectId?: string; step?: any; payload?: any }) => {
    const projectId = data.projectId || currentProjectId;
    const step = data.step || data.payload;
    if (projectId && step) {
      socket.to(projectId).emit("coscientist:step:add", step);
    }
  });

  socket.on("coscientist:step:update", (data: { projectId?: string; step?: any; payload?: any }) => {
    const projectId = data.projectId || currentProjectId;
    const step = data.step || data.payload;
    if (projectId && step) {
      socket.to(projectId).emit("coscientist:step:update", step);
    }
  });

  socket.on("coscientist:comment:add", (data: { projectId?: string; stepId?: string; comment?: any; payload?: any }) => {
    const projectId = data.projectId || currentProjectId;
    const stepId = data.stepId || data.payload?.stepId;
    const comment = data.comment || data.payload?.comment;
    if (projectId && stepId && comment) {
      socket.to(projectId).emit("coscientist:comment:add", { stepId, comment });
    }
  });

  // Legacy co-scientist event handlers
  socket.on("step-added", (data: { projectId: string; step: any }) => {
    socket.to(data.projectId).emit("coscientist:step:add", data.step);
  });

  socket.on("step-updated", (data: { projectId: string; step: any }) => {
    socket.to(data.projectId).emit("coscientist:step:update", data.step);
  });

  socket.on("comment-added", (data: { projectId: string; stepId: string; comment: any }) => {
    socket.to(data.projectId).emit("coscientist:comment:add", {
      stepId: data.stepId,
      comment: data.comment,
    });
  });

  // Mode changes
  socket.on("mode-changed", (data: { projectId: string; mode: string }) => {
    socket.to(data.projectId).emit("mode-changed", data.mode);
  });

  // Checkpoint events - support new event format
  socket.on("checkpoint:create", (data: { projectId?: string; checkpoint?: any; payload?: any }) => {
    const projectId = data.projectId || currentProjectId;
    const checkpoint = data.checkpoint || data.payload;
    if (projectId && checkpoint) {
      socket.to(projectId).emit("checkpoint:create", checkpoint);
    }
  });

  // Legacy checkpoint event handlers
  socket.on("checkpoint-created", (data: { projectId: string; checkpoint: any }) => {
    socket.to(data.projectId).emit("checkpoint:create", data.checkpoint);
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
      socket.to(currentProjectId).emit("user:left", {
        userId: currentUserId,
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

// Handle server errors
httpServer.on('error', (err: NodeJS.ErrnoException) => {
  if (err.code === 'EADDRINUSE') {
    console.error(`❌ Port ${PORT} is already in use. Please kill the existing process or use a different port.`);
    console.error(`   Run: npx kill-port ${PORT}`);
    process.exit(1);
  } else {
    throw err;
  }
});

httpServer.listen(PORT, () => {
  console.log(`🔌 WebSocket server running on port ${PORT}`);
});

export { io, httpServer };
