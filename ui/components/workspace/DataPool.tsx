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
} from "lucide-react";
import { cn, getFileType } from "@/lib/utils";
import type { DataPoolItem } from "@/lib/types";

interface DataPoolProps {
  items: DataPoolItem[];
  onAddItem: (item: Omit<DataPoolItem, "_id" | "addedBy" | "addedAt">) => Promise<void>;
  onRemoveItem: (itemId: string) => Promise<void>;
  onViewItem: (item: DataPoolItem) => void;
  isReadOnly?: boolean;
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
}: DataPoolProps) {
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [newItem, setNewItem] = useState({
    type: "text" as DataPoolItem["type"],
    name: "",
    description: "",
    content: "",
  });

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      setIsUploading(true);
      for (const file of acceptedFiles) {
        const type = getFileType(file.name);
        const reader = new FileReader();

        reader.onload = async () => {
          const content = reader.result as string;
          const base64Content =
            type === "image" || type === "pdf"
              ? content.split(",")[1] // Remove data URL prefix for binary files
              : content;

          await onAddItem({
            type: type as DataPoolItem["type"],
            name: file.name,
            description: "",
            content: base64Content,
          });
        };

        if (type === "image" || type === "pdf") {
          reader.readAsDataURL(file);
        } else {
          reader.readAsText(file);
        }
      }
      setIsUploading(false);
    },
    [onAddItem]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    disabled: isReadOnly,
  });

  const handleAddItem = async () => {
    if (!newItem.name || !newItem.type) return;

    setIsUploading(true);
    await onAddItem({
      type: newItem.type,
      name: newItem.name,
      description: newItem.description,
      content: newItem.content,
    });
    setNewItem({ type: "text", name: "", description: "", content: "" });
    setIsAddDialogOpen(false);
    setIsUploading(false);
  };

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-gray-800 bg-gray-900 px-6 py-4">
        <div>
          <h2 className="text-lg font-semibold text-green-100">Data Pool</h2>
          <p className="text-sm text-gray-400">
            {items.length} item{items.length !== 1 ? "s" : ""} in the pool
          </p>
        </div>
        {!isReadOnly && (
          <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
            <DialogTrigger asChild>
              <Button size="sm">
                <Plus className="mr-2 h-4 w-4" />
                Add Item
              </Button>
            </DialogTrigger>
            <DialogContent className="bg-gray-900 border-gray-800">
              <DialogHeader>
                <DialogTitle className="text-green-100">Add to Data Pool</DialogTitle>
                <DialogDescription className="text-gray-400">
                  Add a new item to the research data pool
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label className="text-gray-300">Type</Label>
                  <Select
                    value={newItem.type}
                    onValueChange={(v) =>
                      setNewItem({ ...newItem, type: v as DataPoolItem["type"] })
                    }
                  >
                    <SelectTrigger className="bg-gray-800 border-gray-700 text-gray-100">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-gray-800 border-gray-700">
                      <SelectItem value="pdb">PDB Structure</SelectItem>
                      <SelectItem value="pdf">PDF Document</SelectItem>
                      <SelectItem value="image">Image</SelectItem>
                      <SelectItem value="sequence">Sequence</SelectItem>
                      <SelectItem value="text">Text Note</SelectItem>
                      <SelectItem value="other">Other</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label className="text-gray-300">Name</Label>
                  <Input
                    placeholder="e.g., SARS-CoV-2 Spike Protein"
                    value={newItem.name}
                    onChange={(e) =>
                      setNewItem({ ...newItem, name: e.target.value })
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-gray-300">Description</Label>
                  <Textarea
                    placeholder="Brief description of this item..."
                    value={newItem.description}
                    onChange={(e) =>
                      setNewItem({ ...newItem, description: e.target.value })
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-gray-300">Content</Label>
                  <Textarea
                    placeholder="Paste content, sequence, or text here..."
                    value={newItem.content}
                    onChange={(e) =>
                      setNewItem({ ...newItem, content: e.target.value })
                    }
                    rows={6}
                    className="font-mono text-sm"
                  />
                </div>
              </div>
              <DialogFooter>
                <Button onClick={handleAddItem} disabled={isUploading || !newItem.name}>
                  {isUploading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Adding...
                    </>
                  ) : (
                    "Add Item"
                  )}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        )}
      </div>

      {/* Drop Zone */}
      {!isReadOnly && (
        <div
          {...getRootProps()}
          className={cn(
            "mx-6 mt-4 cursor-pointer rounded-lg border-2 border-dashed border-gray-700 bg-gray-900 p-6 text-center transition-colors",
            isDragActive && "border-green-500 bg-green-950/30"
          )}
        >
          <input {...getInputProps()} />
          <Upload className="mx-auto h-8 w-8 text-gray-500" />
          <p className="mt-2 text-sm text-gray-300">
            {isDragActive
              ? "Drop files here..."
              : "Drag & drop files here, or click to select"}
          </p>
          <p className="mt-1 text-xs text-gray-500">
            Supports PDB, CIF, PDF, images, FASTA, and text files
          </p>
        </div>
      )}

      {/* Items List */}
      <ScrollArea className="flex-1 px-6 py-4">
        {items.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <File className="h-12 w-12 text-gray-700" />
            <p className="mt-4 text-sm text-gray-400">
              No items in the data pool yet
            </p>
            <p className="text-xs text-gray-500">
              Add research data to get started
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {items.map((item) => (
              <Card key={item._id} className="overflow-hidden bg-gray-900 border-gray-700">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 p-4">
                  <div className="flex items-center gap-3">
                    {FILE_TYPE_ICONS[item.type] || FILE_TYPE_ICONS.other}
                    <div>
                      <CardTitle className="text-sm font-medium text-green-100">
                        {item.name}
                      </CardTitle>
                      {item.description && (
                        <p className="text-xs text-gray-400 line-clamp-1">
                          {item.description}
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary" className="text-xs bg-gray-800 text-gray-300">
                      {item.type.toUpperCase()}
                    </Badge>
                    <Button
                      size="icon"
                      variant="ghost"
                      className="h-8 w-8 text-gray-400 hover:bg-gray-800"
                      onClick={() => onViewItem(item)}
                    >
                      <Eye className="h-4 w-4" />
                    </Button>
                    {!isReadOnly && (
                      <Button
                        size="icon"
                        variant="ghost"
                        className="h-8 w-8 text-red-500 hover:bg-red-950 hover:text-red-400"
                        onClick={() => onRemoveItem(item._id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </CardHeader>
                {item.content && item.type === "text" && (
                  <CardContent className="border-t border-gray-700 bg-gray-800 px-4 py-3">
                    <p className="text-xs text-gray-300 line-clamp-2 font-mono">
                      {item.content}
                    </p>
                  </CardContent>
                )}
              </Card>
            ))}
          </div>
        )}
      </ScrollArea>
    </div>
  );
}
