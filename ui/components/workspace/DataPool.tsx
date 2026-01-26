"use client";

import React, { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { v4 as uuidv4 } from "uuid";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
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
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Plus,
  Upload,
  FileText,
  Image as ImageIcon,
  Box,
  FileCode,
  Trash2,
  Eye,
  Loader2,
  File,
  MessageSquare,
  Target,
} from "lucide-react";
import { cn, getFileType } from "@/lib/utils";
import type { DataPoolItem, Project } from "@/lib/types";
import { api } from "@/lib/api";

interface DataPoolProps {
  items: DataPoolItem[];
  onAddItem: (item: Omit<DataPoolItem, "_id" | "addedBy" | "addedAt">) => Promise<void>;
  onRemoveItem: (itemId: string) => Promise<void>;
  onViewItem: (item: DataPoolItem) => void;
  isReadOnly?: boolean;
  projectId?: string;
  project?: Project;
  onUpdateProject?: (data: Partial<Project>) => Promise<void>;
}

const FILE_TYPE_ICONS: Record<string, React.ReactNode> = {
  pdb: <Box className="h-5 w-5 text-emerald-500" />,
  pdf: <FileText className="h-5 w-5 text-red-500" />,
  image: <ImageIcon className="h-5 w-5 text-blue-500" />,
  sequence: <FileCode className="h-5 w-5 text-purple-500" />,
  text: <File className="h-5 w-5 text-amber-500" />,
  other: <File className="h-5 w-5 text-slate-400" />,
};

