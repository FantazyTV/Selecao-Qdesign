"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, useEffect } from "react";
import { SocketProvider } from "@/lib/socket";
import { useAuthStore } from "@/lib/stores";
import { TooltipProvider } from "@/components/ui/tooltip";

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000,
            refetchOnWindowFocus: false,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <AuthProvider>
          <SocketProvider>{children}</SocketProvider>
        </AuthProvider>
      </TooltipProvider>
    </QueryClientProvider>
  );
}

function AuthProvider({ children }: { children: React.ReactNode }) {
  const { checkSession, isInitialized, _hasHydrated, user } = useAuthStore();

  useEffect(() => {
    // Only check session after hydration is complete
    // And only if we don't already have a user (from localStorage)
    if (_hasHydrated && !isInitialized && !user) {
      checkSession();
    }
  }, [checkSession, isInitialized, _hasHydrated, user]);

  return <>{children}</>;
}
