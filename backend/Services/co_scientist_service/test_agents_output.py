#!/usr/bin/env python
"""
Test script to run and display agent outputs.

This script demonstrates the full agent pipeline:
1. Planner Agent - Loads KG and extracts subgraph
2. Ontologist Agent - Interprets the subgraph concepts
3. Scientist Agent - Generates initial hypothesis
4. Scientist2 Agent - Expands hypothesis with details
5. Critic Agent - Evaluates the hypothesis

Usage:
    cd /home/ghassen/Projects/Selecao-QDesign/backend/Services/co_scientist_service
    ./co_scientist_venv/bin/python test_agents_output.py
"""

import asyncio
import json
import os
from pathlib import Path

# Ensure we're in the right directory
os.chdir(Path(__file__).parent)

from src.agents import (
    PlannerAgent,
    OntologistAgent,
    ScientistAgent,
    Scientist2Agent,
    CriticAgent
)


def print_section(title: str, width: int = 80):
    """Print a section header."""
    print("\n" + "=" * width)
    print(f" {title} ".center(width, "="))
    print("=" * width + "\n")


def print_json(data: dict, indent: int = 2):
    """Pretty print JSON data."""
    print(json.dumps(data, indent=indent, ensure_ascii=False, default=str))


def print_agent_result(name: str, result):
    """Print an agent result nicely."""
    print_section(f"{name} OUTPUT")
    print(f"Confidence: {result.confidence:.2%}")
    print("-" * 40)
    print_json(result.output)


async def test_planner_agent():
    """Test the Planner Agent."""
    print_section("PLANNER AGENT TEST")
    
    planner = PlannerAgent()
    kg_path = "data/knowledge_graphs/test_hemoglobin_kg.json"
    
    # Check if KG exists
    if not Path(kg_path).exists():
        print(f"❌ Knowledge graph not found: {kg_path}")
        return None
    
    state = {
        "kg_path": kg_path,
        "concept_a": "hemoglobin_alpha",
        "concept_b": "low_temperature",
        "exploration_mode": "balanced",
        "max_paths": 3
    }
    
    print(f"Input state:")
    print_json(state)
    
    result = await planner.run(state)
    print_agent_result("Planner", result)
    
    return result


async def test_ontologist_agent(planner_output: dict):
    """Test the Ontologist Agent."""
    print_section("ONTOLOGIST AGENT TEST")
    
    ontologist = OntologistAgent()
    
    state = {
        "planner_output": planner_output,
        "user_query": "How does cold temperature affect hemoglobin oxygen binding?"
    }
    
    print(f"Input: Analyzing subgraph with {len(planner_output.get('subgraph', {}).get('nodes', []))} nodes")
    
    result = await ontologist.run(state)
    print_agent_result("Ontologist", result)
    
    return result


async def test_scientist_agent(planner_output: dict):
    """Test the Scientist Agent."""
    print_section("SCIENTIST AGENT TEST")
    
    scientist = ScientistAgent()
    
    state = {
        "planner_output": planner_output,
        "user_query": "How does cold temperature affect hemoglobin oxygen binding in arctic fish?"
    }
    
    print(f"Input: Generating hypothesis from subgraph")
    
    result = await scientist.run(state)
    print_agent_result("Scientist", result)
    
    return result


async def test_scientist2_agent(hypothesis: dict, planner_output: dict, ontologist_output: dict):
    """Test the Scientist2 Agent (Expander)."""
    print_section("SCIENTIST2 AGENT TEST (EXPANDER)")
    
    # Disable literature search for faster testing
    scientist2 = Scientist2Agent(enable_literature_search=False)
    
    state = {
        "hypothesis": hypothesis,
        "planner_output": planner_output,
        "ontologist_output": ontologist_output,
        "user_query": "How does cold temperature affect hemoglobin oxygen binding in arctic fish?"
    }
    
    print(f"Input: Expanding hypothesis with scientific details")
    
    result = await scientist2.run(state)
    print_agent_result("Scientist2", result)
    
    return result