export function DataPool({
  items,
  onAddItem,
  onRemoveItem,
  onViewItem,
  isReadOnly = false,
  projectId,
  project,
  onUpdateProject,
}: DataPoolProps) {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<Record<string, number>>({});
  const [uploadLogs, setUploadLogs] = useState<string[]>([]);
  const [commentDialogOpen, setCommentDialogOpen] = useState(false);
  const [selectedItem, setSelectedItem] = useState<DataPoolItem | null>(null);
  const [newComment, setNewComment] = useState("");
  const [objectivesDialogOpen, setObjectivesDialogOpen] = useState(false);
  const [mainObjective, setMainObjective] = useState(project?.mainObjective || "");
  const [secondaryObjectives, setSecondaryObjectives] = useState<string[]>(project?.secondaryObjectives || []);
  const [constraints, setConstraints] = useState<string[]>(project?.constraints || []);
  const [notes, setNotes] = useState<string[]>(project?.notes || []);
  const [pendingUploads, setPendingUploads] = useState<Record<string, { name: string; progress: number }>>({});

  // Update objectives when project changes
  React.useEffect(() => {
    if (project) {
      setMainObjective(project.mainObjective || "");
      setSecondaryObjectives(project.secondaryObjectives || []);
      setConstraints(project.constraints || []);
      setNotes(project.notes || []);
    }
  }, [project]);

  const addLog = (message: string) => {
    const timestamp = new Date().toLocaleTimeString();
    setUploadLogs(prev => [...prev, `[${timestamp}] ${message}`]);
    console.log(`[DataPool Upload] ${message}`);
  };



  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      setIsUploading(true);
      setUploadLogs([]);
      addLog(`🚀 Starting upload of ${acceptedFiles.length} file(s)`);
      
      // Create pending uploads immediately
      acceptedFiles.forEach((file) => {
        const fileId = `${file.name}_${Date.now()}`;
        setPendingUploads(prev => ({ ...prev, [fileId]: { name: file.name, progress: 0 } }));
      });
      
      for (const file of acceptedFiles) {
        const fileId = `${file.name}_${Date.now()}`;
        addLog(`📂 Processing file: ${file.name} (${Math.round(file.size / 1024)}KB)`);
        
        // Check file size limits to prevent memory crashes
        const maxSize = 50 * 1024 * 1024; // 50MB limit
        if (file.size > maxSize) {
          addLog(`❌ File "${file.name}" rejected: too large (${Math.round(file.size / (1024*1024))}MB)`);
          alert(`File "${file.name}" is too large (${Math.round(file.size / (1024*1024))}MB). Maximum size is 50MB.`);
          setPendingUploads(prev => {
            const updated = { ...prev };
            delete updated[fileId];
            return updated;
          });
          continue;
        }
        
        const type = getFileType(file.name);
        addLog(`🔍 Detected file type: ${type}`);
        
        // Extra limits for FASTA files due to processing overhead
        if (type === "sequence" && file.size > 300 * 1024 * 1024) {
          addLog(`❌ FASTA file "${file.name}" rejected: too large (${Math.round(file.size / (1024*1024))}MB)`);
          alert(`FASTA file "${file.name}" is too large (${Math.round(file.size / (1024*1024))}MB). Maximum size for sequence files is 300MB.`);
          setPendingUploads(prev => {
            const updated = { ...prev };
            delete updated[fileId];
            return updated;
          });
          continue;
        }
        
        setUploadProgress(prev => ({ ...prev, [fileId]: 0 }));
        
        const reader = new FileReader();
        
        reader.onprogress = (event) => {
          if (event.lengthComputable) {
            const progress = (event.loaded / event.total) * 100;
            setUploadProgress(prev => ({ ...prev, [fileId]: progress }));
            if (type === "sequence") {
              addLog(`📄 Reading FASTA file progress: ${Math.round(progress)}%`);
            }
          }
        };

        reader.onload = async () => {
          try {
            addLog(`✅ File read completed: ${file.name}`);
            setPendingUploads(prev => ({ ...prev, [fileId]: { name: file.name, progress: 100 } }));
            
            const content = reader.result as string;
            addLog(`📊 Content length: ${content.length} characters`);
            
            let processedContent: string;
            if (type === "image" || type === "pdf") {
              if (content.startsWith("data:")) {
                const parts = content.split(",");
                if (parts.length === 2) {
                  processedContent = parts[1];
                  addLog(`🔄 Extracted base64 content (${processedContent.length} chars)`);
                } else {
                  addLog(`❌ Invalid data URL format for ${type}`);
                  throw new Error(`Invalid data URL format for ${type} file`);
                }
              } else {
                addLog(`❌ Expected data URL for ${type}, got: ${content.substring(0, 50)}...`);
                throw new Error(`Expected data URL for ${type} file`);
              }
            } else {
              processedContent = content;
            }

            addLog(`💾 Adding to data pool: ${file.name} (${processedContent.length} chars)`);
            await onAddItem({
              type: type as DataPoolItem["type"],
              name: file.name,
              description: "",
              content: processedContent,
            });
            
            addLog(`🎉 Successfully added: ${file.name}`);
            setPendingUploads(prev => {
              const updated = { ...prev };
              delete updated[fileId];
              return updated;
            });
          } catch (error) {
            addLog(`❌ Error processing ${file.name}: ${error}`);
            console.error(`Error processing file ${file.name}:`, error);
            alert(`Failed to process file "${file.name}". It may be too large or corrupted.`);
            setPendingUploads(prev => {
              const updated = { ...prev };
              delete updated[fileId];
              return updated;
            });
          }
        };
        
        reader.onerror = () => {
          addLog(`❌ Error reading file: ${file.name}`);
          console.error(`Error reading file ${file.name}`);
          alert(`Failed to read file "${file.name}".`);
          setPendingUploads(prev => {
            const updated = { ...prev };
            delete updated[fileId];
            return updated;
          });
        };

        reader.onprogress = (event) => {
          if (event.lengthComputable) {
            const progress = (event.loaded / event.total) * 100;
            setPendingUploads(prev => ({ ...prev, [fileId]: { name: file.name, progress } }));
            if (type === "sequence") {
              addLog(`📄 Reading FASTA file progress: ${Math.round(progress)}%`);
            }
          }
        };

        if (type === "image" || type === "pdf") {
          reader.readAsDataURL(file);
        } else {
          reader.readAsText(file);
        }
      }
      addLog(`🎉 Upload batch completed`);
      setIsUploading(false);
      // Clear logs after 5 seconds
      setTimeout(() => setUploadLogs([]), 5000);
    },
    [onAddItem]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    disabled: isReadOnly,
    maxSize: 50 * 1024 * 1024, // 50MB limit
  });

  const handleAddComment = async () => {
    if (!selectedItem || !newComment.trim()) return;
    
    try {
      if (projectId) {
        await api.projects.addComment(projectId, selectedItem._id, newComment);
      }
    } catch (error) {
      console.error('Failed to add comment:', error);
    }
    
    setNewComment("");
    setCommentDialogOpen(false);
    setSelectedItem(null);
  };

  const handleDeleteComment = async (itemId: string, commentId: string) => {
    try {
      if (projectId) {
        await api.projects.deleteComment(projectId, itemId, commentId);
      }
    } catch (error) {
      console.error('Failed to delete comment:', error);
    }
  };

  const addSecondaryObjective = async () => {
    const updated = [...secondaryObjectives, ""];
    setSecondaryObjectives(updated);
    // Save immediately after adding
    if (onUpdateProject) {
      await onUpdateProject({
        mainObjective,
        secondaryObjectives: updated,
      });
    }
  };

  const updateSecondaryObjective = (index: number, value: string) => {
    const updated = [...secondaryObjectives];
    updated[index] = value;
    setSecondaryObjectives(updated);
  };

  const removeSecondaryObjective = (index: number) => {
    const updated = secondaryObjectives.filter((_, i) => i !== index);
    setSecondaryObjectives(updated);
    // Save immediately after removing
    if (onUpdateProject) {
      onUpdateProject({
        mainObjective,
        secondaryObjectives: updated,
      });
    }
  };

  const addConstraint = async () => {
    const updated = [...constraints, ""];
    setConstraints(updated);
    if (onUpdateProject) {
      await onUpdateProject({
        constraints: updated,
      });
    }
  };

  const updateConstraint = (index: number, value: string) => {
    const updated = [...constraints];
    updated[index] = value;
    setConstraints(updated);
  };

  const removeConstraint = (index: number) => {
    const updated = constraints.filter((_, i) => i !== index);
    setConstraints(updated);
    if (onUpdateProject) {
      onUpdateProject({
        constraints: updated,
      });
    }
  };

  const addNote = async () => {
    const updated = [...notes, ""];
    setNotes(updated);
    if (onUpdateProject) {
      await onUpdateProject({
        notes: updated,
      });
    }
  };

  const updateNote = (index: number, value: string) => {
    const updated = [...notes];
    updated[index] = value;
    setNotes(updated);
  };

  const removeNote = (index: number) => {
    const updated = notes.filter((_, i) => i !== index);
    setNotes(updated);
    if (onUpdateProject) {
      onUpdateProject({
        notes: updated,
      });
    }
  };

  const saveObjectives = async () => {
    if (onUpdateProject) {
      await onUpdateProject({
        mainObjective,
        secondaryObjectives,
        constraints,
        notes,
      });
    }
  };

  const openCommentDialog = (item: DataPoolItem) => {
    setSelectedItem(item);
    setCommentDialogOpen(true);
  };



  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="border-b border-gray-700 bg-gradient-to-r from-gray-900 to-gray-800 px-6 py-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="space-y-1">
            <h2 className="text-2xl font-bold text-green-100 tracking-tight">Data Pool</h2>
            <p className="text-sm text-gray-400 flex items-center gap-2">
              <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-green-500/20 text-green-400 text-xs font-medium">
                {items.length}
              </span>
              {items.length === 1 ? "item" : "items"} in your research pool
            </p>
          </div>
          {!isReadOnly && (
            <Dialog open={objectivesDialogOpen} onOpenChange={setObjectivesDialogOpen}>
              <DialogTrigger asChild>
                <Button 
                  size="lg" 
                  className="bg-green-600 hover:bg-green-700 text-white shadow-lg transition-all duration-200 hover:scale-105"
                >
                  <Target className="mr-2 h-5 w-5" />
                  Manage Objectives
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-gray-900 border-gray-800 max-w-2xl max-h-[80vh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle className="text-green-100">Project Objectives</DialogTitle>
                  <DialogDescription className="text-gray-400">
                    Define and manage your research objectives, constraints, and notes
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-6 py-4">
                  <div className="space-y-2">
                    <Label className="text-gray-300">Main Objective</Label>
                    <Textarea
                      placeholder="Enter the main objective for this project..."
                      value={mainObjective}
                      onChange={(e) => setMainObjective(e.target.value)}
                      onBlur={saveObjectives}
                      className="bg-gray-900 border-gray-600 text-gray-100 min-h-[80px]"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label className="text-gray-300">Secondary Objectives</Label>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={addSecondaryObjective}
                        className="border-gray-600 text-gray-300 hover:bg-gray-700"
                      >
                        <Plus className="h-3 w-3 mr-1" />
                        Add
                      </Button>
                    </div>
                    {secondaryObjectives.map((objective, index) => (
                      <div key={index} className="flex gap-2">
                        <Textarea
                          placeholder={`Secondary objective ${index + 1}...`}
                          value={objective}
                          onChange={(e) => updateSecondaryObjective(index, e.target.value)}
                          onBlur={saveObjectives}
                          className="bg-gray-900 border-gray-600 text-gray-100 min-h-[60px]"
                        />
                        <Button
                          size="icon"
                          variant="ghost"
                          onClick={() => removeSecondaryObjective(index)}
                          className="text-red-400 hover:bg-red-950 hover:text-red-300 mt-1"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    ))}
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label className="text-gray-300">Constraints</Label>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={addConstraint}
                        className="border-gray-600 text-gray-300 hover:bg-gray-700"
                      >
                        <Plus className="h-3 w-3 mr-1" />
                        Add
                      </Button>
                    </div>
                    {constraints.map((constraint, index) => (
                      <div key={index} className="flex gap-2">
                        <Textarea
                          placeholder={`Constraint ${index + 1}...`}
                          value={constraint}
                          onChange={(e) => updateConstraint(index, e.target.value)}
                          onBlur={saveObjectives}
                          className="bg-gray-900 border-gray-600 text-gray-100 min-h-[60px]"
                        />
                        <Button
                          size="icon"
                          variant="ghost"
                          onClick={() => removeConstraint(index)}
                          className="text-red-400 hover:bg-red-950 hover:text-red-300 mt-1"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    ))}
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label className="text-gray-300">Notes</Label>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={addNote}
                        className="border-gray-600 text-gray-300 hover:bg-gray-700"
                      >
                        <Plus className="h-3 w-3 mr-1" />
                        Add
                      </Button>
                    </div>
                    {notes.map((note, index) => (
                      <div key={index} className="flex gap-2">
                        <Textarea
                          placeholder={`Note ${index + 1}...`}
                          value={note}
                          onChange={(e) => updateNote(index, e.target.value)}
                          onBlur={saveObjectives}
                          className="bg-gray-900 border-gray-600 text-gray-100 min-h-[60px]"
                        />
                        <Button
                          size="icon"
                          variant="ghost"
                          onClick={() => removeNote(index)}
                          className="text-red-400 hover:bg-red-950 hover:text-red-300 mt-1"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    ))}
                  </div>
                </div>
              </DialogContent>
            </Dialog>
          )}
          </div>
      {/* Drop Zone */}
      {!isReadOnly && (
        <div className="px-6 py-6">
          <div
            {...getRootProps()}
            className={cn(
              "cursor-pointer rounded-xl border-2 border-dashed border-gray-600 bg-gradient-to-br from-gray-800/50 to-gray-900/50 p-8 text-center transition-all duration-300 hover:border-green-500/50 hover:bg-green-950/10",
              isDragActive && "border-green-400 bg-green-950/20 shadow-lg shadow-green-500/20 scale-[1.02]"
            )}
          >
            <input {...getInputProps()} />
            <div className="space-y-4">
              <div className={cn(
                "mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-gray-700/50 transition-all duration-300",
                isDragActive && "bg-green-600/20 scale-110"
              )}>
                <Upload className={cn(
                  "h-8 w-8 text-gray-400 transition-colors duration-300",
                  isDragActive && "text-green-400"
                )} />
              </div>
              <div className="space-y-2">
                <p className="text-lg font-semibold text-gray-200">
                  {isDragActive
                    ? "Drop your files here"
                    : "Upload Research Data"}
                </p>
                <p className="text-sm text-gray-400">
                  Drag & drop files or click to browse your computer
                </p>
                <div className="flex flex-wrap justify-center gap-2 text-xs text-gray-500">
                  <span className="inline-block px-2 py-1 rounded bg-gray-700/30">PDB</span>
                  <span className="inline-block px-2 py-1 rounded bg-gray-700/30">CIF</span>
                  <span className="inline-block px-2 py-1 rounded bg-gray-700/30">PDF</span>
                  <span className="inline-block px-2 py-1 rounded bg-gray-700/30">Images</span>
                  <span className="inline-block px-2 py-1 rounded bg-gray-700/30">FASTA</span>
                  <span className="inline-block px-2 py-1 rounded bg-gray-700/30">Text</span>
                </div>
                <p className="text-xs text-orange-400 font-medium">
                  Max: 50MB (300MB for FASTA)
                </p>
              </div>
            </div>
          
            {/* Upload Logs */}
            {uploadLogs.length > 0 && (
              <div className="mt-6 p-4 bg-gray-800/80 backdrop-blur-sm rounded-lg border border-gray-700">
                <h4 className="text-xs font-semibold text-gray-300 mb-2">Upload Progress</h4>
                <div className="max-h-32 overflow-y-auto space-y-1">
                  {uploadLogs.map((log, idx) => (
                    <div key={idx} className="text-xs font-mono text-gray-400 leading-relaxed">{log}</div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )},

      {/* Items List */}
      <div className="flex-1 px-6 py-6">
        {items.length === 0 && Object.keys(pendingUploads).length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <div className="w-20 h-20 rounded-full bg-gray-700/30 flex items-center justify-center mb-6">
              <File className="h-10 w-10 text-gray-500" />
            </div>
            <h3 className="text-lg font-semibold text-gray-300 mb-2">
              Your data pool is empty
            </h3>
            <p className="text-sm text-gray-400 max-w-md">
              Upload research files to start building your data collection. Drag and drop files above to get started.
            </p>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-1 lg:grid-cols-2 xl:grid-cols-3">
            {/* Pending Uploads */}
            {Object.entries(pendingUploads).map(([fileId, upload]) => (
              <Card key={fileId} className="overflow-hidden bg-gradient-to-r from-blue-900/20 to-blue-800/20 border border-blue-500/30 border-dashed backdrop-blur-sm">
                <CardHeader className="p-5">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="flex-shrink-0">
                      <div className="w-10 h-10 rounded-full bg-blue-500/20 flex items-center justify-center">
                        <Loader2 className="h-5 w-5 text-blue-400 animate-spin" />
                      </div>
                    </div>
                    <div className="flex-1 min-w-0">
                      <CardTitle className="text-sm font-semibold text-blue-100 truncate">
                        {upload.name}
                      </CardTitle>
                      <p className="text-xs text-blue-300/80">Uploading to data pool...</p>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between text-xs font-medium">
                      <span className="text-gray-300">Progress</span>
                      <span className="text-blue-400">{Math.round(upload.progress)}%</span>
                    </div>
                    <div className="w-full bg-gray-700/50 rounded-full h-2.5 overflow-hidden">
                      <div 
                        className="bg-gradient-to-r from-blue-500 to-blue-400 h-full rounded-full transition-all duration-500 ease-out" 
                        style={{ width: `${upload.progress}%` }}
                      />
                    </div>
                  </div>
                </CardHeader>
              </Card>
            ))}
            
            {/* Regular Items */}
            {items.map((item) => (
              <div key={item._id} className="space-y-3">
                <Card className="overflow-hidden bg-gradient-to-br from-gray-800/80 to-gray-900/80 border-gray-600 hover:border-gray-500 transition-all duration-300 hover:shadow-lg hover:shadow-green-500/10 group">
                  <CardHeader className="p-5">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex items-start gap-4 flex-1 min-w-0">
                        <div className="flex-shrink-0">
                          <div className="w-12 h-12 rounded-xl bg-gray-700/50 flex items-center justify-center group-hover:bg-gray-700/70 transition-colors">
                            {FILE_TYPE_ICONS[item.type] || FILE_TYPE_ICONS.other}
                          </div>
                        </div>
                        <div className="flex-1 min-w-0 space-y-1">
                          <CardTitle className="text-base font-semibold text-green-100 truncate group-hover:text-green-50 transition-colors">
                            {item.name}
                          </CardTitle>
                          {item.description && (
                            <p className="text-sm text-gray-400 line-clamp-2 leading-relaxed">
                              {item.description}
                            </p>
                          )}
                          <div className="flex items-center gap-2 pt-1">
                            <Badge variant="secondary" className="text-xs px-2 py-1 bg-gray-700/60 text-gray-300 border-0">
                              {item.type.toUpperCase()}
                            </Badge>
                          </div>
                        </div>
                      </div>
                      <div className="flex flex-col sm:flex-row items-center gap-2">
                        <Button
                          size="icon"
                          variant="ghost"
                          className="h-9 w-9 text-gray-400 hover:text-green-400 hover:bg-green-950/30 transition-all"
                          onClick={() => onViewItem(item)}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button
                          size="icon"
                          variant="ghost"
                          className="h-9 w-9 text-gray-400 hover:text-blue-400 hover:bg-blue-950/30 transition-all"
                          onClick={() => openCommentDialog(item)}
                        >
                          <MessageSquare className="h-4 w-4" />
                        </Button>
                        {!isReadOnly && (
                          <Button
                            size="icon"
                            variant="ghost"
                            className="h-9 w-9 text-gray-400 hover:text-red-400 hover:bg-red-950/30 transition-all"
                            onClick={() => onRemoveItem(item._id)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                    </div>
                    {item.content && item.type === "text" && (
                      <div className="mt-4 pt-4 border-t border-gray-700/50">
                        <div className="bg-gray-900/50 rounded-lg p-3">
                          <p className="text-xs text-gray-300 font-mono leading-relaxed line-clamp-3">
                            {item.content}
                          </p>
                        </div>
                      </div>
                    )}
                  </CardHeader>
                </Card>
                
                {/* Comments */}
                {item.comments && item.comments.length > 0 && (
                  <div className="mt-4 space-y-3">
                    <div className="text-xs font-medium text-gray-400 px-1">Comments ({item.comments.length})</div>
                    <div className="space-y-3">
                      {item.comments.map((comment, idx) => (
                        <div key={idx} className="bg-gray-800/60 backdrop-blur-sm border border-gray-700/50 rounded-xl p-4 transition-all hover:bg-gray-800/80">
                          <div className="flex justify-between items-start gap-3">
                            <div className="flex-1 space-y-2">
                              <div className="flex items-center gap-3">
                                <div className="w-6 h-6 rounded-full bg-blue-500/20 flex items-center justify-center">
                                  <span className="text-xs font-medium text-blue-400">
                                    {typeof comment.author === 'object' ? comment.author.name.charAt(0).toUpperCase() : comment.author.charAt(0).toUpperCase()}
                                  </span>
                                </div>
                                <div className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-3">
                                  <span className="text-sm font-medium text-blue-300">
                                    {typeof comment.author === 'object' ? comment.author.name : comment.author}
                                  </span>
                                  <span className="text-xs text-gray-500">
                                    {new Date(comment.createdAt).toLocaleDateString('en-US', { 
                                      month: 'short', 
                                      day: 'numeric', 
                                      hour: '2-digit', 
                                      minute: '2-digit' 
                                    })}
                                  </span>
                                </div>
                              </div>
                              <p className="text-sm text-gray-300 leading-relaxed pl-9">{comment.text}</p>
                            </div>
                            {!isReadOnly && (
                              <Button
                                size="icon"
                                variant="ghost"
                                className="h-8 w-8 text-gray-400 hover:text-red-400 hover:bg-red-950/30 transition-all flex-shrink-0"
                                onClick={() => handleDeleteComment(item._id, comment._id)}
                              >
                                <Trash2 className="h-3 w-3" />
                              </Button>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
      
      {/* Comment Dialog */}
      <Dialog open={commentDialogOpen} onOpenChange={setCommentDialogOpen}>
        <DialogContent className="bg-gray-900 border-gray-700 max-w-2xl">
          <DialogHeader className="space-y-3">
            <DialogTitle className="text-xl font-semibold text-green-100">Add Comment</DialogTitle>
            <DialogDescription className="text-gray-400">
              Share your thoughts on <span className="font-medium text-gray-300">{selectedItem?.name}</span>
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-6 py-4">
            <div className="space-y-3">
              <Label className="text-base font-medium text-gray-300">Your Comment</Label>
              <Textarea
                placeholder="Share insights, observations, or questions about this data..."
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                className="bg-gray-800/50 border-gray-600 text-gray-100 min-h-[120px] resize-none focus:border-green-500/50 focus:ring-green-500/20 transition-all"
              />
            </div>
            {selectedItem?.comments && selectedItem.comments.length > 0 && (
              <div className="space-y-3">
                <Label className="text-base font-medium text-gray-300">Previous Comments ({selectedItem.comments.length})</Label>
                <ScrollArea className="h-48 bg-gray-800/30 border border-gray-700/50 rounded-xl p-4">
                  <div className="space-y-4">
                    {selectedItem.comments.map((comment, idx) => (
                      <div key={idx} className="space-y-2 pb-4 border-b border-gray-700/30 last:border-b-0 last:pb-0">
                        <div className="flex items-center gap-3">
                          <div className="w-6 h-6 rounded-full bg-blue-500/20 flex items-center justify-center">
                            <span className="text-xs font-medium text-blue-400">
                              {typeof comment.author === 'object' ? comment.author.name.charAt(0).toUpperCase() : comment.author.charAt(0).toUpperCase()}
                            </span>
                          </div>
                          <div className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-2">
                            <span className="text-sm font-medium text-blue-300">
                              {typeof comment.author === 'object' ? comment.author.name : comment.author}
                            </span>
                            <span className="text-xs text-gray-500">
                              {new Date(comment.createdAt).toLocaleDateString('en-US', { 
                                month: 'short', 
                                day: 'numeric', 
                                hour: '2-digit', 
                                minute: '2-digit' 
                              })}
                            </span>
                          </div>
                        </div>
                        <p className="text-sm text-gray-300 leading-relaxed pl-9">{comment.text}</p>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </div>
            )}
          </div>
          <DialogFooter className="gap-3">
            <Button
              variant="outline"
              onClick={() => setCommentDialogOpen(false)}
              className="border-gray-600 text-gray-300 hover:bg-gray-800 hover:border-gray-500"
            >
              Cancel
            </Button>
            <Button
              onClick={handleAddComment}
              disabled={!newComment.trim()}
              className="bg-green-600 hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              Add Comment
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
    </div>
  );
}
