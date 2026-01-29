"use client";

import React, { useState, useRef, useEffect } from "react";
import { v4 as uuidv4 } from "uuid";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  Lightbulb,
  FlaskConical,
  Brain,
  CheckCircle2,
  HelpCircle,
  Dna,
  MessageSquare,
  Send,
  Download,
  Play,
  Pause,
  RotateCw,
  ChevronRight,
  ChevronDown,
  Paperclip,
  Eye,
  ThumbsUp,
  ThumbsDown,
  X,
  Loader2,
} from "lucide-react";
import { cn, formatDate } from "@/lib/utils";
import type { CoScientistStep, DataPoolItem, KnowledgeGraph } from "@/lib/types";

interface CoScientistSidebarProps {
  steps: CoScientistStep[];
  dataPool: DataPoolItem[];
  knowledgeGraph: KnowledgeGraph;
  onAddStep: (step: CoScientistStep) => void;
  onUpdateStep: (step: CoScientistStep) => void;
  onAddComment: (stepId: string, comment: string) => void;
  onViewAttachment: (attachment: { type: string; name: string; content?: string; fileUrl?: string; dataPoolItemId?: string }) => void;
  onExport: () => void;
  onStart: () => void;
  onPause: () => void;
  onRestart: () => void;
  onSendFeedback?: (feedback: string) => void;
  isRunning: boolean;
  isOpen: boolean;
  onClose: () => void;
}

const STEP_ICONS: Record<string, React.ReactNode> = {
  reasoning: <Brain className="h-4 w-4" />,
  evidence: <FlaskConical className="h-4 w-4" />,
  hypothesis: <Lightbulb className="h-4 w-4" />,
  conclusion: <CheckCircle2 className="h-4 w-4" />,
  question: <HelpCircle className="h-4 w-4" />,
  design: <Dna className="h-4 w-4" />,
};

const STEP_COLORS: Record<string, string> = {
  reasoning: "bg-blue-100 text-blue-700",
  evidence: "bg-emerald-100 text-emerald-700",
  hypothesis: "bg-amber-100 text-amber-700",
  conclusion: "bg-purple-100 text-purple-700",
  question: "bg-rose-100 text-rose-700",
  design: "bg-cyan-100 text-cyan-700",
};

