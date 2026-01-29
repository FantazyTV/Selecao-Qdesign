// Socket emitter utility for backend -> frontend events
import { Server as IOServer } from 'socket.io';

let io: IOServer | null = null;

export function setSocketServer(server: IOServer) {
  io = server;
}

export function emitProjectUpdate(projectId: string, project: any) {
  if (io) {
    io.to(projectId).emit('project:update', project);
  }
}
