#!/usr/bin/env python
"""
Co-Scientist Agent Platform

An elegant, bio-lab inspired interface for multi-agent
scientific hypothesis generation.

Design: Light, clean, professional bio-lab aesthetic
"""

import streamlit as st
import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional
from enum import Enum
from dataclasses import dataclass

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="Co-Scientist | Research Platform",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# ELEGANT BIO-LAB THEME CSS
# ============================================================================

st.markdown("""
<style>
    /* ===== IMPORTS ===== */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=IBM+Plex+Mono:wght@400;500&display=swap');
    
    /* ===== CSS VARIABLES ===== */
    :root {
        /* Light Bio-Lab Palette */
        --bg-primary: #f8faf9;
        --bg-secondary: #ffffff;
        --bg-accent: #f0f7f4;
        --bg-card: #ffffff;
        
        /* Text Colors */
        --text-primary: #1a2f23;
        --text-secondary: #4a5d52;
        --text-muted: #7a8f82;
        --text-light: #9aab9f;
        
        /* Brand Colors - Elegant Bio Tones */
        --bio-emerald: #059669;
        --bio-teal: #0d9488;
        --bio-cyan: #06b6d4;
        --bio-sage: #84cc16;
        --bio-mint: #10b981;
        
        /* Accent Colors */
        --accent-purple: #7c3aed;
        --accent-blue: #3b82f6;
        --accent-amber: #f59e0b;
        --accent-rose: #e11d48;
        
        /* Status Colors */
        --status-success: #059669;
        --status-warning: #d97706;
        --status-error: #dc2626;
        --status-info: #0891b2;
        
        /* Shadows & Effects */
        --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.04);
        --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.06);
        --shadow-lg: 0 12px 40px rgba(0, 0, 0, 0.08);
        --shadow-glow: 0 0 40px rgba(5, 150, 105, 0.12);
        
        /* Borders */
        --border-light: #e5ebe8;
        --border-medium: #d1dbd5;
    }
    
    /* ===== GLOBAL STYLES ===== */
    .stApp {
        background: linear-gradient(180deg, #f8faf9 0%, #f0f7f4 100%);
    }
    
    /* Hide Streamlit defaults */
    #MainMenu, footer, header, .stDeployButton {
        display: none !important;
    }
    
    /* Typography */
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
        color: var(--text-primary);
    }
    
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 700 !important;
        color: var(--text-primary) !important;
        letter-spacing: -0.02em;
    }
    
    code, pre, .stCode {
        font-family: 'IBM Plex Mono', monospace !important;
    }
    
    /* ===== CUSTOM SCROLLBAR ===== */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: var(--bg-accent);
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb {
        background: var(--border-medium);
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: var(--text-muted);
    }
    
    /* ===== HERO SECTION ===== */
    .hero-container {
        text-align: center;
        padding: 3rem 2rem;
        margin-bottom: 2rem;
    }
    
    .hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        background: linear-gradient(135deg, rgba(5, 150, 105, 0.1), rgba(6, 182, 212, 0.1));
        border: 1px solid rgba(5, 150, 105, 0.2);
        border-radius: 100px;
        font-size: 0.75rem;
        font-weight: 600;
        color: var(--bio-emerald);
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 1.5rem;
    }
    
    .hero-title {
        font-size: 3rem;
        font-weight: 800;
        color: var(--text-primary);
        margin: 0 0 0.75rem 0;
        line-height: 1.1;
        letter-spacing: -0.03em;
    }
    
    .hero-title-accent {
        background: linear-gradient(135deg, var(--bio-emerald) 0%, var(--bio-teal) 50%, var(--bio-cyan) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .hero-subtitle {
        font-size: 1.125rem;
        color: var(--text-secondary);
        font-weight: 400;
        max-width: 600px;
        margin: 0 auto;
        line-height: 1.6;
    }
    
    /* ===== CONFIG CARD ===== */
    .config-card {
        background: var(--bg-card);
        border: 1px solid var(--border-light);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: var(--shadow-md);
    }
    
    .config-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 1.5rem;
    }
    
    .config-item {
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
    }
    
    .config-label {
        font-size: 0.7rem;
        font-weight: 600;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    
    .config-value {
        font-size: 0.95rem;
        font-weight: 600;
        color: var(--text-primary);
    }
    
    .config-value-highlight {
        color: var(--bio-emerald);
    }
    
    /* ===== STAGE CARDS ===== */
    .stage-card {
        background: var(--bg-card);
        border: 1px solid var(--border-light);
        border-radius: 20px;
        padding: 2rem;
        margin: 1.5rem 0;
        box-shadow: var(--shadow-md);
        position: relative;
        overflow: hidden;
        transition: all 0.3s ease;
    }
    
    .stage-card:hover {
        box-shadow: var(--shadow-lg);
        border-color: var(--border-medium);
    }
    
    .stage-card-active {
        border-color: var(--bio-emerald);
        box-shadow: var(--shadow-glow);
    }
    
    .stage-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1.5rem;
    }
    
    .stage-info {
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    
    .stage-icon {
        width: 52px;
        height: 52px;
        border-radius: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        background: linear-gradient(135deg, var(--bg-accent), #fff);
        border: 1px solid var(--border-light);
        box-shadow: var(--shadow-sm);
    }
    
    .stage-icon-emerald { background: linear-gradient(135deg, rgba(5, 150, 105, 0.1), rgba(5, 150, 105, 0.05)); border-color: rgba(5, 150, 105, 0.2); }
    .stage-icon-teal { background: linear-gradient(135deg, rgba(13, 148, 136, 0.1), rgba(13, 148, 136, 0.05)); border-color: rgba(13, 148, 136, 0.2); }
    .stage-icon-cyan { background: linear-gradient(135deg, rgba(6, 182, 212, 0.1), rgba(6, 182, 212, 0.05)); border-color: rgba(6, 182, 212, 0.2); }
    .stage-icon-purple { background: linear-gradient(135deg, rgba(124, 58, 237, 0.1), rgba(124, 58, 237, 0.05)); border-color: rgba(124, 58, 237, 0.2); }
    .stage-icon-amber { background: linear-gradient(135deg, rgba(245, 158, 11, 0.1), rgba(245, 158, 11, 0.05)); border-color: rgba(245, 158, 11, 0.2); }
    
    .stage-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: var(--text-primary);
        margin: 0;
    }
    
    .stage-description {
        font-size: 0.875rem;
        color: var(--text-muted);
        margin: 0.25rem 0 0 0;
    }
    
    /* ===== STATUS BADGES ===== */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.4rem 0.875rem;
        border-radius: 100px;
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .status-pending {
        background: var(--bg-accent);
        color: var(--text-muted);
        border: 1px solid var(--border-light);
    }
    
    .status-running {
        background: linear-gradient(135deg, rgba(6, 182, 212, 0.1), rgba(6, 182, 212, 0.05));
        color: var(--bio-cyan);
        border: 1px solid rgba(6, 182, 212, 0.3);
        animation: pulse-border 2s ease-in-out infinite;
    }
    
    .status-success {
        background: linear-gradient(135deg, rgba(5, 150, 105, 0.1), rgba(5, 150, 105, 0.05));
        color: var(--bio-emerald);
        border: 1px solid rgba(5, 150, 105, 0.3);
    }
    
    .status-error {
        background: linear-gradient(135deg, rgba(220, 38, 38, 0.1), rgba(220, 38, 38, 0.05));
        color: var(--status-error);
        border: 1px solid rgba(220, 38, 38, 0.3);
    }
    
    @keyframes pulse-border {
        0%, 100% { border-color: rgba(6, 182, 212, 0.3); }
        50% { border-color: rgba(6, 182, 212, 0.6); }
    }
    
    /* ===== OUTPUT CONTENT ===== */
    .output-section {
        background: var(--bg-accent);
        border-radius: 12px;
        padding: 1.25rem;
        margin-top: 1rem;
    }
    
    .output-label {
        font-size: 0.7rem;
        font-weight: 600;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 0.75rem;
    }
    
    .path-card {
        background: white;
        border: 1px solid var(--border-light);
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 0.75rem;
    }
    
    .path-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 0.5rem;
    }
    
    .path-icon {
        color: var(--bio-emerald);
        font-weight: 600;
    }
    
    .confidence-badge {
        padding: 0.25rem 0.5rem;
        border-radius: 6px;
        font-size: 0.7rem;
        font-weight: 600;
    }
    
    .confidence-high { background: rgba(5, 150, 105, 0.1); color: var(--bio-emerald); }
    .confidence-medium { background: rgba(245, 158, 11, 0.1); color: var(--accent-amber); }
    .confidence-low { background: rgba(220, 38, 38, 0.1); color: var(--status-error); }
    
    /* ===== CHIPS/TAGS ===== */
    .chip {
        display: inline-flex;
        align-items: center;
        padding: 0.35rem 0.75rem;
        background: white;
        border: 1px solid var(--border-light);
        border-radius: 100px;
        font-size: 0.8rem;
        font-weight: 500;
        color: var(--text-secondary);
        margin: 0.25rem;
        transition: all 0.2s ease;
    }
    
    .chip:hover {
        border-color: var(--bio-emerald);
        color: var(--bio-emerald);
    }
    
    .chip-emerald {
        background: rgba(5, 150, 105, 0.08);
        border-color: rgba(5, 150, 105, 0.2);
        color: var(--bio-emerald);
    }
    
    .chip-teal {
        background: rgba(13, 148, 136, 0.08);
        border-color: rgba(13, 148, 136, 0.2);
        color: var(--bio-teal);
    }
    
    /* ===== HYPOTHESIS CARD ===== */
    .hypothesis-card {
        background: linear-gradient(135deg, rgba(5, 150, 105, 0.04), rgba(6, 182, 212, 0.04));
        border: 1px solid rgba(5, 150, 105, 0.15);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    .hypothesis-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .hypothesis-statement {
        font-size: 1rem;
        color: var(--text-secondary);
        line-height: 1.7;
        font-style: italic;
    }
    
    /* ===== SCORE BARS ===== */
    .score-row {
        display: flex;
        align-items: center;
        gap: 1rem;
        margin-bottom: 0.75rem;
    }
    
    .score-label {
        flex: 0 0 120px;
        font-size: 0.85rem;
        color: var(--text-secondary);
    }
    
    .score-bar-bg {
        flex: 1;
        height: 8px;
        background: var(--bg-accent);
        border-radius: 100px;
        overflow: hidden;
    }
    
    .score-bar-fill {
        height: 100%;
        border-radius: 100px;
        transition: width 0.5s ease;
    }
    
    .score-bar-emerald { background: linear-gradient(90deg, var(--bio-emerald), var(--bio-teal)); }
    .score-bar-amber { background: linear-gradient(90deg, var(--accent-amber), #fbbf24); }
    .score-bar-rose { background: linear-gradient(90deg, var(--accent-rose), #f43f5e); }
    
    .score-value {
        flex: 0 0 50px;
        font-size: 0.85rem;
        font-weight: 600;
        color: var(--text-primary);
        text-align: right;
    }
    
    /* ===== DECISION CARD ===== */
    .decision-card {
        text-align: center;
        padding: 2.5rem;
        border-radius: 20px;
        margin: 2rem 0;
    }
    
    .decision-approve {
        background: linear-gradient(135deg, rgba(5, 150, 105, 0.08), rgba(16, 185, 129, 0.04));
        border: 2px solid rgba(5, 150, 105, 0.25);
    }
    
    .decision-revise {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.08), rgba(251, 191, 36, 0.04));
        border: 2px solid rgba(245, 158, 11, 0.25);
    }
    
    .decision-reject {
        background: linear-gradient(135deg, rgba(220, 38, 38, 0.08), rgba(248, 113, 113, 0.04));
        border: 2px solid rgba(220, 38, 38, 0.25);
    }
    
    .decision-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
    }
    
    .decision-label {
        font-size: 1.75rem;
        font-weight: 800;
        letter-spacing: -0.02em;
    }
    
    .decision-approve .decision-label { color: var(--bio-emerald); }
    .decision-revise .decision-label { color: var(--accent-amber); }
    .decision-reject .decision-label { color: var(--status-error); }
    
    /* ===== METRICS ROW ===== */
    .metrics-row {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1rem;
        margin-top: 1.5rem;
    }
    
    .metric-card {
        background: white;
        border: 1px solid var(--border-light);
        border-radius: 12px;
        padding: 1.25rem;
        text-align: center;
    }
    
    .metric-value {
        font-size: 1.75rem;
        font-weight: 800;
        background: linear-gradient(135deg, var(--bio-emerald), var(--bio-teal));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        line-height: 1.2;
    }
    
    .metric-label {
        font-size: 0.7rem;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-top: 0.5rem;
    }
    
    /* ===== HITL CHECKPOINT ===== */
    .hitl-card {
        background: linear-gradient(135deg, rgba(124, 58, 237, 0.05), rgba(139, 92, 246, 0.02));
        border: 1px solid rgba(124, 58, 237, 0.2);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1.5rem 0;
    }
    
    .hitl-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 1rem;
    }
    
    .hitl-icon {
        font-size: 1.25rem;
    }
    
    .hitl-title {
        font-size: 1rem;
        font-weight: 700;
        color: var(--accent-purple);
    }
    
    .hitl-subtitle {
        font-size: 0.85rem;
        color: var(--text-muted);
    }
    
    /* ===== BUTTONS ===== */
    .stButton > button {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-medium) !important;
        color: var(--text-primary) !important;
        border-radius: 10px !important;
        padding: 0.625rem 1.25rem !important;
        font-weight: 600 !important;
        font-size: 0.875rem !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        transition: all 0.2s ease !important;
    }
    
    .stButton > button:hover {
        background: var(--bg-accent) !important;
        border-color: var(--bio-emerald) !important;
        color: var(--bio-emerald) !important;
    }
    
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--bio-emerald), var(--bio-teal)) !important;
        border: none !important;
        color: white !important;
        box-shadow: 0 4px 14px rgba(5, 150, 105, 0.25) !important;
    }
    
    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 6px 20px rgba(5, 150, 105, 0.35) !important;
        transform: translateY(-1px) !important;
    }
    
    /* ===== FORM ELEMENTS ===== */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-light) !important;
        border-radius: 10px !important;
        color: var(--text-primary) !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        padding: 0.75rem 1rem !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--bio-emerald) !important;
        box-shadow: 0 0 0 3px rgba(5, 150, 105, 0.1) !important;
    }
    
    .stSelectbox > div > div {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-light) !important;
        border-radius: 10px !important;
    }
    
    /* Checkbox styling */
    .stCheckbox > label > span {
        color: var(--text-secondary) !important;
    }
    
    /* ===== SIDEBAR ===== */
    [data-testid="stSidebar"] {
        background: white !important;
        border-right: 1px solid var(--border-light) !important;
    }
    
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: var(--text-primary) !important;
    }
    
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label {
        color: var(--text-secondary) !important;
    }
    
    /* ===== EXPANDERS ===== */
    .streamlit-expanderHeader {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-light) !important;
        border-radius: 10px !important;
        color: var(--text-primary) !important;
        font-weight: 600 !important;
    }
    
    .streamlit-expanderContent {
        background: var(--bg-accent) !important;
        border: 1px solid var(--border-light) !important;
        border-top: none !important;
        border-radius: 0 0 10px 10px !important;
    }
    
    /* ===== ALERTS ===== */
    .stAlert {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-light) !important;
        border-radius: 10px !important;
    }
    
    /* ===== DIVIDER ===== */
    hr {
        border: none !important;
        height: 1px !important;
        background: var(--border-light) !important;
        margin: 2rem 0 !important;
    }
    
    /* ===== DOWNLOAD BUTTON ===== */
    .stDownloadButton > button {
        background: linear-gradient(135deg, rgba(5, 150, 105, 0.1), rgba(5, 150, 105, 0.05)) !important;
        border: 1px solid rgba(5, 150, 105, 0.3) !important;
        color: var(--bio-emerald) !important;
    }
    
    /* ===== LOADING SPINNER ===== */
    .loading-container {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 1rem;
        padding: 2rem;
    }
    
    .loading-spinner {
        width: 32px;
        height: 32px;
        border: 3px solid var(--bg-accent);
        border-top-color: var(--bio-emerald);
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
    
    .loading-text {
        color: var(--text-muted);
        font-size: 0.9rem;
    }
    
    /* ===== PIPELINE INDICATOR ===== */
    .pipeline-container {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        margin-bottom: 2rem;
        flex-wrap: wrap;
    }
    
    .pipeline-step {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .pipeline-badge {
        padding: 0.5rem 1rem;
        background: white;
        border: 1px solid var(--border-light);
        border-radius: 100px;
        font-size: 0.8rem;
        font-weight: 500;
        color: var(--text-secondary);
    }
    
    .pipeline-badge-active {
        background: linear-gradient(135deg, rgba(5, 150, 105, 0.1), rgba(5, 150, 105, 0.05));
        border-color: rgba(5, 150, 105, 0.3);
        color: var(--bio-emerald);
    }
    
    .pipeline-arrow {
        color: var(--border-medium);
        font-size: 0.8rem;
    }
    
    /* ===== EMPTY STATE ===== */
    .empty-state {
        text-align: center;
        padding: 4rem 2rem;
        background: white;
        border: 2px dashed var(--border-light);
        border-radius: 20px;
    }
    
    .empty-state-icon {
        font-size: 3.5rem;
        margin-bottom: 1rem;
        opacity: 0.7;
    }
    
    .empty-state-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 0.5rem;
    }
    
    .empty-state-text {
        font-size: 0.95rem;
        color: var(--text-muted);
    }
    
    /* Expander styling - black text */
    .streamlit-expanderHeader {
        color: #1a2f23 !important;
        font-weight: 500 !important;
    }
    .streamlit-expanderHeader p {
        color: #1a2f23 !important;
    }
    [data-testid="stExpander"] summary {
        color: #1a2f23 !important;
    }
    [data-testid="stExpander"] summary span {
        color: #1a2f23 !important;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# IMPORTS
# ============================================================================

import sys
sys.path.insert(0, str(Path(__file__).parent))

try:
    from src.agents import (
        PlannerAgent,
        OntologistAgent, 
        ScientistAgent,
        Scientist2Agent,
        CriticAgent
    )
    from src.orchestration.checkpoints import CheckpointStage, CheckpointStatus
    AGENTS_AVAILABLE = True
except ImportError as e:
    AGENTS_AVAILABLE = False
    IMPORT_ERROR = str(e)


# ============================================================================
# CONSTANTS
# ============================================================================

class WorkflowStage(Enum):
    PLANNER = "planner"
    ONTOLOGIST = "ontologist"
    SCIENTIST = "scientist"
    SCIENTIST2 = "scientist2"
    CRITIC = "critic"


STAGE_CONFIG = {
    WorkflowStage.PLANNER: {
        "title": "Planner",
        "full_title": "Knowledge Graph Planner",
        "description": "Extracts relevant pathways from the biological knowledge graph",
        "icon": "🗺️",
        "icon_class": "stage-icon-emerald"
    },
    WorkflowStage.ONTOLOGIST: {
        "title": "Ontologist",
        "full_title": "Semantic Ontologist",
        "description": "Interprets concepts with biological context and definitions",
        "icon": "📖",
        "icon_class": "stage-icon-teal"
    },
    WorkflowStage.SCIENTIST: {
        "title": "Scientist",
        "full_title": "Hypothesis Generator",
        "description": "Creates initial scientific hypothesis using 7-point framework",
        "icon": "🔬",
        "icon_class": "stage-icon-cyan"
    },
    WorkflowStage.SCIENTIST2: {
        "title": "Scientist²",
        "full_title": "Hypothesis Expander",
        "description": "Adds quantitative predictions and experimental protocols",
        "icon": "⚗️",
        "icon_class": "stage-icon-purple"
    },
    WorkflowStage.CRITIC: {
        "title": "Critic",
        "full_title": "Scientific Evaluator",
        "description": "Critically evaluates hypothesis quality and feasibility",
        "icon": "🎯",
        "icon_class": "stage-icon-amber"
    }
}


# ============================================================================
# FORMATTERS
# ============================================================================

def format_planner_output(output: dict) -> str:
    """Format planner output."""
    if "error" in output:
        return f'<div style="color: #dc2626;">❌ {output["error"]}</div>'
    
    subgraph = output.get("subgraph", {})
    path = subgraph.get("path", {})
    nodes = subgraph.get("nodes", [])
    edges = subgraph.get("edges", [])
    
    html = []
    
    if path:
        conf = _safe_number(path.get('total_strength', 0))
        conf_class = "confidence-high" if conf > 0.7 else "confidence-medium" if conf > 0.4 else "confidence-low"
        source = str(path.get('source', '?'))
        target = str(path.get('target', '?'))
        path_string = str(path.get('path_string', ''))
        html.append(f'<div class="path-card"><div class="path-header"><span class="path-icon">📍</span><strong>Path Discovered</strong><span class="confidence-badge {conf_class}">{conf:.0%} confidence</span></div><div style="font-family: monospace; font-size: 0.9rem; color: #1a2f23;">{source} → {target}</div><div style="color: #64748b; font-size: 0.8rem; margin-top: 0.5rem;">{path_string}</div></div>')
    
    if nodes:
        chip_items = []
        for n in nodes[:8]:
            label = str(n.get("label", n.get("id", "?")))
            chip_items.append(f'<span class="chip chip-emerald">{label}</span>')
        chips = ''.join(chip_items)
        html.append(f'<div style="margin-top: 1rem;"><div class="output-label">Biological Entities ({len(nodes)})</div><div>{chips}</div></div>')
    
    if edges:
        edge_items = []
        for e in edges[:5]:
            source = e.get('source', '?')
            target = e.get('target', '?')
            label = e.get('label', '?')
            edge_items.append(f'<div style="padding: 0.5rem 0; border-bottom: 1px solid #e5ebe8; display: flex; align-items: center; gap: 0.5rem; font-size: 0.85rem;"><span style="color: #1a2f23; font-weight: 500;">{source}</span><span style="color: #64748b;"> — </span><span style="color: #0d9488;">[{label}]</span><span style="color: #64748b;"> → </span><span style="color: #1a2f23; font-weight: 500;">{target}</span></div>')
        edge_html = ''.join(edge_items)
        html.append(f'<div style="margin-top: 1rem;"><div class="output-label">Relationships ({len(edges)})</div>{edge_html}</div>')
    
    return ''.join(html) if html else '<div style="color: #64748b;">No pathway data extracted</div>'


def format_ontologist_output(output: dict) -> str:
    """Format ontologist output."""
    if "error" in output:
        return f'<div style="color: #dc2626;">❌ {output["error"]}</div>'
    
    html = []
    
    definitions = output.get("concept_definitions", [])
    if definitions:
        defs_items = []
        for d in definitions[:4]:
            label = d.get('concept_label', d.get('concept_id', 'Unknown'))
            definition = str(d.get('definition', ''))[:180]
            defs_items.append(f'<div style="background: white; border-left: 3px solid #0d9488; padding: 1rem; margin-bottom: 0.75rem; border-radius: 0 8px 8px 0;"><div style="font-weight: 600; color: #1a2f23; margin-bottom: 0.25rem;">{label}</div><div style="color: #64748b; font-size: 0.9rem;">{definition}...</div></div>')
        defs_html = ''.join(defs_items)
        html.append(f'<div class="output-label">Concept Definitions</div>{defs_html}')
    
    narrative = output.get("narrative_synthesis", {})
    if narrative:
        overview = narrative.get('overview', '') if isinstance(narrative, dict) else str(narrative)
        overview = str(overview)[:350]
        html.append(f'<div style="background: linear-gradient(135deg, rgba(13, 148, 136, 0.06), rgba(6, 182, 212, 0.04)); border: 1px solid rgba(13, 148, 136, 0.15); border-radius: 12px; padding: 1.25rem; margin-top: 1rem;"><div class="output-label" style="color: #0d9488;">Narrative Synthesis</div><div style="color: #475569; line-height: 1.7;">{overview}...</div></div>')
    
    return ''.join(html) if html else '<div style="color: #64748b;">No ontology data available</div>'


def _safe_number(value, default=0):
    """Safely convert value to number."""
    if isinstance(value, (int, float)):
        return value
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def format_scientist_output(output: dict) -> str:
    """Format scientist output."""
    if "error" in output:
        return f'<div style="color: #dc2626;">❌ {output["error"]}</div>'
    
    html = []
    
    hypothesis = output.get("hypothesis", {})
    if hypothesis:
        title = str(hypothesis.get('title', 'Scientific Hypothesis'))
        statement = str(hypothesis.get('statement', 'No statement provided'))
        html.append(f'<div class="hypothesis-card"><div class="hypothesis-title">💡 {title}</div><div class="hypothesis-statement">"{statement}"</div></div>')
    
    outcomes = output.get("expected_outcomes", {})
    if outcomes:
        secondary_items = outcomes.get("secondary", [])[:3]
        secondary_html = ''.join([f'<li style="margin-bottom: 0.25rem;">{str(s)}</li>' for s in secondary_items])
        primary = str(outcomes.get('primary', 'N/A'))
        html.append(f'<div style="margin-top: 1rem;"><div class="output-label">Expected Outcomes</div><div style="background: white; border: 1px solid #e5ebe8; border-radius: 10px; padding: 1rem;"><div style="color: #059669; font-weight: 600; font-size: 0.75rem; text-transform: uppercase; margin-bottom: 0.25rem;">Primary</div><div style="color: #1a2f23; margin-bottom: 0.75rem;">{primary}</div><ul style="color: #475569; padding-left: 1.25rem; margin: 0; font-size: 0.9rem;">{secondary_html}</ul></div></div>')
    
    novelty = output.get("novelty", {})
    if novelty:
        score = _safe_number(novelty.get('score', 0))
        bar_class = "score-bar-emerald" if score >= 7 else "score-bar-amber" if score >= 5 else "score-bar-rose"
        justification_raw = novelty.get('justification', '')
        justification = str(justification_raw)[:120] if justification_raw else ''
        html.append(f'<div style="margin-top: 1rem; background: white; border: 1px solid #e5ebe8; border-radius: 10px; padding: 1rem;"><div class="score-row"><span class="score-label">Novelty Score</span><div class="score-bar-bg"><div class="score-bar-fill {bar_class}" style="width: {score * 10}%;"></div></div><span class="score-value">{score}/10</span></div><div style="color: #64748b; font-size: 0.85rem; margin-top: 0.5rem;">{justification}...</div></div>')
    
    return ''.join(html) if html else '<div style="color: #64748b;">No hypothesis generated</div>'


def format_scientist2_output(output: dict) -> str:
    """Format scientist2 output."""
    if "error" in output:
        return f'<div style="color: #dc2626;">❌ {output["error"]}</div>'
    
    html = []
    
    expanded = output.get("expanded_hypothesis", {})
    if expanded:
        preds = expanded.get("quantitative_predictions", [])
        pred_items = []
        for p in preds[:3]:
            prediction = str(p.get('prediction', ''))
            expected = str(p.get('expected_value', ''))
            pred_items.append(f'<div style="display: flex; justify-content: space-between; padding: 0.6rem; background: #f8faf9; border-radius: 6px; margin-bottom: 0.5rem; font-size: 0.85rem;"><span style="color: #475569;">{prediction}</span><span style="color: #7c3aed; font-weight: 600; font-family: monospace;">{expected}</span></div>')
        preds_html = ''.join(pred_items)
        title = str(expanded.get('title', 'Expanded Hypothesis'))
        statement = str(expanded.get('statement', ''))[:200]
        html.append(f'<div class="hypothesis-card" style="border-color: rgba(124, 58, 237, 0.2); background: linear-gradient(135deg, rgba(124, 58, 237, 0.04), rgba(139, 92, 246, 0.02));"><div class="hypothesis-title" style="color: #7c3aed;">🔬 {title}</div><div class="hypothesis-statement" style="margin-bottom: 1rem;">"{statement}..."</div><div class="output-label">Quantitative Predictions</div>{preds_html}</div>')
    
    methods = output.get("methodologies", {})
    if methods:
        comp = methods.get("computational", [])
        if comp:
            chip_items = []
            for c in comp[:4]:
                method = str(c.get("method", "Unknown"))
                software = str(c.get("software", "N/A"))
                chip_items.append(f'<span class="chip">{method} ({software})</span>')
            chips = ''.join(chip_items)
            html.append(f'<div style="margin-top: 1rem;"><div class="output-label">Computational Methods</div><div>{chips}</div></div>')
    
    return ''.join(html) if html else '<div style="color: #64748b;">No expansion data</div>'


def format_critic_output(output: dict) -> str:
    """Format critic output."""
    if "error" in output:
        return f'<div style="color: #dc2626;">❌ {output["error"]}</div>'
    
    html = []
    
    decision = output.get("decision", "UNKNOWN")
    decision_config = {
        "APPROVE": ("✅", "decision-approve"),
        "REVISE": ("🔄", "decision-revise"),
        "REJECT": ("❌", "decision-reject")
    }
    icon, cls = decision_config.get(decision, ("❓", ""))
    
    # Handle summary - could be string or list
    summary_raw = output.get('summary', '')
    if isinstance(summary_raw, list):
        summary = ' '.join(str(s) for s in summary_raw)[:180]
    elif isinstance(summary_raw, str):
        summary = summary_raw[:180]
    else:
        summary = str(summary_raw)[:180]
    
    html.append(f'<div class="decision-card {cls}"><div class="decision-icon">{icon}</div><div class="decision-label">{decision}</div><div style="color: #64748b; margin-top: 1rem; max-width: 500px; margin-left: auto; margin-right: auto;">{summary}...</div></div>')
    
    scores = output.get("scores", {})
    # Ensure scores is a dict, not a list
    if isinstance(scores, list):
        scores = {f"criterion_{i}": s for i, s in enumerate(scores) if isinstance(s, dict)}
    
    if scores and isinstance(scores, dict):
        score_items = []
        for cat, data in list(scores.items())[:5]:
            if isinstance(data, dict) and "score" in data:
                val = _safe_number(data["score"])
                mx = _safe_number(data.get("max", 10), 10)
                pct = (val / mx) * 100 if mx > 0 else 0
                bar_class = "score-bar-emerald" if pct >= 70 else "score-bar-amber" if pct >= 50 else "score-bar-rose"
                cat_label = cat.replace('_', ' ').title()
                score_items.append(f'<div class="score-row"><span class="score-label">{cat_label}</span><div class="score-bar-bg"><div class="score-bar-fill {bar_class}" style="width: {pct}%;"></div></div><span class="score-value">{val}/{mx}</span></div>')
        if score_items:
            scores_html = ''.join(score_items)
            html.append(f'<div style="background: white; border: 1px solid #e5ebe8; border-radius: 12px; padding: 1.25rem; margin-top: 1rem;"><div class="output-label">Evaluation Scores</div>{scores_html}</div>')
    
    return ''.join(html) if html else '<div style="color: #64748b;">No evaluation data</div>'


FORMATTERS = {
    WorkflowStage.PLANNER: format_planner_output,
    WorkflowStage.ONTOLOGIST: format_ontologist_output,
    WorkflowStage.SCIENTIST: format_scientist_output,
    WorkflowStage.SCIENTIST2: format_scientist2_output,
    WorkflowStage.CRITIC: format_critic_output,
}


# ============================================================================
# STAGE RUNNER
# ============================================================================

async def run_stage(agent, state: dict, stage: WorkflowStage, container) -> dict:
    """Run a single workflow stage."""
    cfg = STAGE_CONFIG[stage]
    
    with container:
        st.markdown(f'''
        <div class="stage-card stage-card-active">
            <div class="stage-header">
                <div class="stage-info">
                    <div class="stage-icon {cfg['icon_class']}">{cfg['icon']}</div>
                    <div>
                        <h3 class="stage-title">{cfg['full_title']}</h3>
                        <p class="stage-description">{cfg['description']}</p>
                    </div>
                </div>
                <span class="status-badge status-running">⚡ Processing</span>
            </div>
        ''', unsafe_allow_html=True)
        
        output_placeholder = st.empty()
        output_placeholder.markdown('''
        <div class="loading-container">
            <div class="loading-spinner"></div>
            <span class="loading-text">Analyzing biological data...</span>
        </div>
        ''', unsafe_allow_html=True)
        
        try:
            result_obj = await agent.run(state)
            result = result_obj.output
            confidence = result_obj.confidence
            
            formatter = FORMATTERS.get(stage, lambda x: json.dumps(x, indent=2))
            formatted = formatter(result)
            
            output_placeholder.markdown(f'''
            <div class="output-section">
                {formatted}
            </div>
            ''', unsafe_allow_html=True)
            
            with st.expander("📄 View Raw Data", expanded=False):
                st.json(result)
            
            st.markdown(f'''
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-top: 1rem; padding: 0.75rem 1rem; background: rgba(5, 150, 105, 0.08); border: 1px solid rgba(5, 150, 105, 0.2); border-radius: 8px;">
                <span style="color: var(--bio-emerald);">✓</span>
                <span style="color: var(--text-secondary); font-size: 0.875rem;">Completed • Confidence: {confidence:.0%}</span>
            </div>
            </div>
            ''', unsafe_allow_html=True)
            
            return result
            
        except Exception as e:
            output_placeholder.markdown(f'''
            <div style="padding: 1rem; background: rgba(220, 38, 38, 0.08); border: 1px solid rgba(220, 38, 38, 0.2); border-radius: 10px; color: var(--status-error);">
                ❌ Error: {str(e)}
            </div>
            </div>
            ''', unsafe_allow_html=True)
            return {"error": str(e)}


# ============================================================================
# HITL CHECKPOINT
# ============================================================================

def render_hitl_checkpoint(stage: WorkflowStage, output: dict, key: str) -> tuple[str, Optional[dict]]:
    """Render HITL checkpoint."""
    cfg = STAGE_CONFIG[stage]
    
    st.markdown(f'''
    <div class="hitl-card">
        <div class="hitl-header">
            <span class="hitl-icon">🔬</span>
            <div>
                <div class="hitl-title">Human Review Checkpoint</div>
                <div class="hitl-subtitle">Review {cfg['title']} output before proceeding</div>
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("✅ Approve", key=f"{key}_approve", type="primary", use_container_width=True):
            return "approved", None
    with col2:
        if st.button("✏️ Modify", key=f"{key}_modify", use_container_width=True):
            return "modify", None
    with col3:
        if st.button("❌ Reject", key=f"{key}_reject", use_container_width=True):
            return "rejected", None
    
    with st.expander("Edit JSON", expanded=False):
        edited = st.text_area("JSON:", value=json.dumps(output, indent=2, default=str), height=250, key=f"{key}_edit", label_visibility="collapsed")
        if st.button("Apply", key=f"{key}_apply"):
            try:
                return "modified", json.loads(edited)
            except json.JSONDecodeError as e:
                st.error(f"Invalid JSON: {e}")
    
    return "pending", None


# ============================================================================
# MAIN WORKFLOW
# ============================================================================

async def run_workflow(config: dict):
    """Execute the full workflow."""
    
    if not AGENTS_AVAILABLE:
        st.error(f"Cannot run workflow: {IMPORT_ERROR}")
        return
    
    if "workflow_state" not in st.session_state:
        st.session_state.workflow_state = {}
    
    wf = st.session_state.workflow_state
    
    # Pipeline indicator
    stages = ["Planner"]
    if config["enable_ontologist"]: stages.append("Ontologist")
    stages.append("Scientist")
    if config["enable_scientist2"]: stages.append("Scientist²")
    stages.append("Critic")
    
    pipeline_html = ''.join([f'<span class="pipeline-badge">{s}</span><span class="pipeline-arrow">→</span>' for s in stages[:-1]])
    pipeline_html += f'<span class="pipeline-badge">{stages[-1]}</span>'
    st.markdown(f'<div class="pipeline-container">{pipeline_html}</div>', unsafe_allow_html=True)
    
    # Stage 1: Planner
    planner = PlannerAgent()
    planner_state = {
        "kg_path": config["kg_path"],
        "concept_a": config["concept_a"],
        "concept_b": config["concept_b"],
        "exploration_mode": "balanced",
        "max_paths": 3
    }
    
    planner_output = await run_stage(planner, planner_state, WorkflowStage.PLANNER, st.container())
    if "error" in planner_output:
        st.error("Planner failed. Workflow stopped.")
        return
    wf["planner_output"] = planner_output
    
    if config["hitl_enabled"] and "planner" in config["hitl_stages"]:
        decision, modified = render_hitl_checkpoint(WorkflowStage.PLANNER, planner_output, "planner_hitl")
        if decision == "rejected": return
        if decision == "modified" and modified: planner_output = modified
        if decision == "pending":
            st.info("⏸️ Awaiting review...")
            return
    
    # Stage 2: Ontologist
    ontologist_output = {}
    if config["enable_ontologist"]:
        ontologist = OntologistAgent()
        ont_state = {"planner_output": planner_output, "user_query": config["user_query"]}
        ontologist_output = await run_stage(ontologist, ont_state, WorkflowStage.ONTOLOGIST, st.container())
        wf["ontologist_output"] = ontologist_output
        
        if config["hitl_enabled"] and "ontologist" in config["hitl_stages"]:
            decision, modified = render_hitl_checkpoint(WorkflowStage.ONTOLOGIST, ontologist_output, "ont_hitl")
            if decision == "rejected": return
            if decision == "modified" and modified: ontologist_output = modified
            if decision == "pending":
                st.info("⏸️ Awaiting review...")
                return
    
    # Stage 3: Scientist
    scientist = ScientistAgent()
    sci_state = {"planner_output": planner_output, "user_query": config["user_query"]}
    scientist_output = await run_stage(scientist, sci_state, WorkflowStage.SCIENTIST, st.container())
    if "error" in scientist_output:
        st.error("Scientist failed. Workflow stopped.")
        return
    wf["scientist_output"] = scientist_output
    
    if config["hitl_enabled"] and "scientist" in config["hitl_stages"]:
        decision, modified = render_hitl_checkpoint(WorkflowStage.SCIENTIST, scientist_output, "sci_hitl")
        if decision == "rejected": return
        if decision == "modified" and modified: scientist_output = modified
        if decision == "pending":
            st.info("⏸️ Awaiting review...")
            return
    
    # Stage 4: Scientist2
    expanded = scientist_output
    if config["enable_scientist2"]:
        scientist2 = Scientist2Agent(enable_literature_search=config["enable_literature"])
        sci2_state = {
            "hypothesis": scientist_output,
            "planner_output": planner_output,
            "ontologist_output": ontologist_output,
            "user_query": config["user_query"]
        }
        scientist2_output = await run_stage(scientist2, sci2_state, WorkflowStage.SCIENTIST2, st.container())
        expanded = scientist2_output
        wf["scientist2_output"] = scientist2_output
        
        if config["hitl_enabled"] and "scientist2" in config["hitl_stages"]:
            decision, modified = render_hitl_checkpoint(WorkflowStage.SCIENTIST2, scientist2_output, "sci2_hitl")
            if decision == "rejected": return
            if decision == "modified" and modified: expanded = modified
            if decision == "pending":
                st.info("⏸️ Awaiting review...")
                return
    
    # Stage 5: Critic
    critic = CriticAgent()
    critic_state = {"hypothesis": expanded, "planner_output": planner_output, "iteration": 1}
    critic_output = await run_stage(critic, critic_state, WorkflowStage.CRITIC, st.container())
    wf["critic_output"] = critic_output
    
    if config["hitl_enabled"] and "critic" in config["hitl_stages"]:
        decision, modified = render_hitl_checkpoint(WorkflowStage.CRITIC, critic_output, "critic_hitl")
        if decision == "modified" and modified: critic_output = modified
    
    # Final Summary
    st.markdown("---")
    
    decision = critic_output.get("decision", "UNKNOWN")
    overall = critic_output.get("scores", {}).get("overall", {})
    score = overall.get("score", "N/A") if isinstance(overall, dict) else "N/A"
    n_stages = 3 + (1 if config["enable_ontologist"] else 0) + (1 if config["enable_scientist2"] else 0)
    
    st.markdown(f'''
    <div class="metrics-row">
        <div class="metric-card">
            <div class="metric-value">{decision}</div>
            <div class="metric-label">Final Decision</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{score}/10</div>
            <div class="metric-label">Overall Score</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{n_stages}</div>
            <div class="metric-label">Stages Completed</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Save workflow results to local JSON file for external service consumption
    output_dir = Path("data/workflow_outputs")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"workflow_result_{timestamp}.json"
    
    # Compile all agent outputs into a single JSON structure
    workflow_result = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "knowledge_graph": str(config["kg_path"]),
            "source_concept": config["concept_a"],
            "target_concept": config["concept_b"],
            "user_query": config["user_query"],
            "stages_completed": n_stages,
            "final_decision": decision
        },
        "outputs": {
            "planner": wf.get("planner_output", {}),
            "ontologist": wf.get("ontologist_output", {}),
            "scientist": wf.get("scientist_output", {}),
            "scientist2": wf.get("scientist2_output", {}),
            "critic": wf.get("critic_output", {})
        }
    }
    
    # Save to file
    with open(output_file, 'w') as f:
        json.dump(workflow_result, f, indent=2, default=str)
    
    st.success(f"✅ Results saved to: {output_file}")
    
    st.download_button(
        "📥 Download Results",
        data=json.dumps(workflow_result, indent=2, default=str),
        file_name=f"co_scientist_results_{timestamp}.json",
        mime="application/json",
        use_container_width=True
    )


# ============================================================================
# SIDEBAR
# ============================================================================

def render_sidebar() -> dict:
    """Render sidebar configuration."""
    
    st.sidebar.markdown('''
    <div style="text-align: center; padding: 1.5rem 0;">
        <div style="font-size: 2.25rem; margin-bottom: 0.5rem;">🧬</div>
        <div style="font-size: 1.25rem; font-weight: 700; color: var(--text-primary);">Co-Scientist</div>
        <div style="font-size: 0.7rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.15em;">Research Platform</div>
    </div>
    ''', unsafe_allow_html=True)
    
    st.sidebar.markdown("---")
    
    st.sidebar.markdown("##### 📊 Knowledge Graph")
    kg_dir = Path("data/knowledge_graphs")
    kg_files = list(kg_dir.glob("*.json")) if kg_dir.exists() else []
    # Filter out invalid KG files and prioritize test files
    valid_kg_files = [f for f in kg_files if f.name not in ["hemoglobin_kg.json"]]  # Exclude raw PDB data files
    kg_options = {f.name: str(f) for f in valid_kg_files}
    
    if kg_options:
        # Pre-select test_hemoglobin_kg.json or example_bio_kg.json if available
        default_options = ["test_hemoglobin_kg.json", "example_bio_kg.json"]
        default_idx = 0
        for i, opt in enumerate(kg_options.keys()):
            if opt in default_options:
                default_idx = i
                break
        selected_kg = st.sidebar.selectbox("Select", list(kg_options.keys()), index=default_idx, label_visibility="collapsed")
        kg_path = kg_options[selected_kg]
    else:
        kg_path = st.sidebar.text_input("Path", value="data/knowledge_graphs/test_hemoglobin_kg.json", label_visibility="collapsed")
    
    st.sidebar.markdown("##### 🔗 Concepts")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        concept_a = st.text_input("Source", value="hemoglobin_alpha", label_visibility="collapsed", placeholder="Source")
    with col2:
        concept_b = st.text_input("Target", value="low_temperature", label_visibility="collapsed", placeholder="Target")
    
    st.sidebar.markdown("##### ❓ Research Query")
    user_query = st.sidebar.text_area("Query", value="How does cold temperature affect hemoglobin oxygen binding in arctic fish?", height=80, label_visibility="collapsed")
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("##### ⚙️ Options")
    
    enable_ontologist = st.sidebar.checkbox("Ontologist Agent", value=True)
    enable_scientist2 = st.sidebar.checkbox("Scientist² Expander", value=True)
    enable_literature = st.sidebar.checkbox("Literature Search", value=False)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("##### 🔬 Human Review")
    
    hitl_enabled = st.sidebar.checkbox("Enable Checkpoints", value=False)
    hitl_stages = []
    if hitl_enabled:
        if st.sidebar.checkbox("After Planner", value=False): hitl_stages.append("planner")
        if st.sidebar.checkbox("After Ontologist", value=False): hitl_stages.append("ontologist")
        if st.sidebar.checkbox("After Scientist", value=True): hitl_stages.append("scientist")
        if st.sidebar.checkbox("After Scientist²", value=False): hitl_stages.append("scientist2")
        if st.sidebar.checkbox("After Critic", value=True): hitl_stages.append("critic")
    
    st.sidebar.markdown("---")
    st.sidebar.markdown('''
    <div style="text-align: center; padding: 0.5rem 0;">
        <div style="font-size: 0.65rem; color: var(--text-light);">Powered by SciAgents</div>
    </div>
    ''', unsafe_allow_html=True)
    
    return {
        "kg_path": kg_path,
        "concept_a": concept_a,
        "concept_b": concept_b,
        "user_query": user_query,
        "enable_ontologist": enable_ontologist,
        "enable_scientist2": enable_scientist2,
        "enable_literature": enable_literature,
        "hitl_enabled": hitl_enabled,
        "hitl_stages": hitl_stages
    }


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main application."""
    
    config = render_sidebar()
    
    # Hero
    st.markdown(f'''
    <div class="hero-container">
        <div class="hero-badge">
            <span>🔬</span>
            <span>AI-Powered Research</span>
        </div>
        <h1 class="hero-title">
            <span class="hero-title-accent">Scientific Discovery</span>
        </h1>
        <p class="hero-subtitle">
            Automated hypothesis generation through multi-agent collaboration on biological knowledge graphs
        </p>
    </div>
    ''', unsafe_allow_html=True)
    
    # Config card
    st.markdown(f'''
    <div class="config-card">
        <div class="config-grid">
            <div class="config-item">
                <span class="config-label">Knowledge Graph</span>
                <span class="config-value">{Path(config['kg_path']).stem}</span>
            </div>
            <div class="config-item">
                <span class="config-label">Connection</span>
                <span class="config-value">{config['concept_a']} <span class="config-value-highlight">→</span> {config['concept_b']}</span>
            </div>
            <div class="config-item">
                <span class="config-label">Query</span>
                <span class="config-value" style="font-size: 0.85rem;">{config['user_query'][:50]}...</span>
            </div>
            <div class="config-item">
                <span class="config-label">Human Review</span>
                <span class="config-value {'config-value-highlight' if config['hitl_enabled'] else ''}">{'Enabled' if config['hitl_enabled'] else 'Disabled'}</span>
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Action buttons
    col1, col2 = st.columns([3, 1])
    with col1:
        run_btn = st.button("🚀 Launch Discovery", type="primary", use_container_width=True)
    with col2:
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state.workflow_state = {}
            st.rerun()
    
    st.markdown("---")
    
    # Run
    if run_btn:
        st.session_state.workflow_state = {}
        asyncio.run(run_workflow(config))
    elif st.session_state.get("workflow_state"):
        st.info("📊 Previous results available. Click 'Launch Discovery' to run a new analysis.")
        with st.expander("View Previous Results", expanded=True):
            st.json(st.session_state.workflow_state)
    else:
        st.markdown('''
        <div class="empty-state">
            <div class="empty-state-icon">🧬</div>
            <div class="empty-state-title">Ready for Discovery</div>
            <div class="empty-state-text">Configure your parameters in the sidebar and click Launch Discovery to begin</div>
        </div>
        ''', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
