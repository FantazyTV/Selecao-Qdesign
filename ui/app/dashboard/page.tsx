"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuthStore } from "@/lib/stores";
import { projectsApi, ApiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import {
  Dna,
  Plus,
  Users,
  FolderOpen,
  Clock,
  LogOut,
  Loader2,
  Hash,
  ArrowRight,
} from "lucide-react";
import { formatDate } from "@/lib/utils";
import type { Project } from "@/lib/types";

export default function DashboardPage() {
  const router = useRouter();
  const { user, isLoading: authLoading, isInitialized, logout, checkSession } = useAuthStore();
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isJoinOpen, setIsJoinOpen] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [isJoining, setIsJoining] = useState(false);

  // Create project form
  const [newProject, setNewProject] = useState({
    name: "",
    mainObjective: "",
    secondaryObjectives: "",
    constraints: "",
    notes: "",
    description: "",
  });

  // Join project form
  const [joinHash, setJoinHash] = useState("");
  const [joinError, setJoinError] = useState("");

  // Check session on mount - only if not already initialized
  useEffect(() => {
    if (!isInitialized && !authLoading) {
      checkSession();
    }
  }, [isInitialized, authLoading, checkSession]);

  // Only redirect after we're fully initialized and confirmed no user
  useEffect(() => {
    if (isInitialized && !authLoading && !user) {
      router.push("/login");
    }
  }, [user, isInitialized, authLoading, router]);

  useEffect(() => {
    const fetchProjects = async () => {
      try {
        const data = await projectsApi.list();
        if (data.projects) {
          setProjects(data.projects);
        }
      } catch (error) {
        console.error("Failed to fetch projects:", error);
      } finally {
        setIsLoading(false);
      }
    };

    if (user) {
      fetchProjects();
    }
  }, [user]);

  const handleLogout = () => {
    logout();
    router.push("/");
  };

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsCreating(true);

    try {
      const data = await projectsApi.create({
        name: newProject.name,
        mainObjective: newProject.mainObjective,
        secondaryObjectives: newProject.secondaryObjectives
          .split("\n")
          .filter(Boolean),
        constraints: newProject.constraints
          .split("\n")
          .filter(Boolean),
        notes: newProject.notes
          .split("\n")
          .filter(Boolean),
        description: newProject.description,
      });

      if (data.project) {
        router.push(`/project/${data.project._id}`);
      }
    } catch (error) {
      console.error("Failed to create project:", error);
    } finally {
      setIsCreating(false);
    }
  };

  const handleJoinProject = async (e: React.FormEvent) => {
    e.preventDefault();
    setJoinError("");
    setIsJoining(true);

    try {
      const data = await projectsApi.join(joinHash);

      if (data.project) {
        router.push(`/project/${data.project._id}`);
      }
    } catch (error) {
      if (error instanceof ApiError) {
        setJoinError(error.message);
      } else {
        setJoinError("Failed to join project");
      }
    } finally {
      setIsJoining(false);
    }
  };

  if (authLoading || isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-950">
        <Loader2 className="h-8 w-8 animate-spin text-green-400" />
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-950">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-900">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
          <div className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-green-600">
              <Dna className="h-5 w-5 text-gray-900" />
            </div>
            <span className="text-xl font-semibold text-green-400">QDesign</span>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-3">
              <Avatar className="h-8 w-8">
                <AvatarFallback className="bg-gray-800 text-sm text-green-300">
                  {user.name.charAt(0).toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <span className="text-sm font-medium text-gray-200">{user.name}</span>
            </div>
            <Button variant="ghost" size="sm" onClick={handleLogout} className="text-gray-300 hover:text-white hover:bg-gray-800">
              <LogOut className="mr-2 h-4 w-4" />
              Sign out
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="mx-auto max-w-7xl px-6 py-8">
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-green-100">Your Workspaces</h1>
            <p className="mt-1 text-gray-400">
              Create or join a research workspace to start designing
            </p>
          </div>
          <div className="flex items-center gap-3">
            {/* Join Project Dialog */}
            <Dialog open={isJoinOpen} onOpenChange={setIsJoinOpen}>
              <DialogTrigger asChild>
                <Button variant="outline" className="border-gray-700 text-gray-300 hover:bg-gray-800">
                  <Hash className="mr-2 h-4 w-4" />
                  Join Workspace
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-gray-900 border-gray-800">
                <DialogHeader>
                  <DialogTitle className="text-green-100">Join a Workspace</DialogTitle>
                  <DialogDescription className="text-gray-400">
                    Enter the workspace code to join an existing research project
                  </DialogDescription>
                </DialogHeader>
                <form onSubmit={handleJoinProject}>
                  <div className="space-y-4 py-4">
                    {joinError && (
                      <div className="rounded-lg bg-red-950/50 border border-red-800 p-3 text-sm text-red-400">
                        {joinError}
                      </div>
                    )}
                    <div className="space-y-2">
                      <Label htmlFor="hash" className="text-gray-300">Workspace Code</Label>
                      <Input
                        id="hash"
                        placeholder="e.g., ABC123"
                        value={joinHash}
                        onChange={(e) => setJoinHash(e.target.value.toUpperCase())}
                        className="font-mono text-lg tracking-widest"
                        maxLength={6}
                        required
                      />
                    </div>
                  </div>
                  <DialogFooter>
                    <Button type="submit" disabled={isJoining}>
                      {isJoining ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Joining...
                        </>
                      ) : (
                        "Join Workspace"
                      )}
                    </Button>
                  </DialogFooter>
                </form>
              </DialogContent>
            </Dialog>

            {/* Create Project Dialog */}
            <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="mr-2 h-4 w-4" />
                  New Workspace
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-lg bg-gray-900 border-gray-800">
                <DialogHeader>
                  <DialogTitle className="text-green-100">Create New Workspace</DialogTitle>
                  <DialogDescription className="text-gray-400">
                    Set up a new research workspace for your team
                  </DialogDescription>
                </DialogHeader>
                <form onSubmit={handleCreateProject}>
                  <div className="space-y-4 py-4">
                    <div className="space-y-2">
                      <Label htmlFor="name" className="text-gray-300">Workspace Name</Label>
                      <Input
                        id="name"
                        placeholder="e.g., SARS-CoV-2 Spike Optimization"
                        value={newProject.name}
                        onChange={(e) =>
                          setNewProject({ ...newProject, name: e.target.value })
                        }
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="mainObjective" className="text-gray-300">Main Objective</Label>
                      <Textarea
                        id="mainObjective"
                        placeholder="Describe the primary goal of this research..."
                        value={newProject.mainObjective}
                        onChange={(e) =>
                          setNewProject({
                            ...newProject,
                            mainObjective: e.target.value,
                          })
                        }
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="secondaryObjectives" className="text-gray-300">
                        Secondary Objectives (one per line)
                      </Label>
                      <Textarea
                        id="secondaryObjectives"
                        placeholder="Improve binding affinity&#10;Reduce immunogenicity&#10;Increase stability"
                        value={newProject.secondaryObjectives}
                        onChange={(e) =>
                          setNewProject({
                            ...newProject,
                            secondaryObjectives: e.target.value,
                          })
                        }
                        rows={3}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="constraints" className="text-gray-300">
                        Constraints (one per line)
                      </Label>
                      <Textarea
                        id="constraints"
                        placeholder="Budget limitations&#10;Time constraints&#10;Regulatory requirements"
                        value={newProject.constraints}
                        onChange={(e) =>
                          setNewProject({
                            ...newProject,
                            constraints: e.target.value,
                          })
                        }
                        rows={3}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="notes" className="text-gray-300">
                        Notes (one per line)
                      </Label>
                      <Textarea
                        id="notes"
                        placeholder="Key considerations&#10;Important references&#10;Future directions"
                        value={newProject.notes}
                        onChange={(e) =>
                          setNewProject({
                            ...newProject,
                            notes: e.target.value,
                          })
                        }
                        rows={3}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="description" className="text-gray-300">Description (optional)</Label>
                      <Textarea
                        id="description"
                        placeholder="Additional context about this project..."
                        value={newProject.description}
                        onChange={(e) =>
                          setNewProject({
                            ...newProject,
                            description: e.target.value,
                          })
                        }
                      />
                    </div>
                  </div>
                  <DialogFooter>
                    <Button type="submit" disabled={isCreating}>
                      {isCreating ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Creating...
                        </>
                      ) : (
                        "Create Workspace"
                      )}
                    </Button>
                  </DialogFooter>
                </form>
              </DialogContent>
            </Dialog>
          </div>
        </div>

        {/* Projects Grid */}
        <div className="mt-8">
          {projects.length === 0 ? (
            <Card className="border-dashed border-gray-700 bg-gray-900">
              <CardContent className="flex flex-col items-center justify-center py-16">
                <FolderOpen className="h-12 w-12 text-gray-600" />
                <h3 className="mt-4 text-lg font-medium text-green-100">
                  No workspaces yet
                </h3>
                <p className="mt-1 text-sm text-gray-400">
                  Create your first workspace to start designing
                </p>
                <Button className="mt-4" onClick={() => setIsCreateOpen(true)}>
                  <Plus className="mr-2 h-4 w-4" />
                  Create Workspace
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {projects.map((project) => (
                <Link key={project._id} href={`/project/${project._id}`}>
                  <Card className="h-full transition-all bg-gray-900 border-gray-700 hover:border-green-600/50 hover:shadow-md">
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div>
                          <CardTitle className="text-lg text-green-100">{project.name}</CardTitle>
                          <CardDescription className="mt-1 line-clamp-2 text-gray-400">
                            {project.mainObjective}
                          </CardDescription>
                        </div>
                        <Badge variant="outline" className="font-mono text-xs border-green-700 text-green-400">
                          {project.hash}
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="flex items-center justify-between text-sm text-gray-400">
                        <div className="flex items-center gap-4">
                          <span className="flex items-center gap-1">
                            <Users className="h-4 w-4" />
                            {project.members.length}
                          </span>
                          <Badge
                            variant={
                              project.currentMode === "coscientist"
                                ? "default"
                                : "secondary"
                            }
                            className={project.currentMode === "coscientist" ? "bg-green-600" : "bg-gray-800 text-gray-300"}
                          >
                            {project.currentMode === "pool"
                              ? "Data Pool"
                              : project.currentMode === "retrieval"
                              ? "Knowledge Graph"
                              : "Co-Scientist"}
                          </Badge>
                        </div>
                        <span className="flex items-center gap-1">
                          <Clock className="h-4 w-4" />
                          {formatDate(project.updatedAt)}
                        </span>
                      </div>
                      <div className="mt-4 flex items-center justify-end">
                        <span className="flex items-center gap-1 text-sm font-medium text-green-400">
                          Open
                          <ArrowRight className="h-4 w-4" />
                        </span>
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
