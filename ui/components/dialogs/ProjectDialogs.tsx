"use client";

import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Plus, Users, Loader2, Dna, FlaskConical, Microscope, Atom } from "lucide-react";
import { cn } from "@/lib/utils";

interface CreateProjectDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (data: { name: string; description: string }) => Promise<void>;
  isLoading?: boolean;
}

const projectIcons = [
  { icon: Dna, label: "Genomics", color: "bg-purple-100 text-purple-600" },
  { icon: FlaskConical, label: "Chemistry", color: "bg-emerald-100 text-emerald-600" },
  { icon: Microscope, label: "Microscopy", color: "bg-blue-100 text-blue-600" },
  { icon: Atom, label: "Structural", color: "bg-amber-100 text-amber-600" },
];

export function CreateProjectDialog({
  open,
  onOpenChange,
  onSubmit,
  isLoading,
}: CreateProjectDialogProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [selectedIcon, setSelectedIcon] = useState(0);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSubmit({ name, description });
    setName("");
    setDescription("");
    setSelectedIcon(0);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 shadow-lg">
              <Plus className="h-5 w-5 text-white" />
            </div>
            Create New Project
          </DialogTitle>
          <DialogDescription>
            Start a new biological design project. You can invite collaborators later.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit}>
          <div className="space-y-6 py-4">
            {/* Project Icon Selection */}
            <div className="space-y-2">
              <Label>Project Type</Label>
              <div className="flex gap-2">
                {projectIcons.map((item, idx) => (
                  <button
                    key={idx}
                    type="button"
                    className={cn(
                      "flex h-16 w-16 flex-col items-center justify-center rounded-xl border-2 transition-all",
                      selectedIcon === idx
                        ? "border-blue-500 bg-blue-50"
                        : "border-slate-200 hover:border-slate-300"
                    )}
                    onClick={() => setSelectedIcon(idx)}
                  >
                    <div className={cn("rounded-lg p-2", item.color)}>
                      <item.icon className="h-4 w-4" />
                    </div>
                    <span className="mt-1 text-[10px] text-slate-500">{item.label}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Project Name */}
            <div className="space-y-2">
              <Label htmlFor="project-name">Project Name</Label>
              <Input
                id="project-name"
                placeholder="e.g., Thermostable Enzyme Design"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="h-11"
                required
              />
            </div>

            {/* Description */}
            <div className="space-y-2">
              <Label htmlFor="project-desc">Description</Label>
              <Textarea
                id="project-desc"
                placeholder="Describe the goals and scope of your project..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="min-h-[100px] resize-none"
              />
            </div>

            {/* Info Box */}
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
              <div className="flex items-start gap-2">
                <Users className="mt-0.5 h-4 w-4 text-slate-500" />
                <div>
                  <p className="text-sm font-medium text-slate-700">Collaboration</p>
                  <p className="text-xs text-slate-500">
                    After creation, you&apos;ll receive a unique code to share with collaborators.
                  </p>
                </div>
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={!name.trim() || isLoading}>
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating...
                </>
              ) : (
                <>
                  <Plus className="mr-2 h-4 w-4" />
                  Create Project
                </>
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

interface JoinProjectDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (code: string) => Promise<void>;
  isLoading?: boolean;
}

export function JoinProjectDialog({
  open,
  onOpenChange,
  onSubmit,
  isLoading,
}: JoinProjectDialogProps) {
  const [code, setCode] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSubmit(code);
    setCode("");
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500 to-cyan-600 shadow-lg">
              <Users className="h-5 w-5 text-white" />
            </div>
            Join a Project
          </DialogTitle>
          <DialogDescription>
            Enter the project code shared by a team member to join their project.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit}>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="join-code">Project Code</Label>
              <Input
                id="join-code"
                placeholder="Enter the project code..."
                value={code}
                onChange={(e) => setCode(e.target.value.toUpperCase())}
                className="h-11 font-mono text-center text-lg tracking-wider"
                maxLength={12}
                required
              />
            </div>

            <p className="text-center text-xs text-slate-500">
              Project codes are 8 characters long and look like: <code className="rounded bg-slate-100 px-1">ABCD1234</code>
            </p>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={!code.trim() || isLoading}>
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Joining...
                </>
              ) : (
                <>
                  <Users className="mr-2 h-4 w-4" />
                  Join Project
                </>
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
