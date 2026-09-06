#!/usr/bin/env python3
"""
generate_demo_result.py — regenerate the cached demo result
===========================================================

Runs the real two-tool Strands flow (Amazon Bedrock) against the bundled sample
transcripts and writes the structured output to `sample_data/demo_result.json`.

That JSON powers the **keyless Demo mode** of the Streamlit app (`app.py`): the
public deploy can show genuine agent output without any AWS credentials, cost,
or abuse risk, because it just loads this file instead of calling Bedrock.

Run it (with AWS Bedrock creds configured) whenever you change the transcripts:

    AWS_REGION=us-east-1 python scripts/generate_demo_result.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Allow running from the repo root: make the project importable.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agent import (  # noqa: E402
    check_followthrough,
    draft_followup_message,
    extract_action_items,
)

SAMPLE_DIR = ROOT / "sample_data"


def main() -> None:
    m1 = (SAMPLE_DIR / "meeting_1_transcript.txt").read_text(encoding="utf-8")
    m2 = (SAMPLE_DIR / "meeting_2_transcript.txt").read_text(encoding="utf-8")

    print("Tool A · extracting Meeting 1 action items…")
    m1_items = json.loads(extract_action_items(m1))
    print("Tool A · extracting Meeting 2 action items…")
    m2_items = json.loads(extract_action_items(m2))
    print("Tool B · checking follow-through…")
    followthrough = json.loads(check_followthrough(json.dumps(m1_items), m2))

    by_desc = {it["description"]: it for it in m1_items}
    followups = []
    for r in followthrough:
        if r["status"] == "NOT_MENTIONED":
            original = by_desc.get(r["description"], {})
            print(f"Drafting · nudge for {r['owner']}…")
            followups.append(
                {
                    "owner": r["owner"],
                    "message": draft_followup_message(
                        {
                            "owner": r["owner"],
                            "description": r["description"],
                            "deadline": original.get("deadline", "unspecified"),
                        }
                    ),
                }
            )

    result = {
        "_note": (
            "Real cached output from a live Amazon Bedrock (Claude Sonnet 4.5) run "
            "via the Strands agent. Used for the keyless public Demo mode. "
            "Regenerate with scripts/generate_demo_result.py."
        ),
        "meeting_1_action_items": m1_items,
        "meeting_2_action_items": m2_items,
        "followthrough": followthrough,
        "followups": followups,
    }
    out = SAMPLE_DIR / "demo_result.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Wrote {out} ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
