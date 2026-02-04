# Architecture: The Single-Threaded Reasoning Engine

**Project Goal:** Ultra-Rare Disease Drug Discovery (<10k patients).
**Core Philosophy:** Deep Reasoning over Parallel Evolution. "Patient Zero" must be perfect.

## 1. System Overview

The engine operates as a linear, recursive gauntlet. A single "Patient Zero" molecule travels through 10 logical loops (L1-L10).

- **The Brain:** Cerebras (Llama 3.1 70B via API) handles "Chemical Reasoning" (Why did it fail?) and "Mutation" (How to fix it?).
- **The Body:** Python + RDKit handles "Physics" (Geometry, Valency, Lipinski Rules).
- **The Safety Anchor:** The system enforces a strict **Backtracking Rule**. Any mutation triggers a reset to Loop 3 (Toxicity) to ensure safety is never compromised.

## 2. Core Components

### A. Mission Control (The Input)

- **File:** `campaign.py`
- **Responsibility:** Captures the "Rules of Engagement."
- **Data:** Disease Name, Target FASTA, Constraints (BBB, Route, Toxicity Threshold).
- **Guardrails:** Validates input data (e.g., checks for invalid amino acids in FASTA).

### B. The Reasoning Engine (The Controller)

- **File:** `state_engine.py`
- **Class:** `ReasoningEngine`
- **Responsibility:** Manages the lifecycle of `MoleculeState`.
- **Logic:**
  - `start_campaign()`: Calls L1 to generate Patient Zero.
  - `run()`: Iterates through loops L2 -> L10.
  - `_evaluate_gate()`: Checks pass/fail criteria for current loop.
  - `_trigger_reasoning()`: Calls AI to analyze failure and mutate structure.
  - **The Backtrack Rule:** If L4+ fails -> Mutate -> Reset `current_loop` to `L3`.

### C. The Agents (The Intelligence)

- **File:** `agents.py`
- **Class:** `HypothesisAgent` (L1)
  - **Task:** Generates the initial molecule.
  - **Guardrails:** Valency Check (RDKit Sanitization), Synthetic Accessibility (SA Score < 5), Druggability Check.
- **Class:** `ReasoningAgent` (L2-L9)
  - **Task:** Diagnoses failures and suggests chemical modifications (Add/Remove/Swap groups).

### D. The Dashboard (The Interface)

- **File:** `dashboard.py`
- **Style:** Google Dark Theme (`#202124`), Inter Font.
- **States:**
  1. **Setup Mode:** Form to create a Campaign.
  2. **Journey Mode:** Visualizes the molecule, the current loop, and the "Reasoning Trace" (History of mutations).

## 3. Data Flow (The Deep Loop)

1. **User Input:** Campaign Constraints defined.
2. **L1 (Spark):** `HypothesisAgent` -> `Patient Zero` (MoleculeState initialized).
3. **L2 (Physics):** RDKit Geometry Check.
   - _Fail?_ -> AI Fix -> Retry L2.
4. **L3 (Safety Anchor):** Toxicity Scan.
   - _Fail?_ -> AI Fix -> Retry L3.
5. **L4 - L8 (Optimization):** Binding, Solubility, BBB Permeability.
   - _Fail?_ -> AI Fix -> **RESET TO L3**.
6. **L9 (Validation):** Synthetic Data Stress Test (10k Virtual Twins).
7. **L10 (Dossier):** Final Report Generation.

## 4. Directory Structure

## 5. Technology Stack

- **Frontend:** Streamlit (Custom CSS)
- **Chemistry Engine:** RDKit
- **Inference:** Cerebras (Llama 3.1 70B)
- **Language:** Python 3.10+
