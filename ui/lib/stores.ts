"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User, Project, DataPoolItem, GraphNode, GraphEdge, CoScientistStep, Checkpoint } from "@/lib/types";
import { authApi, getToken, setToken, removeToken } from "@/lib/api";

interface AuthState {
  user: User | null;
  isLoading: boolean;
  isInitialized: boolean;
  setUser: (user: User | null) => void;
  setLoading: (loading: boolean) => void;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  checkSession: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  isLoading: true,
  isInitialized: false,
  
  setUser: (user) => set({ user, isLoading: false }),
  setLoading: (isLoading) => set({ isLoading }),
  
  login: async (email: string, password: string) => {
    set({ isLoading: true });
    try {
      const response = await authApi.login({ email, password });
      setToken(response.token);
      set({ user: response.user, isLoading: false, isInitialized: true });
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },
  
  register: async (name: string, email: string, password: string) => {
    set({ isLoading: true });
    try {
      const response = await authApi.register({ name, email, password });
      setToken(response.token);
      set({ user: response.user, isLoading: false, isInitialized: true });
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },
  
  logout: () => {
    removeToken();
    set({ user: null, isInitialized: true });
  },
  
  checkSession: async () => {
    const token = getToken();
    if (!token) {
      set({ user: null, isLoading: false, isInitialized: true });
      return;
    }
    
    try {
      const response = await authApi.getSession();
      set({ user: response.user, isLoading: false, isInitialized: true });
    } catch {
      removeToken();
      set({ user: null, isLoading: false, isInitialized: true });
    }
  },
}));

interface ProjectState {
  project: Project | null;
  activeUsers: User[];
  isLoading: boolean;
  
  setProject: (project: Project | null) => void;
  setLoading: (loading: boolean) => void;
  setActiveUsers: (users: User[]) => void;
  addActiveUser: (user: User) => void;
  removeActiveUser: (userId: string) => void;
  
  // Data Pool
  addDataPoolItem: (item: DataPoolItem) => void;
  updateDataPoolItem: (item: DataPoolItem) => void;
  removeDataPoolItem: (itemId: string) => void;
  
  // Knowledge Graph
  addGraphNode: (node: GraphNode) => void;
  updateGraphNode: (node: GraphNode) => void;
  removeGraphNode: (nodeId: string) => void;
  addGraphEdge: (edge: GraphEdge) => void;
  removeGraphEdge: (edgeId: string) => void;
  
  // Co-Scientist
  addCoScientistStep: (step: CoScientistStep) => void;
  updateCoScientistStep: (step: CoScientistStep) => void;
  addStepComment: (stepId: string, comment: CoScientistStep["comments"][0]) => void;
  
  // Checkpoints
  addCheckpoint: (checkpoint: Checkpoint) => void;
  
  // Mode
  setMode: (mode: Project["currentMode"]) => void;
}

