"""
Test suite: Phase 1 Discovery + Phase 2 Audit pipeline.
"""

import asyncio
import json

from utils.cerebras_client import CerebrasClient
from phases.discovery import run_discovery
from phases.audit import run_audit


async def test_pipeline(client: CerebrasClient):
    """Integration test: Phase 1 -> Phase 2."""
    topic = "SpaceX Starship timeline"

    print("=" * 50)
    print("PIPELINE TEST: DISCOVERY -> AUDIT")
    print("=" * 50)

    # Phase 1
    print(f"\n  Phase 1: Discovering '{topic}'...")
    discovery = await run_discovery(client, topic)
    d_count = len(discovery["agent_results"])
    print(f"  Discovery complete: {d_count}/10 agents | {discovery['wall_time']}ms")

    # Phase 2
    print(f"\n  Phase 2: Auditing discovery data...")
    audit = await run_audit(client, discovery)
    a_count = len(audit["audit_results"])
    print(f"  Audit complete: {a_count}/10 auditors | {audit['wall_time']}ms")

    # Summary
    total_wall = discovery["wall_time"] + audit["wall_time"]
    print(f"\n  --- PIPELINE SUMMARY ---")
    print(f"  Discovery Agents : {d_count}/10  | {discovery['wall_time']}ms")
    print(f"  Auditor Agents   : {a_count}/10  | {audit['wall_time']}ms")
    print(f"  Total Pipeline   : {total_wall}ms ({round(total_wall/1000, 2)}s)")
    print(f"  Total Agents     : {d_count + a_count}/20")

    # Audit samples
    print(f"\n  --- AUDIT SAMPLES ---")
    for a in audit["audit_results"]:
        preview = json.dumps(a["content"], indent=None)
        if len(preview) > 120:
            preview = preview[:120] + "..."
        print(f"  [{a['agent_id']}] {a['role']:16s} | {a['latency']}ms | {preview}")

    print()
    verdict = "PASS" if d_count >= 6 and a_count >= 6 else "FAIL"
    print(f"  VERDICT : {verdict}")
    print()


async def main():
    client = CerebrasClient()
    await test_pipeline(client)
    print("All tests complete.")


if __name__ == "__main__":
    asyncio.run(main())
