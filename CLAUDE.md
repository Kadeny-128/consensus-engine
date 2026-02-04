# CLAUDE.md - Project Guidelines

## Project Context

We are building a **Single-Threaded Reasoning Engine** for Drug Discovery.
**Do Not:** Suggest parallel agents, "swarm" logic, or async fan-out.
**Do:** Focus on recursive loops, strict state management, and chemical validity.

## Tech Stack

- **Python:** 3.10+
- **Chemistry:** `rdkit` (Strict usage for valid sanitization).
- **Frontend:** Streamlit (Custom CSS for Google Dark theme).
- **Inference:** `cerebras_cloud_sdk` (Llama 3.1 70B).

## Aesthetic Rules

- **Theme:** Google Dark (`#202124` background, `#E8EAED` text).
- **Font:** Inter / Sans-serif.
- **Tone:** Technical, precise, no fluff. "System Active" style.

## Coding Standards (The "Rare Disease" Protocol)

1.  **Safety First:** If logic touches L4-L9, you MUST implement the "Fallback to L3" logic.
2.  **Mocking:** When I ask for "Skeleton" code, use placeholders for the heavy chemistry but **keep the logic real**.
3.  **Validation:** Every chunk must end with a `test_chunkX.py` script.
4.  **No Hallucinations:** Always wrap RDKit calls in `try/except` blocks to catch invalid physics.
