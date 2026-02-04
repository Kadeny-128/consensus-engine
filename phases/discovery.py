from __future__ import annotations

import asyncio
import json
import re
import time

from utils.cerebras_client import CerebrasClient
from utils.chemistry import analyze_smiles

SCAFFOLDS = [
    "Quinazoline", "Indole", "Macrocycle", "Benzimidazole", "Pyrimidine",
    "Thiazole", "Piperazine", "Oxadiazole", "Pyrrolidine", "Isoquinoline",
    "Triazine", "Chromone", "Dihydropyridine", "Morpholine", "Spirocyclic",
    "Bicyclic peptide",
]

_SYSTEM = (
    "You are a medicinal chemistry agent. Respond ONLY with valid JSON, no markdown. "
    "Generate 5 distinct drug-like molecules based on the given scaffold. "
    'Format: {"molecules": [{"name": "...", "smiles": "...", "rationale": "..."}, ...]}'
)


async def _agent_task(client: CerebrasClient, scaffold: str) -> list[dict]:
    response = await client.generate(
        system_prompt=_SYSTEM,
        user_prompt=f"Scaffold: {scaffold}. Propose 5 diverse molecules.",
        model="llama3.3-70b",
        json_mode=False,
    )
    if response["status"] != "success" or not response["content"]:
        return []

    text = response["content"]
    candidates = []
    for match in re.findall(r"\{[^{}]*\}", text):
        try:
            obj = json.loads(match)
            if "name" in obj and "smiles" in obj:
                obj["scaffold"] = scaffold
                obj["latency"] = response["latency"]
                candidates.append(obj)
        except json.JSONDecodeError:
            continue
    return candidates


_VALIDATE_SYSTEM = (
    "You are a Scientific Classifier. Your job is to determine if the user input is a valid molecular target. "
    "RULES:\n"
    "1. REJECT if the input is a Disease (e.g. Cancer, Diabetes, Malaria).\n"
    "2. REJECT if the input is a Biological Process or Generic Term (e.g. Apoptosis, Cell, DNA).\n"
    "3. ACCEPT if and ONLY if the input is a Specific Molecular Target (Protein, Gene, Receptor, Enzyme, or a named mutant like KRAS G12C).\n"
    'Respond ONLY with valid JSON: {"valid": true} or {"valid": false, "reason": "brief explanation"}'
)


async def validate_topic(topic: str) -> tuple[bool, str]:
    client = CerebrasClient()
    response = await client.generate(
        system_prompt=_VALIDATE_SYSTEM,
        user_prompt=topic,
        model="llama3.3-70b",
        json_mode=True,
    )
    if response["status"] != "success" or not response["content"]:
        return True, ""  # fail open on API error

    content = response["content"]
    if isinstance(content, dict):
        if content.get("valid") is False:
            return False, content.get("reason", "Input incompatible. Please specify a molecular target.")
        return True, ""

    return True, ""


async def generate_candidates(topic: str, num_agents: int = 16) -> list[dict]:
    client = CerebrasClient()
    scaffolds = SCAFFOLDS[:num_agents]

    wall_start = time.perf_counter()
    results = await asyncio.gather(*[_agent_task(client, s) for s in scaffolds])
    wall_time = round((time.perf_counter() - wall_start) * 1000, 1)

    candidates = [c for batch in results for c in batch]
    target_clean = topic.split()[0].upper() if topic.strip() else "LEAD"
    for i, c in enumerate(candidates):
        c["id"] = i
        c["name"] = f"CB-{target_clean}-C{i + 1:02d}"
        # Pre-generate image for each candidate
        analysis = analyze_smiles(c.get("smiles", ""))
        if analysis:
            c["image_b64"] = analysis["image_b64"]

    return candidates
