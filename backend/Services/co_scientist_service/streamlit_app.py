#!/usr/bin/env python
"""
Streamlit App for Co-Scientist Agent Testing

Features:
- Step-by-step workflow visualization
- Streaming agent outputs (token by token)
- Human-in-the-Loop checkpoints
- Nicely formatted outputs with post-processing
"""

import streamlit as st
import asyncio
import json
import re
import time
from pathlib import Path
from typing import AsyncIterator, Optional
from dataclasses import dataclass
from enum import Enum

# Set page config first
st.set_page_config(
    page_title="Co-Scientist Agent Testing",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import agents and tools
import sys
sys.path.insert(0, str(Path(__file__).parent))

from src.agents import (
    PlannerAgent,
    OntologistAgent, 
    ScientistAgent,
    Scientist2Agent,
    CriticAgent
)
from src.orchestration.checkpoints import CheckpointStage, CheckpointStatus


# ============================================================================
# CONSTANTS & ENUMS
# ============================================================================

class WorkflowStage(Enum):
    PLANNER = "planner"
    ONTOLOGIST = "ontologist"
    SCIENTIST = "scientist"
    SCIENTIST2 = "scientist2"
    CRITIC = "critic"


STAGE_INFO = {
    WorkflowStage.PLANNER: {
        "title": "🗺️ Planner Agent",
        "description": "Loads knowledge graph and extracts relevant subgraph",
        "icon": "🗺️"
    },
    WorkflowStage.ONTOLOGIST: {
        "title": "📚 Ontologist Agent", 
        "description": "Interprets concepts and relationships semantically",
        "icon": "📚"
    },
    WorkflowStage.SCIENTIST: {
        "title": "🔬 Scientist Agent",
        "description": "Generates initial hypothesis using 7-point framework",
        "icon": "🔬"
    },
    WorkflowStage.SCIENTIST2: {
        "title": "⚗️ Scientist2 Agent (Expander)",
        "description": "Expands hypothesis with quantitative details",
        "icon": "⚗️"
    },
    WorkflowStage.CRITIC: {
        "title": "🎯 Critic Agent",
        "description": "Evaluates hypothesis and provides decision",
        "icon": "🎯"
    }
}


# ============================================================================
# STREAMING HELPERS
# ============================================================================

def stream_text(text: str, placeholder, delay: float = 0.01):
    """Stream text character by character to a placeholder."""
    displayed = ""
    for char in text:
        displayed += char
        placeholder.markdown(displayed + "▌")
        time.sleep(delay)
    placeholder.markdown(displayed)
    return displayed


def stream_json_formatted(data: dict, placeholder, delay: float = 0.005):
    """Stream formatted JSON to a placeholder."""
    json_str = json.dumps(data, indent=2, ensure_ascii=False, default=str)
    stream_text(json_str, placeholder, delay)


async def collect_stream(stream: AsyncIterator[str]) -> tuple[str, list[str]]:
    """Collect all chunks from a stream."""
    chunks = []
    full_text = ""
    async for chunk in stream:
        chunks.append(chunk)
        full_text += chunk
    return full_text, chunks


# ============================================================================
# OUTPUT FORMATTERS
# ============================================================================

def format_planner_output(output: dict) -> str:
    """Format planner output for display."""
    if "error" in output:
        return f"❌ **Error:** {output['error']}"
    
    lines = ["### 📍 Path Found\n"]
    
    subgraph = output.get("subgraph", {})
    path = subgraph.get("path", {})
    
    if path:
        lines.append(f"**Path:** `{path.get('source', '?')}` → `{path.get('target', '?')}`\n")
        lines.append(f"**Confidence:** {path.get('total_strength', 0):.2%}\n")
        lines.append(f"**Route:** {path.get('path_string', 'N/A')}\n")
    
    nodes = subgraph.get("nodes", [])
    if nodes:
        lines.append(f"\n### 🔵 Nodes ({len(nodes)})\n")
        for node in nodes[:6]:
            features = ", ".join(node.get("biological_features", [])[:3])
            lines.append(f"- **{node.get('label', node.get('id'))}** ({node.get('type')})")
            if features:
                lines.append(f"  - Features: {features}")
    
    edges = subgraph.get("edges", [])
    if edges:
        lines.append(f"\n### 🔗 Edges ({len(edges)})\n")
        for edge in edges[:5]:
            lines.append(f"- {edge.get('source')} --[{edge.get('label')}]--> {edge.get('target')} (strength: {edge.get('strength', 0):.2f})")
    
    return "\n".join(lines)


def format_ontologist_output(output: dict) -> str:
    """Format ontologist output for display."""
    if "error" in output:
        return f"❌ **Error:** {output['error']}"
    
    lines = ["### 📖 Concept Definitions\n"]
    
    for defn in output.get("concept_definitions", [])[:4]:
        lines.append(f"**{defn.get('concept_label', defn.get('concept_id'))}**")
        lines.append(f"> {defn.get('definition', 'No definition')[:200]}...")
        lines.append("")
    
    lines.append("\n### 🔗 Key Relationships\n")
    for rel in output.get("relationship_explanations", [])[:3]:
        lines.append(f"- **{rel.get('from_concept')}** → **{rel.get('to_concept')}**")
        lines.append(f"  - *{rel.get('relationship')}*: {rel.get('explanation', '')[:150]}...")
    
    narrative = output.get("narrative_synthesis", {})
    if narrative:
        lines.append("\n### 📝 Narrative Synthesis\n")
        lines.append(f"> {narrative.get('overview', '')[:300]}...")
    
    return "\n".join(lines)


def format_scientist_output(output: dict) -> str:
    """Format scientist output for display."""
    if "error" in output:
        return f"❌ **Error:** {output['error']}"
    
    lines = []
    
    hypothesis = output.get("hypothesis", {})
    if hypothesis:
        lines.append(f"### 💡 {hypothesis.get('title', 'Hypothesis')}\n")
        lines.append(f"**Statement:** {hypothesis.get('statement', 'N/A')}\n")
    
    outcomes = output.get("expected_outcomes", {})
    if outcomes:
        lines.append("\n### 🎯 Expected Outcomes\n")
        lines.append(f"**Primary:** {outcomes.get('primary', 'N/A')}\n")
        for sec in outcomes.get("secondary", [])[:2]:
            lines.append(f"- {sec}")
    
    mechanisms = output.get("mechanisms", {})
    if mechanisms:
        lines.append("\n### ⚙️ Mechanisms\n")
        lines.append(f"{mechanisms.get('overview', 'N/A')[:300]}...")
    
    novelty = output.get("novelty", {})
    if novelty:
        lines.append(f"\n### ⭐ Novelty Score: {novelty.get('score', '?')}/10\n")
        lines.append(f"> {novelty.get('justification', '')[:200]}...")
    
    return "\n".join(lines)


def format_scientist2_output(output: dict) -> str:
    """Format scientist2 output for display."""
    if "error" in output:
        return f"❌ **Error:** {output['error']}"
    
    lines = []
    
    expanded = output.get("expanded_hypothesis", {})
    if expanded:
        lines.append(f"### 🔬 {expanded.get('title', 'Expanded Hypothesis')}\n")
        lines.append(f"**Statement:** {expanded.get('statement', 'N/A')[:300]}...\n")
        
        predictions = expanded.get("quantitative_predictions", [])
        if predictions:
            lines.append("\n**Quantitative Predictions:**")
            for pred in predictions[:3]:
                lines.append(f"- {pred.get('prediction')}: **{pred.get('expected_value')}**")
    
    methods = output.get("methodologies", {})
    if methods:
        lines.append("\n### 🧪 Methodologies\n")
        for comp in methods.get("computational", [])[:2]:
            lines.append(f"- **{comp.get('method')}** ({comp.get('software', 'N/A')})")
    
    protocols = output.get("experimental_protocols", [])
    if protocols:
        lines.append(f"\n### 📋 Experimental Protocols ({len(protocols)} phases)\n")
        for protocol in protocols[:2]:
            lines.append(f"**{protocol.get('phase')}:** {len(protocol.get('steps', []))} steps")
    
    risk = output.get("risk_assessment", {})
    if risk:
        timeline = risk.get("timeline_estimate", {})
        lines.append(f"\n### ⏱️ Timeline: {timeline.get('total', 'N/A')}")
    
    return "\n".join(lines)


def format_critic_output(output: dict) -> str:
    """Format critic output for display."""
    if "error" in output:
        return f"❌ **Error:** {output['error']}"
    
    lines = []
    
    decision = output.get("decision", "UNKNOWN")
    decision_emoji = {"APPROVE": "✅", "REVISE": "🔄", "REJECT": "❌"}.get(decision, "❓")
    
    lines.append(f"## {decision_emoji} Decision: **{decision}**\n")
    lines.append(f"> {output.get('summary', 'No summary')[:200]}...\n")
    
    scores = output.get("scores", {})
    if scores:
        lines.append("\n### 📊 Scores\n")
        lines.append("| Category | Score |")
        lines.append("|----------|-------|")
        for cat, data in scores.items():
            if isinstance(data, dict) and "score" in data:
                lines.append(f"| {cat.replace('_', ' ').title()} | {data['score']}/{data.get('max', 10)} |")
    
    strengths = output.get("strengths", [])
    if strengths:
        lines.append("\n### 💪 Strengths\n")
        for s in strengths[:2]:
            lines.append(f"- **{s.get('aspect')}**: {s.get('description', '')[:100]}...")
    
    weaknesses = output.get("weaknesses", [])
    if weaknesses:
        lines.append("\n### ⚠️ Weaknesses\n")
        for w in weaknesses[:2]:
            severity = w.get("severity", "minor")
            emoji = {"critical": "🔴", "major": "🟠", "minor": "🟡"}.get(severity, "⚪")
            lines.append(f"- {emoji} **{w.get('aspect')}** ({severity}): {w.get('description', '')[:100]}...")
    
    revisions = output.get("required_revisions", [])
    if revisions:
        lines.append("\n### 📝 Required Revisions\n")
        for rev in revisions[:3]:
            lines.append(f"1. **{rev.get('what')}**")
            lines.append(f"   - Why: {rev.get('why', '')[:80]}...")
    
    return "\n".join(lines)


FORMATTERS = {
    WorkflowStage.PLANNER: format_planner_output,
    WorkflowStage.ONTOLOGIST: format_ontologist_output,
    WorkflowStage.SCIENTIST: format_scientist_output,
    WorkflowStage.SCIENTIST2: format_scientist2_output,
    WorkflowStage.CRITIC: format_critic_output,
}


# ============================================================================
# AGENT RUNNERS WITH STREAMING
# ============================================================================

async def run_agent_with_streaming(
    agent,
    state: dict,
    stage: WorkflowStage,
    output_container,
    use_streaming: bool = True
) -> dict:
    """Run an agent and stream its output."""
    
    info = STAGE_INFO[stage]
    
    with output_container:
        st.markdown(f"### {info['title']}")
        st.caption(info['description'])
        
        # Progress indicator
        progress_placeholder = st.empty()
        progress_placeholder.info("🔄 Processing...")
        
        # Output placeholder
        output_placeholder = st.empty()
        raw_output_expander = st.expander("📄 Raw JSON Output", expanded=False)
        
        try:
            if use_streaming and hasattr(agent, 'run_stream'):
                # Use streaming
                output_placeholder.markdown("*Generating...*")
                
                full_response = ""
                async for chunk in agent.run_stream(state):
                    full_response += chunk
                    # Try to parse partial JSON for display
                    try:
                        partial = json.loads(full_response)
                        formatter = FORMATTERS.get(stage, lambda x: json.dumps(x, indent=2))
                        output_placeholder.markdown(formatter(partial))
                    except json.JSONDecodeError:
                        # Show raw streaming text
                        output_placeholder.code(full_response[-500:] + "...", language="json")
                
                # Final parse
                try:
                    result = json.loads(full_response)
                except json.JSONDecodeError:
                    result = {"raw_response": full_response, "error": "Failed to parse JSON"}
                
                confidence = 0.8  # Default for streaming
            else:
                # Non-streaming
                result_obj = await agent.run(state)
                result = result_obj.output
                confidence = result_obj.confidence
                
                # Stream the formatted output
                formatter = FORMATTERS.get(stage, lambda x: json.dumps(x, indent=2))
                formatted = formatter(result)
                
                # Simulate streaming for visual effect
                displayed = ""
                for char in formatted:
                    displayed += char
                    output_placeholder.markdown(displayed + "▌")
                    await asyncio.sleep(0.002)  # Small delay for streaming effect
                output_placeholder.markdown(displayed)
            
            # Show raw JSON
            with raw_output_expander:
                st.json(result)
            
            # Update progress
            progress_placeholder.success(f"✅ Completed (Confidence: {confidence:.0%})")
            
            return result
            
        except Exception as e:
            progress_placeholder.error(f"❌ Error: {str(e)}")
            return {"error": str(e)}


# ============================================================================
# HITL CHECKPOINT UI
# ============================================================================

def render_hitl_checkpoint(
    stage: WorkflowStage,
    output: dict,
    checkpoint_key: str
) -> tuple[str, Optional[dict]]:
    """Render HITL checkpoint UI and return decision."""
    
    st.markdown("---")
    st.markdown("### 🛑 Human-in-the-Loop Checkpoint")
    st.markdown(f"**Stage:** {STAGE_INFO[stage]['title']}")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("✅ Approve", key=f"{checkpoint_key}_approve", type="primary"):
            return "approved", None
    
    with col2:
        if st.button("🔄 Modify", key=f"{checkpoint_key}_modify"):
            return "modify", None
    
    with col3:
        if st.button("❌ Reject", key=f"{checkpoint_key}_reject"):
            return "rejected", None
    
    # Modification input
    with st.expander("✏️ Modify Output", expanded=False):
        modified_json = st.text_area(
            "Edit the output JSON:",
            value=json.dumps(output, indent=2, default=str),
            height=300,
            key=f"{checkpoint_key}_edit"
        )
        
        if st.button("Apply Modifications", key=f"{checkpoint_key}_apply"):
            try:
                modified = json.loads(modified_json)
                return "modified", modified
            except json.JSONDecodeError as e:
                st.error(f"Invalid JSON: {e}")
    
    # Feedback input
    feedback = st.text_input(
        "Optional feedback:",
        key=f"{checkpoint_key}_feedback",
        placeholder="Enter any notes or feedback..."
    )
    
    return "pending", None


# ============================================================================
# MAIN WORKFLOW
# ============================================================================

async def run_workflow(
    kg_path: str,
    concept_a: str,
    concept_b: str,
    user_query: str,
    hitl_enabled: bool,
    hitl_stages: list[str],
    enable_streaming: bool,
    enable_ontologist: bool,
    enable_scientist2: bool,
    enable_literature: bool
):
    """Run the full agent workflow with streaming and HITL."""
    
    # Initialize session state for workflow
    if "workflow_state" not in st.session_state:
        st.session_state.workflow_state = {}
    
    workflow_state = st.session_state.workflow_state
    
    # Create main containers
    stages_container = st.container()
    
    with stages_container:
        # ========== STAGE 1: PLANNER ==========
        st.markdown("## 📍 Stage 1: Planning")
        planner_container = st.container()
        
        planner = PlannerAgent()
        planner_state = {
            "kg_path": kg_path,
            "concept_a": concept_a,
            "concept_b": concept_b,
            "exploration_mode": "balanced",
            "max_paths": 3
        }
        
        planner_output = await run_agent_with_streaming(
            planner, planner_state, WorkflowStage.PLANNER,
            planner_container, use_streaming=False  # Planner doesn't stream
        )
        
        if "error" in planner_output:
            st.error("Planner failed. Cannot continue workflow.")
            return
        
        workflow_state["planner_output"] = planner_output
        
        # HITL Checkpoint for Planner
        if hitl_enabled and "planner" in hitl_stages:
            decision, modified = render_hitl_checkpoint(
                WorkflowStage.PLANNER, planner_output, "planner_hitl"
            )
            if decision == "rejected":
                st.warning("Workflow stopped by user at Planner stage.")
                return
            elif decision == "modified" and modified:
                planner_output = modified
                workflow_state["planner_output"] = planner_output
            elif decision == "pending":
                st.info("⏸️ Waiting for checkpoint decision...")
                return
        
        st.markdown("---")
        
        # ========== STAGE 2: ONTOLOGIST (Optional) ==========
        ontologist_output = {}
        if enable_ontologist:
            st.markdown("## 📚 Stage 2: Ontology Analysis")
            ontologist_container = st.container()
            
            ontologist = OntologistAgent()
            ontologist_state = {
                "planner_output": planner_output,
                "user_query": user_query
            }
            
            ontologist_output = await run_agent_with_streaming(
                ontologist, ontologist_state, WorkflowStage.ONTOLOGIST,
                ontologist_container, use_streaming=enable_streaming
            )
            
            workflow_state["ontologist_output"] = ontologist_output
            
            # HITL Checkpoint
            if hitl_enabled and "ontologist" in hitl_stages:
                decision, modified = render_hitl_checkpoint(
                    WorkflowStage.ONTOLOGIST, ontologist_output, "ontologist_hitl"
                )
                if decision == "rejected":
                    st.warning("Workflow stopped by user at Ontologist stage.")
                    return
                elif decision == "modified" and modified:
                    ontologist_output = modified
                    workflow_state["ontologist_output"] = ontologist_output
                elif decision == "pending":
                    st.info("⏸️ Waiting for checkpoint decision...")
                    return
            
            st.markdown("---")
        
        # ========== STAGE 3: SCIENTIST ==========
        st.markdown("## 🔬 Stage 3: Hypothesis Generation")
        scientist_container = st.container()
        
        scientist = ScientistAgent()
        scientist_state = {
            "planner_output": planner_output,
            "user_query": user_query
        }
        
        scientist_output = await run_agent_with_streaming(
            scientist, scientist_state, WorkflowStage.SCIENTIST,
            scientist_container, use_streaming=enable_streaming
        )
        
        if "error" in scientist_output:
            st.error("Scientist failed. Cannot continue workflow.")
            return
        
        workflow_state["scientist_output"] = scientist_output
        
        # HITL Checkpoint
        if hitl_enabled and "scientist" in hitl_stages:
            decision, modified = render_hitl_checkpoint(
                WorkflowStage.SCIENTIST, scientist_output, "scientist_hitl"
            )
            if decision == "rejected":
                st.warning("Workflow stopped by user at Scientist stage.")
                return
            elif decision == "modified" and modified:
                scientist_output = modified
                workflow_state["scientist_output"] = scientist_output
            elif decision == "pending":
                st.info("⏸️ Waiting for checkpoint decision...")
                return
        
        st.markdown("---")
        
        # ========== STAGE 4: SCIENTIST2 (Optional) ==========
        expanded_hypothesis = scientist_output
        if enable_scientist2:
            st.markdown("## ⚗️ Stage 4: Hypothesis Expansion")
            scientist2_container = st.container()
            
            scientist2 = Scientist2Agent(enable_literature_search=enable_literature)
            scientist2_state = {
                "hypothesis": scientist_output,
                "planner_output": planner_output,
                "ontologist_output": ontologist_output,
                "user_query": user_query
            }
            
            scientist2_output = await run_agent_with_streaming(
                scientist2, scientist2_state, WorkflowStage.SCIENTIST2,
                scientist2_container, use_streaming=enable_streaming
            )
            
            expanded_hypothesis = scientist2_output
            workflow_state["scientist2_output"] = scientist2_output
            
            # HITL Checkpoint
            if hitl_enabled and "scientist2" in hitl_stages:
                decision, modified = render_hitl_checkpoint(
                    WorkflowStage.SCIENTIST2, scientist2_output, "scientist2_hitl"
                )
                if decision == "rejected":
                    st.warning("Workflow stopped by user at Scientist2 stage.")
                    return
                elif decision == "modified" and modified:
                    expanded_hypothesis = modified
                    workflow_state["scientist2_output"] = expanded_hypothesis
                elif decision == "pending":
                    st.info("⏸️ Waiting for checkpoint decision...")
                    return
            
            st.markdown("---")
        
        # ========== STAGE 5: CRITIC ==========
        st.markdown("## 🎯 Stage 5: Critical Evaluation")
        critic_container = st.container()
        
        critic = CriticAgent()
        critic_state = {
            "hypothesis": expanded_hypothesis,
            "planner_output": planner_output,
            "iteration": 1
        }
        
        critic_output = await run_agent_with_streaming(
            critic, critic_state, WorkflowStage.CRITIC,
            critic_container, use_streaming=enable_streaming
        )
        
        workflow_state["critic_output"] = critic_output
        
        # HITL Checkpoint for final decision
        if hitl_enabled and "critic" in hitl_stages:
            decision, modified = render_hitl_checkpoint(
                WorkflowStage.CRITIC, critic_output, "critic_hitl"
            )
            if decision == "modified" and modified:
                critic_output = modified
                workflow_state["critic_output"] = critic_output
        
        st.markdown("---")
        
        # ========== FINAL SUMMARY ==========
        st.markdown("## 🏁 Workflow Complete")
        
        final_decision = critic_output.get("decision", "UNKNOWN")
        decision_emoji = {"APPROVE": "✅", "REVISE": "🔄", "REJECT": "❌"}.get(final_decision, "❓")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Final Decision", f"{decision_emoji} {final_decision}")
        with col2:
            overall = critic_output.get("scores", {}).get("overall", {})
            score = overall.get("score", "N/A") if isinstance(overall, dict) else "N/A"
            st.metric("Overall Score", f"{score}/10")
        with col3:
            st.metric("Stages Completed", "5" if enable_ontologist and enable_scientist2 else "3-4")
        
        # Download results
        st.download_button(
            label="📥 Download Full Results (JSON)",
            data=json.dumps(workflow_state, indent=2, default=str),
            file_name="co_scientist_results.json",
            mime="application/json"
        )


# ============================================================================
# SIDEBAR CONFIGURATION
# ============================================================================

def render_sidebar():
    """Render sidebar configuration."""
    
    st.sidebar.title("🔬 Co-Scientist")
    st.sidebar.markdown("### Configuration")
    
    # Knowledge Graph Selection
    st.sidebar.subheader("📊 Knowledge Graph")
    
    kg_files = list(Path("data/knowledge_graphs").glob("*.json"))
    kg_options = {f.name: str(f) for f in kg_files}
    
    if kg_options:
        selected_kg = st.sidebar.selectbox(
            "Select Knowledge Graph",
            options=list(kg_options.keys()),
            index=0
        )
        kg_path = kg_options[selected_kg]
    else:
        kg_path = st.sidebar.text_input(
            "Knowledge Graph Path",
            value="data/knowledge_graphs/test_hemoglobin_kg.json"
        )
    
    # Concept Selection
    st.sidebar.subheader("🔗 Concepts to Connect")
    concept_a = st.sidebar.text_input("Concept A", value="hemoglobin_alpha")
    concept_b = st.sidebar.text_input("Concept B", value="low_temperature")
    
    # User Query
    st.sidebar.subheader("❓ Research Query")
    user_query = st.sidebar.text_area(
        "Query",
        value="How does cold temperature affect hemoglobin oxygen binding in arctic fish?",
        height=100
    )
    
    # Workflow Options
    st.sidebar.subheader("⚙️ Workflow Options")
    enable_streaming = st.sidebar.checkbox("Enable Streaming Output", value=True)
    enable_ontologist = st.sidebar.checkbox("Enable Ontologist Agent", value=True)
    enable_scientist2 = st.sidebar.checkbox("Enable Scientist2 (Expander)", value=True)
    enable_literature = st.sidebar.checkbox("Enable Literature Search", value=False)
    
    # HITL Configuration
    st.sidebar.subheader("🛑 Human-in-the-Loop")
    hitl_enabled = st.sidebar.checkbox("Enable HITL Checkpoints", value=True)
    
    hitl_stages = []
    if hitl_enabled:
        st.sidebar.markdown("**Checkpoint Stages:**")
        if st.sidebar.checkbox("After Planner", value=False):
            hitl_stages.append("planner")
        if st.sidebar.checkbox("After Ontologist", value=False):
            hitl_stages.append("ontologist")
        if st.sidebar.checkbox("After Scientist", value=True):
            hitl_stages.append("scientist")
        if st.sidebar.checkbox("After Scientist2", value=False):
            hitl_stages.append("scientist2")
        if st.sidebar.checkbox("After Critic", value=True):
            hitl_stages.append("critic")
    
    return {
        "kg_path": kg_path,
        "concept_a": concept_a,
        "concept_b": concept_b,
        "user_query": user_query,
        "enable_streaming": enable_streaming,
        "enable_ontologist": enable_ontologist,
        "enable_scientist2": enable_scientist2,
        "enable_literature": enable_literature,
        "hitl_enabled": hitl_enabled,
        "hitl_stages": hitl_stages
    }


# ============================================================================
# MAIN APP
# ============================================================================

def main():
    """Main Streamlit app."""
    
    st.title("🔬 Co-Scientist Agent Testing")
    st.markdown("*Interactive testing of the multi-agent scientific hypothesis workflow*")
    
    # Get configuration from sidebar
    config = render_sidebar()
    
    # Main content area
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("### Workflow Configuration")
        st.markdown(f"""
        - **Knowledge Graph:** `{Path(config['kg_path']).name}`
        - **Connecting:** `{config['concept_a']}` → `{config['concept_b']}`
        - **Query:** {config['user_query'][:50]}...
        - **HITL:** {'Enabled' if config['hitl_enabled'] else 'Disabled'}
        """)
    
    with col2:
        run_button = st.button("🚀 Run Workflow", type="primary", use_container_width=True)
        
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state.workflow_state = {}
            st.rerun()
    
    st.markdown("---")
    
    # Run workflow
    if run_button:
        st.session_state.workflow_state = {}  # Reset state
        
        # Run async workflow
        asyncio.run(run_workflow(
            kg_path=config["kg_path"],
            concept_a=config["concept_a"],
            concept_b=config["concept_b"],
            user_query=config["user_query"],
            hitl_enabled=config["hitl_enabled"],
            hitl_stages=config["hitl_stages"],
            enable_streaming=config["enable_streaming"],
            enable_ontologist=config["enable_ontologist"],
            enable_scientist2=config["enable_scientist2"],
            enable_literature=config["enable_literature"]
        ))
    
    # Show previous results if available
    elif st.session_state.get("workflow_state"):
        st.info("Previous workflow results are shown below. Click 'Run Workflow' to start a new run.")
        
        with st.expander("📊 Previous Results", expanded=True):
            st.json(st.session_state.workflow_state)


if __name__ == "__main__":
    main()
