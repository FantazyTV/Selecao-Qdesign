"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuthStore } from "@/lib/stores";
import { Button } from "@/components/ui/button";
import {
  Dna,
  FlaskConical,
  Network,
  Users,
  Sparkles,
  ArrowRight,
  Microscope,
  Target,
  Loader2,
} from "lucide-react";

export default function Home() {
  const router = useRouter();
  const { user, isLoading } = useAuthStore();

  useEffect(() => {
    if (!isLoading && user) {
      router.push("/dashboard");
    }
  }, [user, isLoading, router]);

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950">
      {/* Header */}
      <header className="border-b border-gray-800">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
          <div className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-green-600">
              <Dna className="h-5 w-5 text-gray-900" />
            </div>
            <span className="text-xl font-semibold text-green-400">QDesign</span>
          </div>
          <nav className="flex items-center gap-6">
            <Link
              href="/login"
              className="text-sm font-medium text-gray-300 hover:text-green-400"
            >
              Sign in
            </Link>
            <Link href="/register">
              <Button size="sm">Get Started</Button>
            </Link>
          </nav>
        </div>
      </header>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-gray-950 via-gray-900 to-green-950/20" />
        <div className="absolute inset-0 bg-[url('/grid.svg')] bg-center opacity-10" />
        <div className="relative mx-auto max-w-7xl px-6 py-24 sm:py-32">
          <div className="mx-auto max-w-3xl text-center">
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-green-800 bg-green-950/50 px-4 py-1.5 text-sm text-green-300 shadow-sm">
              <Sparkles className="h-4 w-4 text-green-400" />
              AI-Powered Biological Design
            </div>
            <h1 className="text-5xl font-bold tracking-tight text-green-100 sm:text-6xl">
              Design the future of
              <span className="block text-green-400">biological systems</span>
            </h1>
            <p className="mt-6 text-lg leading-8 text-gray-300">
              QDesign is a collaborative platform where scientists explore biological
              knowledge, generate novel protein designs, and iteratively refine them
              using AI-powered, evidence-based reasoning.
            </p>
            <div className="mt-10 flex items-center justify-center gap-4">
              <Link href="/register">
                <Button size="lg" className="gap-2">
                  Start Designing
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
              <Link href="/login">
                <Button size="lg" variant="outline" className="border-gray-700 text-gray-300 hover:bg-gray-800">
                  Sign In
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="border-t border-gray-800 bg-gray-900 py-24">
        <div className="mx-auto max-w-7xl px-6">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-green-100">
              A complete workspace for biological invention
            </h2>
            <p className="mt-4 text-lg text-gray-300">
              Move beyond analysis into AI-driven design with explainable outputs
              and human supervision at every step.
            </p>
          </div>

          <div className="mt-16 grid gap-8 md:grid-cols-2 lg:grid-cols-3">
            {/* Feature 1 */}
            <div className="rounded-2xl border border-gray-700 bg-gray-900/50 p-8 shadow-sm hover:border-green-600/50 transition-all duration-300">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-green-950/50 border border-green-800">
                <FlaskConical className="h-6 w-6 text-green-400" />
              </div>
              <h3 className="mt-6 text-lg font-semibold text-green-100">
                Protein & Antibody Engineering
              </h3>
              <p className="mt-2 text-gray-400">
                Define goals like binding affinity or stability, and let QDesign
                generate optimized mutated variants with explainable outputs.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="rounded-2xl border border-gray-700 bg-gray-900/50 p-8 shadow-sm hover:border-green-600/50 transition-all duration-300">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-green-950/50 border border-green-800">
                <Microscope className="h-6 w-6 text-green-400" />
              </div>
              <h3 className="mt-6 text-lg font-semibold text-green-100">
                Enzyme Optimization
              </h3>
              <p className="mt-2 text-gray-400">
                Improve catalytic rates, substrate specificity, and industrial
                stability with AI-proposed designs backed by structural evidence.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="rounded-2xl border border-gray-700 bg-gray-900/50 p-8 shadow-sm hover:border-green-600/50 transition-all duration-300">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-green-950/50 border border-green-800">
                <Target className="h-6 w-6 text-green-400" />
              </div>
              <h3 className="mt-6 text-lg font-semibold text-green-100">
                Drug Target Discovery
              </h3>
              <p className="mt-2 text-gray-400">
                Identify high-value therapeutic targets from disease-associated
                genes and proteins with evidence-based explanations.
              </p>
            </div>

            {/* Feature 4 */}
            <div className="rounded-2xl border border-gray-700 bg-gray-900/50 p-8 shadow-sm hover:border-green-600/50 transition-all duration-300">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-green-950/50 border border-green-800">
                <Network className="h-6 w-6 text-green-400" />
              </div>
              <h3 className="mt-6 text-lg font-semibold text-green-100">
                Knowledge Network
              </h3>
              <p className="mt-2 text-gray-400">
                Visualize and navigate an interpretable network of papers,
                structures, and experimental data with real-time collaboration.
              </p>
            </div>

            {/* Feature 5 */}
            <div className="rounded-2xl border border-gray-700 bg-gray-900/50 p-8 shadow-sm hover:border-green-600/50 transition-all duration-300">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-green-950/50 border border-green-800">
                <Users className="h-6 w-6 text-green-400" />
              </div>
              <h3 className="mt-6 text-lg font-semibold text-green-100">
                Real-time Collaboration
              </h3>
              <p className="mt-2 text-gray-400">
                Work together with your team in shared research workspaces.
                Annotate, comment, and refine designs collaboratively.
              </p>
            </div>

            {/* Feature 6 */}
            <div className="rounded-2xl border border-gray-700 bg-gray-900/50 p-8 shadow-sm hover:border-green-600/50 transition-all duration-300">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-green-950/50 border border-green-800">
                <Sparkles className="h-6 w-6 text-green-400" />
              </div>
              <h3 className="mt-6 text-lg font-semibold text-green-100">
                AI Co-Scientist
              </h3>
              <p className="mt-2 text-gray-400">
                Let AI reason through your data, propose hypotheses, and generate
                designs while you supervise and guide the process.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="border-t border-gray-800 bg-gray-950 py-24">
        <div className="mx-auto max-w-7xl px-6">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-green-100">
              Ready to transform your research?
            </h2>
            <p className="mt-4 text-lg text-gray-300">
              Join scientists worldwide using QDesign for breakthrough biological discoveries.
            </p>
            <div className="mt-8">
              <Link href="/register">
                <Button size="lg" className="gap-2">
                  Create Your Workspace
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-800 bg-gray-950 py-8">
        <div className="mx-auto max-w-7xl px-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="flex h-7 w-7 items-center justify-center rounded bg-green-600">
                <Dna className="h-4 w-4 text-gray-900" />
              </div>
              <span className="font-semibold text-green-400">QDesign</span>
            </div>
            <p className="text-sm text-gray-500">
              © 2026 QDesign. AI-driven biological design platform.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
