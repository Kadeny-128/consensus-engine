from __future__ import annotations

from utils.cerebras_client import CerebrasClient

_SYSTEM = (
    "You are a Lead Optimization Chemist. Given a drug candidate, propose a single optimized "
    "analog that addresses its weaknesses. Return valid JSON with keys: "
    "name, smiles, rationale, predicted_improvements."
)


async def synthesize_lead(candidates: list[dict], topic: str = "") -> dict | None:
    if not candidates:
        return None

    client = CerebrasClient()
    best = sorted(candidates, key=lambda c: c.get("total_score", 0), reverse=True)[0]

    designation = f"CB-{topic.split()[0].upper()}-001" if topic.strip() else "CB-LEAD-001"

    response = await client.generate(
        system_prompt=_SYSTEM,
        user_prompt=(
            f"Candidate: {best.get('name', 'Unknown')}\n"
            f"SMILES: {best.get('smiles', '?')}\n"
            f"Total Score: {best.get('total_score', 0)}\n"
            f"QED: {best.get('qed', 'N/A')}\n"
            "Modify this molecule to fix its flaws and improve druglikeness."
        ),
        model="llama3.3-70b",
        json_mode=True,
    )

    if response["status"] != "success":
        return None

    content = response["content"]
    if isinstance(content, dict):
        content["name"] = designation
        content["source_candidate"] = best.get("name")
        content["latency"] = response["latency"]
        return content

    return {"raw": content, "name": designation, "source_candidate": best.get("name"), "latency": response["latency"]}
