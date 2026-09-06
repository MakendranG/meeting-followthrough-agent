#!/usr/bin/env python3
"""
main.py — CLI entry point for the Meeting Follow-Through Agent
==============================================================

Runs the full end-to-end flow against the two sample transcripts:

  1. extract_action_items(Meeting 1)  -> store to memory/ as JSON
     (simulates persistent memory that survives between meetings)
  2. extract_action_items(Meeting 2)  -> Meeting 2's NEW action items
  3. check_followthrough(Meeting 1 items, Meeting 2 transcript)
     -> DONE / IN_PROGRESS / NOT_MENTIONED status per prior item
  4. draft_followup_message(...) for every NOT_MENTIONED (at-risk) item

It then prints:
  (a) Meeting 2's new action items (owners + deadlines)
  (b) a follow-through status table for Meeting 1's items
  (c) drafted polite follow-up messages for the at-risk items

This two-tool flow — extraction PLUS a cross-meeting follow-through check with
persistent memory — is what makes this more than a plain meeting summarizer.

Built With: Strands Agents SDK (Amazon Bedrock / Claude Sonnet 4).
No hardcoded secrets: AWS credentials are read from the environment.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap
from pathlib import Path
from typing import Dict, List

from agent import (
    check_followthrough,
    draft_followup_message,
    extract_action_items,
)

# Optional: load a local .env file if python-dotenv is installed. This is a
# developer convenience only; credentials still come from the environment.
try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover - dotenv is optional
    pass


BASE_DIR = Path(__file__).resolve().parent
SAMPLE_DIR = BASE_DIR / "sample_data"
MEMORY_DIR = BASE_DIR / "memory"

STATUS_ICON = {
    "DONE": "✅",
    "IN_PROGRESS": "🔄",
    "NOT_MENTIONED": "⚠️ ",
}


# ---------------------------------------------------------------------------
# Small presentation helpers
# ---------------------------------------------------------------------------
def _hr(char: str = "─", width: int = 78) -> str:
    return char * width


def _header(title: str) -> None:
    print("\n" + _hr("═"))
    print(f"  {title}")
    print(_hr("═"))


def _read_transcript(path: Path) -> str:
    if not path.exists():
        sys.exit(f"ERROR: transcript not found: {path}")
    return path.read_text(encoding="utf-8")


def _print_action_items(items: List[Dict[str, str]]) -> None:
    if not items:
        print("  (no action items found)")
        return
    for i, it in enumerate(items, 1):
        print(f"  {i}. {it['description']}")
        print(f"       Owner: {it['owner']:<12} Deadline: {it['deadline']}")


def _print_followthrough_table(rows: List[Dict[str, str]]) -> None:
    """Render the follow-through status table."""
    print(f"  {'OWNER':<10} {'STATUS':<16} ACTION ITEM")
    print(f"  {_hr('-', 74)}")
    for r in rows:
        icon = STATUS_ICON.get(r["status"], "  ")
        status_label = f"{icon} {r['status']}"
        desc = textwrap.shorten(r["description"], width=40, placeholder="…")
        print(f"  {r['owner']:<10} {status_label:<16} {desc}")
    print(f"  {_hr('-', 74)}")

    done = sum(1 for r in rows if r["status"] == "DONE")
    prog = sum(1 for r in rows if r["status"] == "IN_PROGRESS")
    risk = sum(1 for r in rows if r["status"] == "NOT_MENTIONED")
    print(
        f"  Summary: {done} done · {prog} in progress · {risk} at risk "
        f"(not mentioned)"
    )


# ---------------------------------------------------------------------------
# Main flow
# ---------------------------------------------------------------------------
def run(meeting1_path: Path, meeting2_path: Path) -> None:
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)

    meeting1_text = _read_transcript(meeting1_path)
    meeting2_text = _read_transcript(meeting2_path)

    # --- Step 1: extract Meeting 1's action items and persist them ---------
    _header("STEP 1  ·  Extracting action items from Meeting 1")
    print("  Running Tool A: extract_action_items(Meeting 1)…")
    meeting1_items = json.loads(extract_action_items(meeting1_text))
    _print_action_items(meeting1_items)

    memory_file = MEMORY_DIR / "meeting_1_action_items.json"
    memory_file.write_text(json.dumps(meeting1_items, indent=2), encoding="utf-8")
    print(f"\n  💾 Stored to persistent memory: {memory_file.relative_to(BASE_DIR)}")

    # --- Step 2: extract Meeting 2's NEW action items ----------------------
    _header("STEP 2  ·  Extracting NEW action items from Meeting 2")
    print("  Running Tool A: extract_action_items(Meeting 2)…")
    meeting2_items = json.loads(extract_action_items(meeting2_text))
    (MEMORY_DIR / "meeting_2_action_items.json").write_text(
        json.dumps(meeting2_items, indent=2), encoding="utf-8"
    )

    # --- Step 3: check follow-through of Meeting 1 items vs Meeting 2 ------
    _header("STEP 3  ·  Checking follow-through (Meeting 1 items vs Meeting 2)")
    print("  Loading Meeting 1 items from memory and running Tool B: "
          "check_followthrough…")
    stored_items = json.loads(memory_file.read_text(encoding="utf-8"))
    followthrough = json.loads(
        check_followthrough(json.dumps(stored_items), meeting2_text)
    )
    (MEMORY_DIR / "followthrough_report.json").write_text(
        json.dumps(followthrough, indent=2), encoding="utf-8"
    )

    # --- Step 4: draft follow-ups for at-risk (NOT_MENTIONED) items --------
    at_risk = [r for r in followthrough if r["status"] == "NOT_MENTIONED"]
    followup_messages: List[Dict[str, str]] = []
    if at_risk:
        _header("STEP 4  ·  Drafting follow-up messages for at-risk items")
        # Match each at-risk item back to its original deadline from memory.
        by_desc = {it["description"]: it for it in stored_items}
        for r in at_risk:
            original = by_desc.get(r["description"], {})
            item = {
                "owner": r["owner"],
                "description": r["description"],
                "deadline": original.get("deadline", "unspecified"),
            }
            print(f"  Drafting nudge for {r['owner']}…")
            message = draft_followup_message(item)
            followup_messages.append({"owner": r["owner"], "message": message})

    # =======================================================================
    # FINAL REPORT
    # =======================================================================
    _header("FINAL REPORT")

    print("\n(a) MEETING 2 — NEW ACTION ITEMS")
    print(_hr())
    _print_action_items(meeting2_items)

    print("\n(b) FOLLOW-THROUGH ON MEETING 1'S ACTION ITEMS")
    print(_hr())
    _print_followthrough_table(followthrough)

    print("\n(c) DRAFTED FOLLOW-UP MESSAGES FOR AT-RISK ITEMS")
    print(_hr())
    if not followup_messages:
        print("  🎉 Nothing at risk — every Meeting 1 item was addressed.")
    else:
        for fm in followup_messages:
            print(f"\n  ✉️  To {fm['owner']}:")
            for line in textwrap.wrap(fm["message"], width=72):
                print(f"      {line}")

    print("\n" + _hr("═"))
    print("  Done. Reports saved under ./memory/")
    print(_hr("═"))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Meeting Follow-Through Agent — extract action items and "
        "check cross-meeting follow-through (Built With: Strands Agents SDK)."
    )
    parser.add_argument(
        "--meeting1",
        default=str(SAMPLE_DIR / "meeting_1_transcript.txt"),
        help="Path to the earlier meeting transcript (default: sample_data).",
    )
    parser.add_argument(
        "--meeting2",
        default=str(SAMPLE_DIR / "meeting_2_transcript.txt"),
        help="Path to the later meeting transcript (default: sample_data).",
    )
    args = parser.parse_args()
    run(Path(args.meeting1), Path(args.meeting2))


if __name__ == "__main__":
    main()