function StepCard({
  step,
  onAddComment,
  onViewAttachment,
  onApprove,
  onReject,
}: {
  step: CoScientistStep;
  onAddComment: (comment: string) => void;
  onViewAttachment: (attachment: { type: string; name: string; content?: string; fileUrl?: string; dataPoolItemId?: string }) => void;
  onApprove: () => void;
  onReject: () => void;
}) {
  const [isExpanded, setIsExpanded] = useState(true);
  const [comment, setComment] = useState("");
  const [showComments, setShowComments] = useState(false);

  const handleSubmitComment = () => {
    if (!comment.trim()) return;
    onAddComment(comment);
    setComment("");
  };

  return (
    <div className="animate-fade-in rounded-lg border border-gray-700 bg-gray-900 shadow-sm">
      {/* Header */}
      <div
        className="flex cursor-pointer items-center gap-3 p-4"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className={cn("rounded-lg p-2", STEP_COLORS[step.type])}>
          {STEP_ICONS[step.type]}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h4 className="font-medium text-green-100 truncate">{step.title}</h4>
            <Badge
              variant={
                step.status === "approved"
                  ? "success"
                  : step.status === "rejected"
                  ? "destructive"
                  : "secondary"
              }
              className="text-[10px]"
            >
              {step.status}
            </Badge>
          </div>
          <p className="text-xs text-gray-400">
            {formatDate(step.createdAt)}
          </p>
        </div>
        {isExpanded ? (
          <ChevronDown className="h-4 w-4 text-gray-500" />
        ) : (
          <ChevronRight className="h-4 w-4 text-gray-500" />
        )}
      </div>

      {/* Content */}
      {isExpanded && (
        <div className="border-t border-gray-800 px-4 py-3">
          <p className="text-sm text-gray-300 whitespace-pre-wrap">{step.content}</p>

          {/* Attachments */}
          {step.attachments && step.attachments.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2">
              {step.attachments.map((att, idx) => (
                <button
                  key={idx}
                  className="flex items-center gap-1 rounded-md border border-gray-700 bg-gray-800 px-2 py-1 text-xs text-gray-300 hover:bg-gray-700"
                  onClick={() => onViewAttachment(att)}
                >
                  <Paperclip className="h-3 w-3" />
                  {att.name}
                  <Eye className="ml-1 h-3 w-3" />
                </button>
              ))}
            </div>
          )}

          {/* Actions */}
          {step.status === "pending" && (
            <div className="mt-3 flex items-center gap-2">
              <Button
                size="sm"
                variant="outline"
                className="h-7 text-xs text-emerald-400 border-gray-700 hover:bg-emerald-950"
                onClick={onApprove}
              >
                <ThumbsUp className="mr-1 h-3 w-3" />
                Approve
              </Button>
              <Button
                size="sm"
                variant="outline"
                className="h-7 text-xs text-red-400 border-gray-700 hover:bg-red-950"
                onClick={onReject}
              >
                <ThumbsDown className="mr-1 h-3 w-3" />
                Reject
              </Button>
            </div>
          )}

          {/* Comments Toggle */}
          <button
            className="mt-3 flex items-center gap-1 text-xs text-gray-400 hover:text-gray-200"
            onClick={() => setShowComments(!showComments)}
          >
            <MessageSquare className="h-3 w-3" />
            {step.comments.length} comment{step.comments.length !== 1 ? "s" : ""}
          </button>

          {/* Comments */}
          {showComments && (
            <div className="mt-2 space-y-2">
              {step.comments.map((c) => (
                <div
                  key={c.id}
                  className="rounded-md bg-gray-800 p-2 text-xs text-gray-300"
                >
                  <p>{c.text}</p>
                  <p className="mt-1 text-gray-500">
                    {formatDate(c.createdAt)}
                  </p>
                </div>
              ))}
              <div className="flex gap-2">
                <Input
                  placeholder="Add a comment..."
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  className="h-7 text-xs"
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      handleSubmitComment();
                    }
                  }}
                />
                <Button
                  size="sm"
                  className="h-7"
                  onClick={handleSubmitComment}
                  disabled={!comment.trim()}
                >
                  <Send className="h-3 w-3" />
                </Button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function CoScientistPanel({
  steps,
  dataPool,
  knowledgeGraph,
  onAddStep,
  onUpdateStep,
  onAddComment,
  onViewAttachment,
  onExport,
  onStart,
  isRunning,
}: Omit<CoScientistSidebarProps, "onPause" | "onRestart" | "onSendFeedback" | "isOpen" | "onClose">) {
  // No sidebar, just a centered panel
  return (
    <div className="flex flex-col items-center justify-center w-full h-full py-12">
      <div className="flex flex-col items-center max-w-2xl w-full bg-gray-900 rounded-xl shadow-lg p-8 border border-gray-800">
        <Brain className="h-12 w-12 text-green-400 mb-2" />
        <h2 className="text-2xl font-bold text-green-100 mb-1">AI Co-Scientist</h2>
        <p className="text-gray-400 mb-6 text-center">
          Let the AI analyze your data pool and knowledge graph to generate insights and design suggestions.
        </p>
        <div className="flex gap-4 mb-6">
          <Button
            size="lg"
            className="px-6"
            onClick={onStart}
            disabled={isRunning}
          >
            <Play className="mr-2 h-5 w-5" />
            {steps.length === 0 ? "Start Analysis" : "Continue Analysis"}
          </Button>
          <Button
            size="lg"
            variant="outline"
            className="px-6 border-gray-700 text-gray-300 hover:bg-gray-800"
            onClick={onExport}
            disabled={steps.length === 0}
          >
            <Download className="mr-2 h-5 w-5" />
            Export
          </Button>
        </div>
        <div className="w-full">
          {steps.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <Brain className="h-12 w-12 text-gray-700" />
              <p className="mt-4 text-sm text-gray-400">
                No analysis steps yet
              </p>
              <p className="text-xs text-gray-500">
                Click "Start Analysis" to begin
              </p>
            </div>
          ) : (
            <ScrollArea className="max-h-[400px] w-full">
              <div className="space-y-3">
                {steps.map((step) => (
                  <StepCard
                    key={step.id}
                    step={step}
                    onAddComment={(comment) => onAddComment(step.id, comment)}
                    onViewAttachment={onViewAttachment}
                    onApprove={() => onUpdateStep({ ...step, status: "approved" })}
                    onReject={() => onUpdateStep({ ...step, status: "rejected" })}
                  />
                ))}
                {isRunning && (
                  <div className="flex items-center gap-3 rounded-lg border border-gray-700 bg-gray-800 p-4">
                    <Loader2 className="h-5 w-5 animate-spin text-green-500" />
                    <div>
                      <p className="text-sm font-medium text-gray-200">Analyzing...</p>
                      <p className="text-xs text-gray-400">
                        Processing data and generating insights
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </ScrollArea>
          )}
        </div>
      </div>
    </div>
  );
}
