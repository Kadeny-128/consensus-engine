# Product Requirements: The Single-Threaded Reasoning Engine

## 1. Executive Summary

**Goal:** Build a "Deep Reasoning Engine" for Ultra-Rare Disease Drug Discovery (<10k patients).
**Core Philosophy:** Unlike mass-market drug discovery (which tests 10,000 random molecules), we cannot afford failures. We create **ONE** "Patient Zero" molecule and use recursive AI reasoning to perfect it.
**The Method:** A single linear gauntlet (L1 -> L10). The molecule only advances if it solves the specific chemical constraint of that loop.

## 2. Technical Architecture

- **Brain:** Cerebras Wafer-Scale Engine (Llama 3.1 70B). Used for "Chemical Reasoning" (Why did it fail? How do I fix it?).
- **Body:** Python + RDKit. Used for "Physics Verification" (Geometry, Valency, Lipinski Rules).
- **Control Flow:** Single-Threaded Recursion. No parallel fan-out.

## 3. The Logic Chain (The Gauntlet)

### Phase 1: The Spark

- **L1 (Hypothesis):** Input Target (FASTA) -> Output Patient Zero (SMILES).
  - _Guardrails:_ Druggability Check, Valency Sanitization, Synthetic Accessibility Score < 5.

### Phase 2: The Deep Loop (L2 - L8)

- **The Process:** Molecule faces a constraint (e.g., "Must cross Blood-Brain Barrier").
- **The Failure:** If it fails, the Reasoning Engine analyzes the structure.
- **The Fix:** The Engine mutates the molecule.
- **The Safety Anchor (CRITICAL):** If a mutation happens in L4+, the system **MUST RESET to L3 (Toxicity)** to re-verify safety. We never move forward with an unchecked mutation.

### Phase 3: The Validation

- **L9 (Stress Test):** Run the molecule against 10,000 Synthetic Patient profiles (Virtual Twins).
- **L10 (Dossier):** Generate the final regulatory report (PDF/Markdown).

## 4. UI/UX Specifications

- **Aesthetic:** "Google Dark" Mode (`#202124`). Font: Inter.
- **Layout:**
  - **Setup Mode:** Rigid input form (Target, Constraints).
  - **Journey Mode:** Visualizes the "Reasoning Trace" (e.g., "L4 Failed -> Mutated Group X -> Reset to L3").
- **Visuals:** RDKit 2D Molecule rendering.

## 5. Success Metrics

- **Reliability:** 0% Crash rate on "Impossible Molecules" (RDKit must catch them).
- **Safety:** No molecule reaches L10 without passing L3 (Toxicity) _after_ its last mutation.