export const useProjectStore = create<ProjectState>((set) => ({
  project: null,
  activeUsers: [],
  isLoading: true,
  
  setProject: (project) => set({ project, isLoading: false }),
  setLoading: (isLoading) => set({ isLoading }),
  setActiveUsers: (activeUsers) => set({ activeUsers }),
  addActiveUser: (user) => set((state) => ({
    activeUsers: state.activeUsers.some((u) => u.id === user.id)
      ? state.activeUsers
      : [...state.activeUsers, user],
  })),
  removeActiveUser: (userId) => set((state) => ({
    activeUsers: state.activeUsers.filter((u) => u.id !== userId),
  })),
  
  addDataPoolItem: (item) => set((state) => {
    if (!state.project) return state;
    return {
      project: {
        ...state.project,
        dataPool: [...state.project.dataPool, item],
      },
    };
  }),
  
  updateDataPoolItem: (item) => set((state) => {
    if (!state.project) return state;
    return {
      project: {
        ...state.project,
        dataPool: state.project.dataPool.map((i) =>
          i._id === item._id ? item : i
        ),
      },
    };
  }),
  
  removeDataPoolItem: (itemId) => set((state) => {
    if (!state.project) return state;
    return {
      project: {
        ...state.project,
        dataPool: state.project.dataPool.filter((i) => i._id !== itemId),
      },
    };
  }),
  
  addGraphNode: (node) => set((state) => {
    if (!state.project) return state;
    return {
      project: {
        ...state.project,
        knowledgeGraph: {
          ...state.project.knowledgeGraph,
          nodes: [...state.project.knowledgeGraph.nodes, node],
        },
      },
    };
  }),
  
  updateGraphNode: (node) => set((state) => {
    if (!state.project) return state;
    return {
      project: {
        ...state.project,
        knowledgeGraph: {
          ...state.project.knowledgeGraph,
          nodes: state.project.knowledgeGraph.nodes.map((n) =>
            n.id === node.id ? node : n
          ),
        },
      },
    };
  }),
  
  removeGraphNode: (nodeId) => set((state) => {
    if (!state.project) return state;
    return {
      project: {
        ...state.project,
        knowledgeGraph: {
          ...state.project.knowledgeGraph,
          nodes: state.project.knowledgeGraph.nodes.filter((n) => n.id !== nodeId),
          edges: state.project.knowledgeGraph.edges.filter(
            (e) => e.source !== nodeId && e.target !== nodeId
          ),
        },
      },
    };
  }),
  
  addGraphEdge: (edge) => set((state) => {
    if (!state.project) return state;
    return {
      project: {
        ...state.project,
        knowledgeGraph: {
          ...state.project.knowledgeGraph,
          edges: [...state.project.knowledgeGraph.edges, edge],
        },
      },
    };
  }),
  
  removeGraphEdge: (edgeId) => set((state) => {
    if (!state.project) return state;
    return {
      project: {
        ...state.project,
        knowledgeGraph: {
          ...state.project.knowledgeGraph,
          edges: state.project.knowledgeGraph.edges.filter((e) => e.id !== edgeId),
        },
      },
    };
  }),
  
  addCoScientistStep: (step) => set((state) => {
    if (!state.project) return state;
    return {
      project: {
        ...state.project,
        coScientistSteps: [...state.project.coScientistSteps, step],
      },
    };
  }),
  
  updateCoScientistStep: (step) => set((state) => {
    if (!state.project) return state;
    return {
      project: {
        ...state.project,
        coScientistSteps: state.project.coScientistSteps.map((s) =>
          s.id === step.id ? step : s
        ),
      },
    };
  }),
  
  addStepComment: (stepId, comment) => set((state) => {
    if (!state.project) return state;
    return {
      project: {
        ...state.project,
        coScientistSteps: state.project.coScientistSteps.map((s) =>
          s.id === stepId ? { ...s, comments: [...s.comments, comment] } : s
        ),
      },
    };
  }),
  
  addCheckpoint: (checkpoint) => set((state) => {
    if (!state.project) return state;
    return {
      project: {
        ...state.project,
        checkpoints: [...state.project.checkpoints, checkpoint],
      },
    };
  }),
  
  setMode: (mode) => set((state) => {
    if (!state.project) return state;
    return {
      project: {
        ...state.project,
        currentMode: mode,
      },
    };
  }),
}));

// UI State
interface UIState {
  sidebarOpen: boolean;
  coScientistOpen: boolean;
  activeViewers: Array<{
    id: string;
    type: "pdb" | "pdf" | "image" | "text" | "sequence";
    title: string;
    content?: string;
    fileUrl?: string;
    position: { x: number; y: number };
    size: { width: number; height: number };
    minimized: boolean;
  }>;
  selectedNode: GraphNode | null;
  selectedEdge: GraphEdge | null;
  
  toggleSidebar: () => void;
  toggleCoScientist: () => void;
  openViewer: (viewer: UIState["activeViewers"][0]) => void;
  closeViewer: (id: string) => void;
  updateViewerPosition: (id: string, position: { x: number; y: number }) => void;
  updateViewerSize: (id: string, size: { width: number; height: number }) => void;
  minimizeViewer: (id: string) => void;
  restoreViewer: (id: string) => void;
  setSelectedNode: (node: GraphNode | null) => void;
  setSelectedEdge: (edge: GraphEdge | null) => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  coScientistOpen: false,
  activeViewers: [],
  selectedNode: null,
  selectedEdge: null,
  
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  toggleCoScientist: () => set((state) => ({ coScientistOpen: !state.coScientistOpen })),
  
  openViewer: (viewer) => set((state) => ({
    activeViewers: state.activeViewers.some((v) => v.id === viewer.id)
      ? state.activeViewers
      : [...state.activeViewers, viewer],
  })),
  
  closeViewer: (id) => set((state) => ({
    activeViewers: state.activeViewers.filter((v) => v.id !== id),
  })),
  
  updateViewerPosition: (id, position) => set((state) => ({
    activeViewers: state.activeViewers.map((v) =>
      v.id === id ? { ...v, position } : v
    ),
  })),
  
  updateViewerSize: (id, size) => set((state) => ({
    activeViewers: state.activeViewers.map((v) =>
      v.id === id ? { ...v, size } : v
    ),
  })),
  
  minimizeViewer: (id) => set((state) => ({
    activeViewers: state.activeViewers.map((v) =>
      v.id === id ? { ...v, minimized: true } : v
    ),
  })),
  
  restoreViewer: (id) => set((state) => ({
    activeViewers: state.activeViewers.map((v) =>
      v.id === id ? { ...v, minimized: false } : v
    ),
  })),
  
  setSelectedNode: (node) => set({ selectedNode: node, selectedEdge: null }),
  setSelectedEdge: (edge) => set({ selectedEdge: edge, selectedNode: null }),
}));
