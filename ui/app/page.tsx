"use client";

import { useEffect, useState } from "react";
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
  Menu,
  X,
  Zap,
  Brain,
  Database,
  CheckCircle,
  Star,
  ChevronRight,
} from "lucide-react";

export default function Home() {
  const router = useRouter();
  const { user, isLoading } = useAuthStore();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    if (!isLoading && user) {
      router.push("/dashboard");
    }
  }, [user, isLoading, router]);

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-950">
        <Loader2 className="h-8 w-8 animate-spin text-green-400" />
      </div>
    );
  }

  return (
    <div className="min-h-screen overflow-x-hidden bg-gray-950">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-950/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-green-500 to-green-600 shadow-lg">
              <Dna className="h-6 w-6 text-gray-900" />
            </div>
            <span className="text-xl font-bold text-green-400">QDesign</span>
          </div>

          {/* Desktop nav */}
          <nav className="hidden items-center gap-8 sm:flex">
            <a
              href="#features"
              className="text-sm font-medium text-gray-300 hover:text-green-400 transition-colors"
            >
              Features
            </a>
            <a
              href="#how-it-works"
              className="text-sm font-medium text-gray-300 hover:text-green-400 transition-colors"
            >
              How it Works
            </a>
            <Link
              href="/login"
              className="text-sm font-medium text-gray-300 hover:text-green-400 transition-colors"
            >
              Sign in
            </Link>
            <Link href="/register">
              <Button size="sm" className="bg-green-600 hover:bg-green-700 text-white">
                Get Started
              </Button>
            </Link>
          </nav>

          {/* Mobile menu button */}
          <button
            className="flex h-10 w-10 items-center justify-center rounded-lg text-gray-300 hover:bg-gray-800 sm:hidden"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>

        {/* Mobile nav */}
        {mobileMenuOpen && (
          <div className="border-t border-gray-800 px-6 py-4 sm:hidden bg-gray-950">
            <nav className="flex flex-col gap-4">
              <a
                href="#features"
                className="text-sm font-medium text-gray-300 hover:text-green-400 transition-colors"
                onClick={() => setMobileMenuOpen(false)}
              >
                Features
              </a>
              <a
                href="#how-it-works"
                className="text-sm font-medium text-gray-300 hover:text-green-400 transition-colors"
                onClick={() => setMobileMenuOpen(false)}
              >
                How it Works
              </a>
              <Link
                href="/login"
                className="text-sm font-medium text-gray-300 hover:text-green-400 transition-colors"
                onClick={() => setMobileMenuOpen(false)}
              >
                Sign in
              </Link>
              <Link href="/register" onClick={() => setMobileMenuOpen(false)}>
                <Button size="sm" className="w-full bg-green-600 hover:bg-green-700 text-white">Get Started</Button>
              </Link>
            </nav>
          </div>
        )}
      </header>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-gray-950 via-gray-900 to-green-950/20" />
        <div className="absolute inset-0 bg-[url('/grid.svg')] bg-center opacity-5" />
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-green-500/10 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl" />

        <div className="relative mx-auto max-w-7xl px-6 py-24 sm:py-32">
          <div className="mx-auto max-w-4xl text-center">
            <div className="mb-8 inline-flex items-center gap-2 rounded-full border border-green-800 bg-green-950/50 px-4 py-2 text-sm text-green-300 shadow-lg backdrop-blur-sm">
              <Sparkles className="h-4 w-4 text-green-400" />
              AI-Powered Biological Design Platform
            </div>
            <h1 className="text-5xl font-bold tracking-tight text-white sm:text-7xl">
              Design the future of
              <span className="block bg-gradient-to-r from-green-400 to-blue-400 bg-clip-text text-transparent">
                biological systems
              </span>
            </h1>
            <p className="mt-8 text-xl leading-8 text-gray-300 max-w-2xl mx-auto">
              QDesign is a collaborative platform where scientists explore biological
              knowledge, generate novel protein designs, and iteratively refine them
              using AI-powered, evidence-based reasoning.
            </p>
            <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link href="/register">
                <Button size="lg" className="gap-2 bg-green-600 hover:bg-green-700 text-white px-8 py-3 text-lg">
                  Start Designing
                  <ArrowRight className="h-5 w-5" />
                </Button>
              </Link>
              <Link href="/login">
                <Button size="lg" variant="outline" className="border-gray-700 text-gray-300 hover:bg-gray-800 px-8 py-3 text-lg">
                  Sign In
                </Button>
              </Link>
            </div>

            {/* Trust indicators */}
            <div className="mt-12 flex flex-wrap items-center justify-center gap-8 text-sm text-gray-400">
              <div className="flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-green-400" />
                <span>Evidence-based AI</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-green-400" />
                <span>Human supervision</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-green-400" />
                <span>Real-time collaboration</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="border-t border-gray-800 bg-gray-900 py-24">
        <div className="mx-auto max-w-7xl px-6">
          <div className="mx-auto max-w-2xl text-center mb-16">
            <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
              A complete workspace for biological invention
            </h2>
            <p className="mt-4 text-lg text-gray-300">
              Move beyond analysis into AI-driven design with explainable outputs
              and human supervision at every step.
            </p>
          </div>

          <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
            {/* Feature 1 */}
            <div className="group rounded-2xl border border-gray-700 bg-gray-900/50 p-8 shadow-sm hover:border-green-600/50 hover:shadow-green-500/10 transition-all duration-300 hover:-translate-y-1">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-green-500 to-green-600 border border-green-800 shadow-lg">
                <FlaskConical className="h-6 w-6 text-white" />
              </div>
              <h3 className="mt-6 text-lg font-semibold text-white">
                Protein & Antibody Engineering
              </h3>
              <p className="mt-3 text-gray-400 leading-relaxed">
                Define goals like binding affinity or stability, and let QDesign
                generate optimized mutated variants with explainable outputs.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="group rounded-2xl border border-gray-700 bg-gray-900/50 p-8 shadow-sm hover:border-green-600/50 hover:shadow-green-500/10 transition-all duration-300 hover:-translate-y-1">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 border border-blue-800 shadow-lg">
                <Microscope className="h-6 w-6 text-white" />
              </div>
              <h3 className="mt-6 text-lg font-semibold text-white">
                Enzyme Optimization
              </h3>
              <p className="mt-3 text-gray-400 leading-relaxed">
                Improve catalytic rates, substrate specificity, and industrial
                stability with AI-proposed designs backed by structural evidence.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="group rounded-2xl border border-gray-700 bg-gray-900/50 p-8 shadow-sm hover:border-green-600/50 hover:shadow-green-500/10 transition-all duration-300 hover:-translate-y-1">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-purple-500 to-purple-600 border border-purple-800 shadow-lg">
                <Target className="h-6 w-6 text-white" />
              </div>
              <h3 className="mt-6 text-lg font-semibold text-white">
                Drug Target Discovery
              </h3>
              <p className="mt-3 text-gray-400 leading-relaxed">
                Identify high-value therapeutic targets from disease-associated
                genes and proteins with evidence-based explanations.
              </p>
            </div>

            {/* Feature 4 */}
            <div className="group rounded-2xl border border-gray-700 bg-gray-900/50 p-8 shadow-sm hover:border-green-600/50 hover:shadow-green-500/10 transition-all duration-300 hover:-translate-y-1">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-500 to-cyan-600 border border-cyan-800 shadow-lg">
                <Network className="h-6 w-6 text-white" />
              </div>
              <h3 className="mt-6 text-lg font-semibold text-white">
                Knowledge Network
              </h3>
              <p className="mt-3 text-gray-400 leading-relaxed">
                Visualize and navigate an interpretable network of papers,
                structures, and experimental data with real-time collaboration.
              </p>
            </div>

            {/* Feature 5 */}
            <div className="group rounded-2xl border border-gray-700 bg-gray-900/50 p-8 shadow-sm hover:border-green-600/50 hover:shadow-green-500/10 transition-all duration-300 hover:-translate-y-1">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-pink-500 to-pink-600 border border-pink-800 shadow-lg">
                <Users className="h-6 w-6 text-white" />
              </div>
              <h3 className="mt-6 text-lg font-semibold text-white">
                Real-time Collaboration
              </h3>
              <p className="mt-3 text-gray-400 leading-relaxed">
                Work together with your team in shared research workspaces.
                Annotate, comment, and refine designs collaboratively.
              </p>
            </div>

            {/* Feature 6 */}
            <div className="group rounded-2xl border border-gray-700 bg-gray-900/50 p-8 shadow-sm hover:border-green-600/50 hover:shadow-green-500/10 transition-all duration-300 hover:-translate-y-1">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-yellow-500 to-yellow-600 border border-yellow-800 shadow-lg">
                <Brain className="h-6 w-6 text-white" />
              </div>
              <h3 className="mt-6 text-lg font-semibold text-white">
                AI Co-Scientist
              </h3>
              <p className="mt-3 text-gray-400 leading-relaxed">
                Let AI reason through your data, propose hypotheses, and generate
                designs while you supervise and guide the process.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* How it Works */}
      <section id="how-it-works" className="border-t border-gray-800 bg-gray-950 py-24">
        <div className="mx-auto max-w-7xl px-6">
          <div className="mx-auto max-w-2xl text-center mb-16">
            <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
              How QDesign Works
            </h2>
            <p className="mt-4 text-lg text-gray-300">
              A streamlined workflow from data to discovery
            </p>
          </div>

          <div className="grid gap-8 md:grid-cols-3">
            {/* Step 1 */}
            <div className="text-center">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-green-500 to-green-600 mb-6">
                <Database className="h-8 w-8 text-white" />
              </div>
              <div className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-green-600 text-white text-sm font-bold mb-4">
                1
              </div>
              <h3 className="text-xl font-semibold text-white mb-3">Upload & Explore</h3>
              <p className="text-gray-400">
                Upload your biological data - proteins, sequences, papers, and experimental results.
                Explore our knowledge network to understand relationships and patterns.
              </p>
            </div>

            {/* Step 2 */}
            <div className="text-center">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-blue-600 mb-6">
                <Brain className="h-8 w-8 text-white" />
              </div>
              <div className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-blue-600 text-white text-sm font-bold mb-4">
                2
              </div>
              <h3 className="text-xl font-semibold text-white mb-3">AI Analysis</h3>
              <p className="text-gray-400">
                Our AI co-scientist analyzes your data, identifies patterns, and generates
                hypotheses. Every suggestion comes with evidence and reasoning.
              </p>
            </div>

            {/* Step 3 */}
            <div className="text-center">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-purple-500 to-purple-600 mb-6">
                <Zap className="h-8 w-8 text-white" />
              </div>
              <div className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-purple-600 text-white text-sm font-bold mb-4">
                3
              </div>
              <h3 className="text-xl font-semibold text-white mb-3">Design & Refine</h3>
              <p className="text-gray-400">
                Generate novel designs, iterate with AI feedback, and collaborate with
                your team. Export results for experimental validation.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials/Social Proof */}
      <section className="border-t border-gray-800 bg-gray-900 py-24">
        <div className="mx-auto max-w-7xl px-6">
          <div className="mx-auto max-w-2xl text-center mb-16">
            <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
              Trusted by researchers worldwide
            </h2>
            <p className="mt-4 text-lg text-gray-300">
              Join leading scientists using QDesign for breakthrough discoveries
            </p>
          </div>

          <div className="grid gap-8 md:grid-cols-3">
            <div className="rounded-2xl border border-gray-700 bg-gray-900/50 p-6">
              <div className="flex items-center gap-1 mb-4">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                ))}
              </div>
              <p className="text-gray-300 mb-4">
                "QDesign transformed our enzyme optimization workflow. The AI suggestions
                are backed by real structural evidence, not just black-box predictions."
              </p>
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-full bg-gradient-to-br from-green-500 to-green-600 flex items-center justify-center">
                  <span className="text-white font-semibold text-sm">DR</span>
                </div>
                <div>
                  <p className="text-white font-medium">Dr. Sarah Chen</p>
                  <p className="text-gray-400 text-sm">Protein Engineer, BioTech Labs</p>
                </div>
              </div>
            </div>

            <div className="rounded-2xl border border-gray-700 bg-gray-900/50 p-6">
              <div className="flex items-center gap-1 mb-4">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                ))}
              </div>
              <p className="text-gray-300 mb-4">
                "The collaborative features are game-changing. Our team can now work
                together in real-time, with the AI providing insights we never considered."
              </p>
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center">
                  <span className="text-white font-semibold text-sm">MJ</span>
                </div>
                <div>
                  <p className="text-white font-medium">Dr. Michael Johnson</p>
                  <p className="text-gray-400 text-sm">Computational Biologist, PharmaCorp</p>
                </div>
              </div>
            </div>

            <div className="rounded-2xl border border-gray-700 bg-gray-900/50 p-6">
              <div className="flex items-center gap-1 mb-4">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                ))}
              </div>
              <p className="text-gray-300 mb-4">
                "Finally, an AI tool that doesn't just predict - it explains. Every design
                comes with structural reasoning that we can trust and build upon."
              </p>
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-full bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center">
                  <span className="text-white font-semibold text-sm">AR</span>
                </div>
                <div>
                  <p className="text-white font-medium">Dr. Anna Rodriguez</p>
                  <p className="text-gray-400 text-sm">Structural Biologist, Research Institute</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="border-t border-gray-800 bg-gray-950 py-24">
        <div className="mx-auto max-w-7xl px-6">
          <div className="mx-auto max-w-3xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
              Ready to transform your research?
            </h2>
            <p className="mt-4 text-xl text-gray-300">
              Join scientists worldwide using QDesign for breakthrough biological discoveries.
              Start your free trial today.
            </p>
            <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link href="/register">
                <Button size="lg" className="gap-2 bg-green-600 hover:bg-green-700 text-white px-8 py-4 text-lg">
                  Create Your Workspace
                  <ArrowRight className="h-5 w-5" />
                </Button>
              </Link>
              <Link href="/login">
                <Button size="lg" variant="outline" className="border-gray-700 text-gray-300 hover:bg-gray-800 px-8 py-4 text-lg">
                  Sign In to Existing Account
                </Button>
              </Link>
            </div>

            <p className="mt-6 text-sm text-gray-400">
              No credit card required • 14-day free trial • Cancel anytime
            </p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-800 bg-gray-950 py-12">
        <div className="mx-auto max-w-7xl px-6">
          <div className="grid gap-8 md:grid-cols-4">
            <div className="md:col-span-2">
              <div className="flex items-center gap-3 mb-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-green-500 to-green-600">
                  <Dna className="h-6 w-6 text-gray-900" />
                </div>
                <span className="text-xl font-bold text-green-400">QDesign</span>
              </div>
              <p className="text-gray-400 mb-4 max-w-md">
                AI-driven biological design platform for scientists who want to move
                beyond analysis into evidence-based innovation.
              </p>
              <div className="flex gap-4">
                <a href="#" className="text-gray-400 hover:text-green-400 transition-colors">
                  Twitter
                </a>
                <a href="#" className="text-gray-400 hover:text-green-400 transition-colors">
                  LinkedIn
                </a>
                <a href="#" className="text-gray-400 hover:text-green-400 transition-colors">
                  GitHub
                </a>
              </div>
            </div>

            <div>
              <h3 className="text-white font-semibold mb-4">Product</h3>
              <ul className="space-y-2 text-gray-400">
                <li><a href="#features" className="hover:text-green-400 transition-colors">Features</a></li>
                <li><a href="#how-it-works" className="hover:text-green-400 transition-colors">How it Works</a></li>
                <li><a href="#" className="hover:text-green-400 transition-colors">Pricing</a></li>
                <li><a href="#" className="hover:text-green-400 transition-colors">API</a></li>
              </ul>
            </div>

            <div>
              <h3 className="text-white font-semibold mb-4">Support</h3>
              <ul className="space-y-2 text-gray-400">
                <li><a href="#" className="hover:text-green-400 transition-colors">Documentation</a></li>
                <li><a href="#" className="hover:text-green-400 transition-colors">Help Center</a></li>
                <li><a href="#" className="hover:text-green-400 transition-colors">Contact Us</a></li>
                <li><a href="#" className="hover:text-green-400 transition-colors">Status</a></li>
              </ul>
            </div>
          </div>

          <div className="border-t border-gray-800 mt-8 pt-8 flex flex-col sm:flex-row items-center justify-between">
            <p className="text-sm text-gray-500">
              © 2026 QDesign. All rights reserved.
            </p>
            <div className="flex gap-6 mt-4 sm:mt-0">
              <a href="#" className="text-sm text-gray-500 hover:text-green-400 transition-colors">
                Privacy Policy
              </a>
              <a href="#" className="text-sm text-gray-500 hover:text-green-400 transition-colors">
                Terms of Service
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}