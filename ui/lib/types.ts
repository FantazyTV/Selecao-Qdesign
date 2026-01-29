// Types for the QDesign application

export interface User {
  id: string;
  email: string;
  name: string;
  avatar?: string;
}

export interface DataPoolComment {
  _id: string;
  author: {
    _id: string;
    name: string;
    email: string;
  } | string; // Can be populated object or just string ID
  text: string;
  createdAt: string;
}

export interface DataPoolItem {
  _id: string;
  id?: string; // Alias for frontend compatibility
  type: "pdb" | "pdf" | "image" | "sequence" | "text" | "other";
  name: string;
  description?: string;
  content?: string;
  fileUrl?: string;
  url?: string; // Alias for frontend compatibility
  metadata?: Record<string, unknown>;
  addedBy: string;
  addedAt: string;
  comments?: DataPoolComment[];
}

export interface GraphNode {
  id: string;
  type: "pdb" | "pdf" | "image" | "sequence" | "text" | "retrieved" | "annotation";
  label: string;
  description?: string;
  content?: string;
  fileUrl?: string;
  largeFileId?: string; // Optional, for backend compatibility
  position: { x: number; y: number };
  trustLevel: "high" | "medium" | "low" | "untrusted";
  notes: Array<{
    id: string;
    text: string;
    author: string;
    createdAt: string;
  }>;
  metadata?: Record<string, unknown>;
  groupId?: string;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  label?: string;
  correlationType: "similar" | "cites" | "contradicts" | "supports" | "derived" | "custom";
  strength: number;
  explanation?: string;
  metadata?: Record<string, unknown>;
}

export interface KnowledgeGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
  groups: Array<{
    id: string;
    name: string;
    color: string;
  }>;
}

export interface CoScientistStep {
  id: string;
  type: "reasoning" | "evidence" | "hypothesis" | "conclusion" | "question" | "design";
  title: string;
  content: string;
  attachments: Array<{
    type: "pdb" | "pdf" | "image" | "text";
    name: string;
    content?: string;
    fileUrl?: string;
    dataPoolItemId?: string;
  }>;
  comments: Array<{
    id: string;
    text: string;
    author: string;
    createdAt: string;
  }>;
  status: "pending" | "approved" | "rejected" | "modified";
  createdAt: string;
}

export interface Checkpoint {
  _id: string;
  id?: string; // Alias for frontend compatibility
  name: string;
  description?: string;
  mode: "pool" | "retrieval" | "coscientist";
  dataPool: DataPoolItem[];
  knowledgeGraph: KnowledgeGraph;
  coScientistSteps: CoScientistStep[];
  createdBy: string;
  createdAt: string;
}

export interface Project {
  _id: string;
  hash: string;
  name: string;
  mainObjective: string;
  secondaryObjectives: string[];
  constraints: string[];
  notes: string[];
  description?: string;
  owner: string;
  members: Array<{
    user: string | User;
    role: "owner" | "editor" | "viewer";
    joinedAt: string;
  }>;
  currentMode: "pool" | "retrieval" | "coscientist";
  dataPool: DataPoolItem[];
  knowledgeGraph: KnowledgeGraph;
  coScientistSteps: CoScientistStep[];
  checkpoints: Checkpoint[];
  createdAt: string;
  updatedAt: string;
}

// Socket events
export type SocketEvent =
  | { type: "project:update"; payload: Partial<Project> }
  | { type: "pool:add"; payload: DataPoolItem }
  | { type: "pool:remove"; payload: { itemId: string } }
  | { type: "pool:update"; payload: DataPoolItem }
  | { type: "graph:node:add"; payload: GraphNode }
  | { type: "graph:node:update"; payload: GraphNode }
  | { type: "graph:node:remove"; payload: { nodeId: string } }
  | { type: "graph:edge:add"; payload: GraphEdge }
  | { type: "graph:edge:remove"; payload: { edgeId: string } }
  | { type: "coscientist:step:add"; payload: CoScientistStep }
  | { type: "coscientist:step:update"; payload: CoScientistStep }
  | { type: "coscientist:comment:add"; payload: { stepId: string; comment: CoScientistStep["comments"][0] } }
  | { type: "user:joined"; payload: User }
  | { type: "user:left"; payload: { userId: string } }
  | { type: "checkpoint:create"; payload: Checkpoint };

// API Response types
export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

// Graph JSON format expected by frontend
export interface GraphDataFormat {
  nodes: Array<{
    id: string;
    type: GraphNode["type"];
    label: string;
    description?: string;
    content?: string;
    fileUrl?: string;
    x: number;
    y: number;
    trustLevel: GraphNode["trustLevel"];
    notes: GraphNode["notes"];
    metadata?: Record<string, unknown>;
    group?: string;
    // Visual properties
    size?: number;
    color?: string;
  }>;
  edges: Array<{
    id: string;
    source: string;
    target: string;
    label?: string;
    type: GraphEdge["correlationType"];
    strength: number;
    explanation?: string;
    // Visual properties
    color?: string;
    width?: number;
    animated?: boolean;
  }>;
  groups: Array<{
    id: string;
    name: string;
    color: string;
  }>;
}
