"use client";

import React, { useCallback, useMemo, useState, useContext, createContext } from "react";
import { projectsApi } from "@/lib/api";
import {
  ReactFlow,
  Node,
  Edge,
  Controls,
  Background,
  MiniMap,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  Panel,
  NodeTypes,
  EdgeTypes,
  MarkerType,
  Handle,
  Position,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import {
  Plus,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Eye,
  Trash2,
  MessageSquare,
  AlertTriangle,
  Check,
  X,
  Box,
  FileText,
  Image as ImageIcon,
  FileCode,
  File,
  Link as LinkIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { GraphNode, GraphEdge, KnowledgeGraph } from "@/lib/types";
import { v4 as uuidv4 } from "uuid";

interface KnowledgeGraphViewProps {
  graph: KnowledgeGraph;
  onNodeAdd: (node: GraphNode) => void;
  onNodeUpdate: (node: GraphNode) => void;
  onNodeRemove: (nodeId: string, reason?: string) => void;
  onEdgeAdd: (edge: GraphEdge) => void;
  onEdgeRemove: (edgeId: string) => void;
  onNodeView: (node: GraphNode) => void;
  isReadOnly?: boolean;
}

const NODE_COLORS: Record<string, { bg: string; border: string }> = {
  pdb: { bg: "#dcfce7", border: "#22c55e" },
  pdf: { bg: "#fee2e2", border: "#ef4444" },
  image: { bg: "#dbeafe", border: "#3b82f6" },
  sequence: { bg: "#ede9fe", border: "#8b5cf6" },
  text: { bg: "#fef3c7", border: "#f59e0b" },
  retrieved: { bg: "#f1f5f9", border: "#64748b" },
  annotation: { bg: "#fce7f3", border: "#ec4899" },
};

const TRUST_COLORS: Record<string, string> = {
  high: "#22c55e",
  medium: "#f59e0b",
  low: "#ef4444",
  untrusted: "#6b7280",
};

const NODE_ICONS: Record<string, React.ReactNode> = {
  pdb: <Box className="h-4 w-4" />,
  pdf: <FileText className="h-4 w-4" />,
  image: <ImageIcon className="h-4 w-4" />,
  sequence: <FileCode className="h-4 w-4" />,
  text: <File className="h-4 w-4" />,
  retrieved: <LinkIcon className="h-4 w-4" />,
  annotation: <MessageSquare className="h-4 w-4" />,
};

// Context for expand logic
const ExpandPromptContext = createContext<{
  expandedNodeId: string | null;
  setExpandedNodeId: (id: string | null) => void;
}>({ expandedNodeId: null, setExpandedNodeId: () => {} });

// Custom Node Component
function CustomNode({ data, selected }: {
  data: GraphNode & { onView: () => void; onSelect: () => void };
  selected: boolean;
}) {
  const { expandedNodeId, setExpandedNodeId } = useContext(ExpandPromptContext);
  const colors = NODE_COLORS[data.type] || NODE_COLORS.text;
  const trustColor = TRUST_COLORS[data.trustLevel];
  const [expandPrompt, setExpandPrompt] = useState("");
  const isExpanded = expandedNodeId === data.id;

  return (
    <div
      className={cn(
        "relative cursor-pointer rounded-lg border-2 px-4 py-3 shadow-sm transition-all",
        selected && "ring-2 ring-blue-500 ring-offset-2"
      )}
      style={{
        backgroundColor: colors.bg,
        borderColor: colors.border,
        minWidth: 150,
        maxWidth: 200,
      }}
      onClick={data.onSelect}
      onDoubleClick={data.onView}
    >
      {/* Trust indicator */}
      <div
        className="absolute -right-1 -top-1 h-3 w-3 rounded-full border-2 border-white"
        style={{ backgroundColor: trustColor }}
        title={`Trust: ${data.trustLevel}`}
      />

      {/* Expand circle */}
      <div
        className="absolute -left-4 top-1 flex items-center justify-center"
        style={{ width: 24, height: 24 }}
      >
        <div
          className="flex items-center justify-center rounded-full bg-green-600 border-2 border-white shadow cursor-pointer"
          style={{ width: 20, height: 20 }}
          onClick={e => { e.stopPropagation(); setExpandedNodeId(isExpanded ? null : data.id); }}
        >
          <Plus className="h-4 w-4 text-white" />
        </div>
      </div>

      {/* Content */}
      <div className="flex items-start gap-2">
        <span style={{ color: colors.border }}>{NODE_ICONS[data.type]}</span>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium truncate" style={{ color: '#1e293b' }}>{data.id}</p>
          {data.description && (
            <p className="text-xs text-gray-400 line-clamp-2 mt-1">
              {data.description}
            </p>
          )}
        </div>
      </div>

      {/* Notes indicator */}
      {data.notes && data.notes.length > 0 && (
        <div className="mt-2 flex items-center gap-1 text-xs text-gray-400">
          <MessageSquare className="h-3 w-3" />
          {data.notes.length} note{data.notes.length !== 1 ? "s" : ""}
        </div>
      )}

      {/* Expand prompt */}
      {isExpanded && (
        <div className="absolute left-1/2 top-full z-10 -translate-x-1/2 mt-2 w-48 rounded-lg bg-white shadow-lg p-2 flex flex-col gap-2">
          <input
            className="border rounded px-2 py-1 text-sm"
            placeholder="Expand prompt..."
            value={expandPrompt}
            onChange={e => setExpandPrompt(e.target.value)}
          />
          <button
            className="bg-green-600 text-white rounded px-2 py-1 text-sm"
            onClick={() => { setExpandedNodeId(null); setExpandPrompt(""); /* TODO: call backend */ }}
          >
            Expand
          </button>
        </div>
      )}

      {/* Handles */}
      <Handle type="target" position={Position.Top} className="!bg-green-500" />
      <Handle type="source" position={Position.Bottom} className="!bg-green-500" />
    </div>
  );
}

const nodeTypes: NodeTypes = {
  custom: CustomNode,
};


export function KnowledgeGraphView({
  graph: initialGraph,
  onNodeAdd,
  onNodeUpdate,
  onNodeRemove,
  onEdgeAdd,
  onEdgeRemove,
  onNodeView,
  isReadOnly = false,
}: KnowledgeGraphViewProps) {
  const [graph, setGraph] = useState<KnowledgeGraph>(initialGraph);
  const [loading, setLoading] = useState(false);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<GraphEdge | null>(null);
  const [isAddNodeOpen, setIsAddNodeOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [deleteReason, setDeleteReason] = useState("");
  const [newNote, setNewNote] = useState("");
  const [expandedNodeId, setExpandedNodeId] = useState<string | null>(null);

  const [newNode, setNewNode] = useState({
    type: "text" as GraphNode["type"],
    label: "",
    description: "",
    content: "",
  });

  // Fetch knowledge graph on mount
  React.useEffect(() => {
    async function fetchGraph() {
      setLoading(true);
      try {
        const projectId = getProjectIdFromUrl();
        const res = await projectsApi.get(projectId);
        // Support both { knowledgeGraph: { nodes, edges, groups } } and { knowledgeGraph: { knowledgeGraph: { nodes, edges, groups }, ... } }
        let graphData = null;
        console.log(res.project.knowledgeGraph);
        if (res && res.project) {
          if (res.project.knowledgeGraph && Array.isArray(res.project.knowledgeGraph.nodes)) {
            graphData = res.project.knowledgeGraph;
          } else if (
            res.project.knowledgeGraph &&
            res.project.knowledgeGraph.knowledgeGraph &&
            Array.isArray(res.project.knowledgeGraph.knowledgeGraph.nodes)
          ) {
            graphData = res.project.knowledgeGraph.knowledgeGraph;
          }
        }
        if (graphData) {
          setGraph(graphData);
        } else {
          setGraph({ nodes: [], edges: [], groups: [] });
        }
      } finally {
        setLoading(false);
      }
    }
    fetchGraph();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // --- Auto-layout for node positions ---
  function autoLayoutNodes(nodes: GraphNode[], edges: GraphEdge[]): { [id: string]: { x: number; y: number } } {
    // Improved force-directed layout for better node separation
    const W = 2000, H = 1400; // Larger canvas
    const N = nodes.length;
    if (N === 0) return {};
    let positions: { [id: string]: { x: number; y: number } } = {};
    const spacing = 350; // More space between nodes
    // Initial grid positions
    const cols = Math.ceil(Math.sqrt(N));
    nodes.forEach((node, i) => {
      const row = Math.floor(i / cols);
      const col = i % cols;
      positions[node.id] = {
        x: 200 + col * spacing,
        y: 200 + row * spacing,
      };
    });
    // More iterations for layout
    for (let iter = 0; iter < 200; iter++) {
      // Repulsion (stronger)
      for (let i = 0; i < N; i++) {
        for (let j = i + 1; j < N; j++) {
          const a = nodes[i], b = nodes[j];
          const posA = positions[a.id], posB = positions[b.id];
          let dx = posA.x - posB.x, dy = posA.y - posB.y;
          let dist = Math.sqrt(dx * dx + dy * dy) || 1;
          if (dist < spacing * 1.1) {
            // Push apart more strongly
            const force = (spacing * 1.1 - dist) * 0.25;
            const fx = (dx / dist) * force, fy = (dy / dist) * force;
            posA.x += fx; posA.y += fy;
            posB.x -= fx; posB.y -= fy;
          }
        }
      }
      // Attraction (edges, stronger)
      edges.forEach(edge => {
        const src = positions[edge.source], tgt = positions[edge.target];
        if (!src || !tgt) return;
        let dx = tgt.x - src.x, dy = tgt.y - src.y;
        let dist = Math.sqrt(dx * dx + dy * dy) || 1;
        if (dist > spacing) {
          // Pull together more strongly
          const force = (dist - spacing) * 0.15;
          const fx = (dx / dist) * force, fy = (dy / dist) * force;
          src.x += fx; src.y += fy;
          tgt.x -= fx; tgt.y -= fy;
        }
      });
    }
    // Clamp positions to viewport
    Object.values(positions).forEach(pos => {
      pos.x = Math.max(60, Math.min(W - 60, pos.x));
      pos.y = Math.max(60, Math.min(H - 60, pos.y));
    });
    return positions;
  }

  // Always use auto-layout for node positions, ignore DB positions
  const layoutPositions = useMemo(() => autoLayoutNodes(graph.nodes, graph.edges), [graph.nodes, graph.edges]);

  // Convert graph nodes to ReactFlow nodes
  const initialNodes: Node[] = useMemo(
    () =>
      graph.nodes.map((node) => ({
        id: node.id,
        type: "custom",
        position: layoutPositions[node.id],
        data: {
          ...node,
          onView: () => onNodeView(node),
          onSelect: () => setSelectedNode(node),
        },
      })),
    [graph.nodes, onNodeView, layoutPositions]
  );

  // Convert graph edges to ReactFlow edges
  const initialEdges = useMemo(
    () =>
      graph.edges.map((edge) => {
        // Find node names for label (but do not render label on edge)
        const sourceNode = graph.nodes.find(n => n.id === edge.source);
        const targetNode = graph.nodes.find(n => n.id === edge.target);
        // Remove label from edge to prevent anything being printed on top of the edge
        return {
          id: edge.id,
          source: edge.source,
          target: edge.target,
          // label: (removed)
          animated: edge.correlationType === "supports",
          style: {
            stroke:
              edge.correlationType === "contradicts"
                ? "#ef4444"
                : edge.correlationType === "supports"
                ? "#22c55e"
                : "#64748b",
            strokeWidth: edge.strength * 3,
          },
          markerEnd: {
            type: MarkerType.ArrowClosed,
          },
          data: {
            ...edge,
            sourceLabel: sourceNode?.label,
            targetLabel: targetNode?.label,
          },
        };
      }),
    [graph.edges, graph.nodes]
  );

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const onConnect = useCallback(
    (params: Connection) => {
      if (isReadOnly) return;

      const newEdge: GraphEdge = {
        id: uuidv4(),
        source: params.source!,
        target: params.target!,
        correlationType: "similar",
        strength: 0.5,
      };

      onEdgeAdd(newEdge);
      setEdges((eds) =>
        addEdge(
          {
            ...params,
            id: newEdge.id,
            animated: false,
            style: { stroke: "#64748b", strokeWidth: 1.5 },
            markerEnd: { type: MarkerType.ArrowClosed },
          },
          eds
        )
      );
    },
    [isReadOnly, onEdgeAdd, setEdges]
  );

  const handleAddNode = () => {
    if (!newNode.label) return;

    const node: GraphNode = {
      id: uuidv4(),
      type: newNode.type,
      label: newNode.label,
      description: newNode.description,
      content: newNode.content,
      position: { x: Math.random() * 400 + 100, y: Math.random() * 400 + 100 },
      trustLevel: "medium",
      notes: [],
    };

    onNodeAdd(node);
    setNewNode({ type: "text", label: "", description: "", content: "" });
    setIsAddNodeOpen(false);
  };

  const handleDeleteNode = () => {
    if (!selectedNode) return;
    onNodeRemove(selectedNode.id, deleteReason);
    setSelectedNode(null);
    setIsDeleteDialogOpen(false);
    setDeleteReason("");
  };


  // Utility to get projectId from URL
  function getProjectIdFromUrl() {
    if (typeof window !== 'undefined') {
      const parts = window.location.pathname.split("/");
      // Find the index of 'project' and return the next segment as the ID
      const idx = parts.findIndex((p) => p === 'project');
      if (idx !== -1 && parts.length > idx + 1) {
        return parts[idx + 1];
      }
    }
    return "";
  }


  const [pendingTrust, setPendingTrust] = useState<GraphNode["trustLevel"] | null>(null);
  const [trustSaving, setTrustSaving] = useState(false);
  const [noteSaving, setNoteSaving] = useState(false);

  const handleTrustChange = (trust: GraphNode["trustLevel"]) => {
    setPendingTrust(trust);
  };

  const handleSaveTrust = async () => {
    if (!selectedNode || !pendingTrust) return;
    setTrustSaving(true);
    try {
      const projectId = getProjectIdFromUrl();
      // Only send the trustLevel field
      await projectsApi.updateNode(
        projectId,
        selectedNode.id,
        { trustLevel: pendingTrust }
      );
      const updatedNode = { ...selectedNode, trustLevel: pendingTrust };
      onNodeUpdate(updatedNode);
      setSelectedNode(updatedNode);
      setPendingTrust(null);
    } finally {
      setTrustSaving(false);
    }
  };

  const handleAddNote = async () => {
    if (!selectedNode || !newNote.trim()) return;
    setNoteSaving(true);
    try {
      const projectId = getProjectIdFromUrl();
      const res = await projectsApi.addNodeNote(projectId, selectedNode.id, newNote);
      // Find the updated node from the returned project
      const updatedNode = res.project.knowledgeGraph.nodes.find((n: any) => n.id === selectedNode.id);
      if (updatedNode) {
        onNodeUpdate(updatedNode);
        setSelectedNode(updatedNode);
      }
      setNewNote("");
    } finally {
      setNoteSaving(false);
    }
  };

  return (
    <div className="flex h-full">
      {/* Graph Canvas */}
      <div className="flex-1 bg-gray-900">
        <ExpandPromptContext.Provider value={{ expandedNodeId, setExpandedNodeId }}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            nodeTypes={nodeTypes}
            fitView
            className="bg-gray-900"
            onNodeClick={(_, node) => {
              const graphNode = graph.nodes.find((n) => n.id === node.id);
              if (graphNode) setSelectedNode(graphNode);
              setExpandedNodeId(null);
            }}
            onEdgeClick={(_, edge) => {
              // Use edge.data to get full edge info and node labels
              if (edge.data) {
                setSelectedEdge({
                  ...edge.data,
                  // fallback for label if not present
                } as GraphEdge);
              } else {
                const graphEdge = graph.edges.find((e) => e.id === edge.id);
                if (graphEdge) setSelectedEdge(graphEdge);
              }
              setExpandedNodeId(null);
            }}
            onPaneClick={() => {
              setSelectedNode(null);
              setSelectedEdge(null);
              setExpandedNodeId(null);
            }}
          >
          <Controls />
          <MiniMap
            nodeColor={(node) => {
              const colors = NODE_COLORS[node.data?.type as string] || NODE_COLORS.text;
              return colors.border;
            }}
            maskColor="rgb(17, 24, 39, 0.8)"
          />
          <Background gap={20} size={1} color="#374151" />

          {/* Top Panel */}
          <Panel position="top-left" className="flex gap-2">
            {!isReadOnly && (
              <Button
                size="sm"
                onClick={async () => {
                  try {
                    const projectId = getProjectIdFromUrl();
                    // Fetch the full project (for up-to-date data)
                    const res = await projectsApi.get(projectId);
                    const project = res.project;
                    // Prepare payload: remove knowledgeGraph, coScientistSteps, checkpoints, members, owners, hash
                    const {
                      knowledgeGraph,
                      coScientistSteps,
                      checkpoints,
                      members,
                      owners,
                      hash,
                      ...rest
                    } = project;
                    await projectsApi.retrieveProject(projectId, rest);
                    alert('Retrieve request sent!');
                  } catch (err) {
                    alert('Failed to send retrieve request.');
                  }
                }}
              >
                <Box className="mr-2 h-4 w-4" />
                Retrieve
              </Button>
            )}
          </Panel>

          {/* Legend */}
          <Panel position="bottom-left" className="rounded-lg border border-gray-700 bg-gray-900 p-3 shadow-sm">
            <p className="text-xs font-medium text-gray-300 mb-2">Legend</p>
            <div className="space-y-1">
              {Object.entries(NODE_COLORS).map(([type, colors]) => (
                <div key={type} className="flex items-center gap-2 text-xs text-gray-400">
                  <div
                    className="h-3 w-3 rounded"
                    style={{ backgroundColor: colors.bg, borderColor: colors.border, borderWidth: 1 }}
                  />
                  <span className="capitalize">{type}</span>
                </div>
              ))}
            </div>
          </Panel>
        </ReactFlow>
        </ExpandPromptContext.Provider>
      </div>

      {/* Side Panel */}
      {(selectedNode || selectedEdge) && (
        <div className="w-80 border-l border-gray-800 bg-gray-900">
          <ScrollArea className="h-full">
            {selectedNode && (
              <div className="p-4 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold text-green-100">Node Details</h3>
                  <Button
                    size="icon"
                    variant="ghost"
                    className="h-8 w-8 text-gray-400 hover:bg-gray-800"
                    onClick={() => setSelectedNode(null)}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>

                {/* Node Info */}
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <span style={{ color: NODE_COLORS[selectedNode.type]?.border }}>
                      {NODE_ICONS[selectedNode.type]}
                    </span>
                    <span className="font-medium text-green-100">{selectedNode.id}</span>
                  </div>

                  <Badge variant="secondary" className="bg-gray-800 text-gray-300">{selectedNode.type.toUpperCase()}</Badge>

                  {selectedNode.description && (
                    <p className="text-sm text-gray-400">{selectedNode.description}</p>
                  )}
                </div>

                {/* Actions */}
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    className="flex-1 border-gray-700 text-gray-300 hover:bg-gray-800"
                    onClick={() => { console.log('Node contents:', selectedNode); onNodeView(selectedNode); }}
                  >
                    <Eye className="mr-2 h-4 w-4" />
                    View
                  </Button>
                  {!isReadOnly && (
                    <Button
                      size="sm"
                      variant="outline"
                      className="text-red-500 border-gray-700 hover:bg-red-950"
                      onClick={() => setIsDeleteDialogOpen(true)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  )}
                </div>

                {/* Trust Level */}
                {!isReadOnly && (
                  <div className="space-y-2">
                    <Label className="text-xs text-gray-300">Trust Level</Label>
                    <div className="flex gap-2 items-center">
                      <Select
                        value={pendingTrust ?? selectedNode.trustLevel}
                        onValueChange={(v) => handleTrustChange(v as GraphNode["trustLevel"])}
                      >
                        <SelectTrigger className="h-8 bg-gray-800 border-gray-700 text-gray-100">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="bg-gray-800 border-gray-700">
                          <SelectItem value="high">
                            <span className="flex items-center gap-2">
                              <Check className="h-3 w-3 text-green-500" />
                              High Trust
                            </span>
                          </SelectItem>
                          <SelectItem value="medium">
                            <span className="flex items-center gap-2">
                              <AlertTriangle className="h-3 w-3 text-amber-500" />
                              Medium Trust
                            </span>
                          </SelectItem>
                          <SelectItem value="low">
                            <span className="flex items-center gap-2">
                              <AlertTriangle className="h-3 w-3 text-red-500" />
                              Low Trust
                            </span>
                          </SelectItem>
                          <SelectItem value="untrusted">
                            <span className="flex items-center gap-2">
                              <X className="h-3 w-3 text-gray-500" />
                              Untrusted
                            </span>
                          </SelectItem>
                        </SelectContent>
                      </Select>
                      <Button size="sm" onClick={handleSaveTrust} disabled={trustSaving || !pendingTrust || pendingTrust === selectedNode.trustLevel}>
                        {trustSaving ? "Saving..." : "Save Trust"}
                      </Button>
                    </div>
                  </div>
                )}

                {/* Notes */}
                <div className="space-y-2">
                  <Label className="text-xs text-gray-300">Notes</Label>
                  <div className="space-y-2">
                    {selectedNode.notes.map((note) => (
                      <div
                        key={note.id}
                        className="rounded-lg bg-gray-800 p-2 text-xs text-gray-300"
                      >
                        {note.text}
                      </div>
                    ))}
                    {!isReadOnly && (
                      <div className="flex gap-2">
                        <Input
                          placeholder="Add a note..."
                          value={newNote}
                          onChange={(e) => setNewNote(e.target.value)}
                          className="h-8 text-xs"
                        />
                        <Button size="sm" className="h-8" onClick={handleAddNote} disabled={noteSaving}>
                          {noteSaving ? "Saving..." : "Add"}
                        </Button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {selectedEdge && (
              <div className="p-4 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold text-green-100">Edge Details</h3>
                  <Button
                    size="icon"
                    variant="ghost"
                    className="h-8 w-8 text-gray-400 hover:bg-gray-800"
                    onClick={() => setSelectedEdge(null)}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>

                <div className="space-y-3">
                  <Badge
                    variant={
                      selectedEdge.correlationType === "supports"
                        ? "success"
                        : selectedEdge.correlationType === "contradicts"
                        ? "destructive"
                        : "secondary"
                    }
                  >
                    {selectedEdge.correlationType}
                  </Badge>

                  {/* Provenance (source and target node names) */}
                  <div className="space-y-1">
                    <Label className="text-xs text-gray-300">Provenance: </Label>
                    <span className="text-sm text-green-400">
                      {graph.nodes.find(n => n.id === selectedEdge.source)?.label || selectedEdge.source}
                      {" "} | {" "}
                      {graph.nodes.find(n => n.id === selectedEdge.target)?.label || selectedEdge.target}
                    </span>
                  </div>

                  {/* Similarity score */}
                  <div className="space-y-1">
                    <Label className="text-xs text-gray-300">Similarity Score: </Label>
                    <span className="text-sm text-green-400">
                      {(selectedEdge.strength * 100).toFixed(1)}%
                    </span>
                  </div>

                  {/* Biological Features */}
                  <div className="space-y-1">
                    <Label className="text-xs text-gray-300">Biological Features: </Label>
                    <span className="text-sm text-gray-400">
                      {selectedEdge.metadata.provenance
                        ? selectedEdge.metadata.provenance.biological_features.slice(0, 2).join(" and ")
                        : "-"}
                    </span>
                  </div>

                </div>
              </div>
            )}
          </ScrollArea>
        </div>
      )}

      {/* Add Node Dialog */}
      <Dialog open={isAddNodeOpen} onOpenChange={setIsAddNodeOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Node</DialogTitle>
            <DialogDescription>Add a new element to the knowledge graph</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Type</Label>
              <Select
                value={newNode.type}
                onValueChange={(v) => setNewNode({ ...newNode, type: v as GraphNode["type"] })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="pdb">PDB Structure</SelectItem>
                  <SelectItem value="pdf">PDF Document</SelectItem>
                  <SelectItem value="image">Image</SelectItem>
                  <SelectItem value="sequence">Sequence</SelectItem>
                  <SelectItem value="text">Text Note</SelectItem>
                  <SelectItem value="annotation">Annotation</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Label</Label>
              <Input
                placeholder="Node name..."
                value={newNode.label}
                onChange={(e) => setNewNode({ ...newNode, label: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label>Description</Label>
              <Textarea
                placeholder="Brief description..."
                value={newNode.description}
                onChange={(e) => setNewNode({ ...newNode, description: e.target.value })}
              />
            </div>
          </div>
          <DialogFooter>
            <Button onClick={handleAddNode} disabled={!newNode.label}>
              Add Node
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Remove Node</DialogTitle>
            <DialogDescription>
              This will remove the node from the knowledge graph. Please provide a reason
              to help improve future retrievals.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <Label>Reason for removal</Label>
            <Textarea
              placeholder="e.g., Outdated information, irrelevant to objective..."
              value={deleteReason}
              onChange={(e) => setDeleteReason(e.target.value)}
              className="mt-2"
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDeleteDialogOpen(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleDeleteNode}>
              Remove
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
