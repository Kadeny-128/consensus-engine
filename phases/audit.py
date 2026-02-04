from __future__ import annotations

import asyncio
import json
import re
import time

from utils.cerebras_client import CerebrasClient

_SYSTEM = (
    "You are a pharmaceutical reviewer. Respond ONLY with valid JSON, no markdown. "
    "For each molecule listed, assign a soft_score from 0 to 50 based on predicted toxicity risk "
    "and synthesis feasibility (50 = excellent, 0 = poor). Decimals are allowed (e.g., 37.5). "
    'Format: {"scores": [{"id": <int>, "soft_score": <number>, "reasoning": "..."}, ...]}'
)


def _format_batch(batch: list[dict]) -> str:
    lines = []
    for mol in batch:
        lines.append(
            f"ID={mol['id']}, Name={mol.get('name','?')}, SMILES={mol.get('smiles','?')}"
        )
    return "\n".join(lines)


async def _audit_batch(client: CerebrasClient, batch: list[dict]) -> dict:
    listing = _format_batch(batch)
    response = await client.generate(
        system_prompt=_SYSTEM,
        user_prompt=f"Review these molecules:\n{listing}",
        model="llama3.3-70b",
        json_mode=False,
    )
    scores: dict[int, float] = {}
    if response["status"] == "success" and response["content"]:
        for match in re.findall(r"\{[^{}]*\}", response["content"]):
            try:
                obj = json.loads(match)
                if "id" in obj and "soft_score" in obj:
                    scores[int(obj["id"])] = float(obj["soft_score"])
            except (json.JSONDecodeError, ValueError):
                continue
    return scores


async def audit_candidates(candidates: list[dict]) -> list[dict]:
    client = CerebrasClient()

    # Hard cap: top 30 by qed
    sorted_cands = sorted(candidates, key=lambda c: c.get("qed", 0), reverse=True)[:30]

    # Batches of 5
    batches = [sorted_cands[i:i + 5] for i in range(0, len(sorted_cands), 5)]

    wall_start = time.perf_counter()
    results = await asyncio.gather(*[_audit_batch(client, b) for b in batches])
    wall_time = round((time.perf_counter() - wall_start) * 1000, 1)

    # Merge scores
    all_scores: dict[int, float] = {}
    for score_map in results:
        all_scores.update(score_map)

    for mol in sorted_cands:
        try:
            hard_score = float(mol.get("hard_score", 0))
        except (TypeError, ValueError):
            hard_score = 0.0
        try:
            soft_score = float(all_scores.get(mol["id"], 20))
        except (TypeError, ValueError):
            soft_score = 0.0
        mol["soft_score"] = round(soft_score, 1)
        mol["total_score"] = round(hard_score + soft_score, 1)

    # Sort descending by total_score (highest first)
    sorted_cands.sort(key=lambda m: float(m.get("total_score", 0)), reverse=True)

    return sorted_cands
