"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "secondary" | "destructive" | "outline" | "success" | "warning";
}

function Badge({ className, variant = "default", ...props }: BadgeProps) {
  return (
    <div
      className={cn(
        "inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 focus:ring-offset-gray-900",
        {
          "border-transparent bg-green-600 text-green-50": variant === "default",
          "border-gray-700 bg-gray-800 text-gray-300": variant === "secondary",
          "border-transparent bg-red-600 text-red-50": variant === "destructive",
          "border-gray-600 text-gray-300": variant === "outline",
          "border-transparent bg-green-900/50 text-green-400": variant === "success",
          "border-transparent bg-amber-900/50 text-amber-400": variant === "warning",
        },
        className
      )}
      {...props}
    />
  );
}

export { Badge };
