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

export function CoScientistSidebar({
  steps,
  dataPool,
  knowledgeGraph,
  onAddStep,
  onUpdateStep,
  onAddComment,
  onViewAttachment,
  onExport,
  onStart,
  onPause,
  onRestart,
  onSendFeedback,
  isRunning,
  isOpen,
  onClose,
}: CoScientistSidebarProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [feedbackText, setFeedbackText] = useState("");

  // Auto-scroll to bottom when new steps are added
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [steps.length]);

  const handleSendFeedback = () => {
    if (!feedbackText.trim() || !onSendFeedback) return;
    onSendFeedback(feedbackText.trim());
    setFeedbackText("");
  };

  if (!isOpen) return null;

  const handleApprove = (step: CoScientistStep) => {
    onUpdateStep({ ...step, status: "approved" });
  };

  const handleReject = (step: CoScientistStep) => {
    onUpdateStep({ ...step, status: "rejected" });
  };

  return (
    <div className="fixed right-0 top-0 z-40 flex h-full w-96 flex-col border-l border-gray-800 bg-gray-900 shadow-xl">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-gray-800 px-4 py-3">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-green-500 to-emerald-600">
            <Brain className="h-4 w-4 text-gray-900" />
          </div>
          <div>
            <h2 className="font-semibold text-green-100">AI Co-Scientist</h2>
            <p className="text-xs text-gray-400">
              {isRunning ? "Analyzing..." : `${steps.length} steps completed`}
            </p>
          </div>
        </div>
        <Button size="icon" variant="ghost" onClick={onClose} className="text-gray-400 hover:bg-gray-800">
          <X className="h-4 w-4" />
        </Button>
      </div>

      {/* Controls */}
      <div className="flex items-center gap-2 border-b border-gray-800 px-4 py-2">
        {isRunning ? (
          <Button size="sm" variant="outline" onClick={onPause} className="border-gray-700 text-gray-300 hover:bg-gray-800">
            <Pause className="mr-2 h-3 w-3" />
            Pause
          </Button>
        ) : (
          <Button size="sm" onClick={onStart}>
            <Play className="mr-2 h-3 w-3" />
            {steps.length === 0 ? "Start Analysis" : "Continue"}
          </Button>
        )}
        <Button size="sm" variant="outline" onClick={onRestart} className="border-gray-700 text-gray-300 hover:bg-gray-800">
          <RotateCw className="mr-2 h-3 w-3" />
          Restart
        </Button>
        <Button
          size="sm"
          variant="outline"
          className="ml-auto border-gray-700 text-gray-300 hover:bg-gray-800"
          onClick={onExport}
          disabled={steps.length === 0}
        >
          <Download className="mr-2 h-3 w-3" />
          Export
        </Button>
      </div>

      {/* Context Summary */}
      <div className="border-b border-gray-800 bg-gray-800 px-4 py-2">
        <p className="text-xs text-gray-400">
          Analyzing {dataPool.length} data items and {knowledgeGraph.nodes.length} knowledge nodes
        </p>
      </div>

      {/* Steps */}
      <ScrollArea className="flex-1" ref={scrollRef}>
        <div className="space-y-3 p-4">
          {steps.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Brain className="h-12 w-12 text-gray-700" />
              <p className="mt-4 text-sm text-gray-400">
                No analysis steps yet
              </p>
              <p className="text-xs text-gray-500">
                Click &quot;Start Analysis&quot; to begin
              </p>
            </div>
          ) : (
            steps.map((step) => (
              <StepCard
                key={step.id}
                step={step}
                onAddComment={(comment) => onAddComment(step.id, comment)}
                onViewAttachment={onViewAttachment}
                onApprove={() => handleApprove(step)}
                onReject={() => handleReject(step)}
              />
            ))
          )}

          {/* Loading indicator */}
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

      {/* Input Area - for adding feedback */}
      <div className="border-t border-gray-800 p-4">
        <p className="mb-2 text-xs text-gray-400">
          Add feedback or constraints for the AI
        </p>
        <div className="flex gap-2">
          <Textarea
            placeholder="e.g., 'Focus on thermal stability' or 'This contradicts our lab results...'"
            className="min-h-[60px] text-sm"
            value={feedbackText}
            onChange={(e) => setFeedbackText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && e.ctrlKey) {
                e.preventDefault();
                handleSendFeedback();
              }
            }}
          />
        </div>
        <Button 
          className="mt-2 w-full" 
          size="sm"
          onClick={handleSendFeedback}
          disabled={!feedbackText.trim() || isRunning}
        >
          <Send className="mr-2 h-3 w-3" />
          Send Feedback
        </Button>
      </div>
    </div>
  );
}