async def test_critic_agent(hypothesis: dict, planner_output: dict):
    """Test the Critic Agent."""
    print_section("CRITIC AGENT TEST")
    
    critic = CriticAgent()
    
    state = {
        "hypothesis": hypothesis,
        "planner_output": planner_output,
        "iteration": 1
    }
    
    print(f"Input: Evaluating hypothesis quality")
    
    result = await critic.run(state)
    print_agent_result("Critic", result)
    
    # Show decision
    decision = result.output.get("decision", "UNKNOWN")
    print(f"\n🎯 Final Decision: {decision}")
    
    if decision == "REVISE":
        guidance = critic.get_revision_guidance(result.output)
        print("\n📝 Revision Guidance:")
        print_json(guidance)
    
    return result


async def run_full_pipeline():
    """Run the full agent pipeline."""
    print_section("FULL AGENT PIPELINE TEST", width=90)
    print("This test runs all agents in sequence:\n")
    print("  1. Planner    → Load KG, find paths, extract subgraph")
    print("  2. Ontologist → Interpret concepts and relationships")
    print("  3. Scientist  → Generate initial hypothesis")
    print("  4. Scientist2 → Expand with scientific details")
    print("  5. Critic     → Evaluate hypothesis quality")
    print("\n" + "-" * 90)
    
    # Step 1: Planner
    planner_result = await test_planner_agent()
    if not planner_result or "error" in planner_result.output:
        print("❌ Planner failed, stopping pipeline")
        return
    
    planner_output = planner_result.output
    
    # Step 2: Ontologist
    ontologist_result = await test_ontologist_agent(planner_output)
    ontologist_output = ontologist_result.output if ontologist_result else {}
    
    # Step 3: Scientist
    scientist_result = await test_scientist_agent(planner_output)
    if not scientist_result or "error" in scientist_result.output:
        print("❌ Scientist failed, stopping pipeline")
        return
    
    hypothesis = scientist_result.output
    
    # Step 4: Scientist2 (Expander)
    scientist2_result = await test_scientist2_agent(hypothesis, planner_output, ontologist_output)
    expanded_hypothesis = scientist2_result.output if scientist2_result else hypothesis
    
    # Step 5: Critic
    critic_result = await test_critic_agent(expanded_hypothesis, planner_output)
    
    # Summary
    print_section("PIPELINE SUMMARY", width=90)
    print(f"✅ Planner confidence:    {planner_result.confidence:.2%}")
    if ontologist_result:
        print(f"✅ Ontologist confidence: {ontologist_result.confidence:.2%}")
    print(f"✅ Scientist confidence:  {scientist_result.confidence:.2%}")
    if scientist2_result:
        print(f"✅ Scientist2 confidence: {scientist2_result.confidence:.2%}")
    print(f"✅ Critic confidence:     {critic_result.confidence:.2%}")
    print(f"\n🎯 Final Decision: {critic_result.output.get('decision', 'UNKNOWN')}")


async def test_single_agent(agent_name: str):
    """Test a single agent interactively."""
    print_section(f"TESTING {agent_name.upper()} AGENT")
    
    if agent_name == "planner":
        return await test_planner_agent()
    
    # For other agents, we need planner output first
    print("Running planner first to get subgraph...")
    planner_result = await test_planner_agent()
    if not planner_result or "error" in planner_result.output:
        print("❌ Planner failed")
        return None
    
    planner_output = planner_result.output
    
    if agent_name == "ontologist":
        return await test_ontologist_agent(planner_output)
    
    elif agent_name == "scientist":
        return await test_scientist_agent(planner_output)
    
    elif agent_name == "scientist2":
        # Need scientist output first
        scientist_result = await test_scientist_agent(planner_output)
        ontologist_result = await test_ontologist_agent(planner_output)
        return await test_scientist2_agent(
            scientist_result.output, 
            planner_output, 
            ontologist_result.output
        )
    
    elif agent_name == "critic":
        scientist_result = await test_scientist_agent(planner_output)
        return await test_critic_agent(scientist_result.output, planner_output)
    
    else:
        print(f"Unknown agent: {agent_name}")
        return None


def main():
    """Main entry point."""
    import sys
    
    if len(sys.argv) > 1:
        agent_name = sys.argv[1].lower()
        if agent_name == "all":
            asyncio.run(run_full_pipeline())
        else:
            asyncio.run(test_single_agent(agent_name))
    else:
        # Default: run full pipeline
        print("Usage: python test_agents_output.py [agent_name|all]")
        print("  Agents: planner, ontologist, scientist, scientist2, critic, all")
        print("\nRunning full pipeline by default...\n")
        asyncio.run(run_full_pipeline())


if __name__ == "__main__":
    main()
