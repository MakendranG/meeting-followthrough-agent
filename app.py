"""
app.py — Streamlit web UI for the Meeting Follow-Through Agent
=============================================================

A browser front-end over the exact same two Strands tools used by the CLI
(`extract_action_items` and `check_followthrough`) plus the LLM
`draft_followup_message` helper — see agent.py. Nothing about the agent logic
changes here; this module only handles input widgets and rendering so a judge
can run the full flow live in a browser.

Run locally:
    streamlit run app.py

Requires Python 3.10+ and AWS Bedrock credentials in the environment (same as
the CLI). No secrets are stored in this file.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import streamlit as st
import pandas as pd

# Optional .env convenience (same as main.py).
try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover
    pass

# Reuse the SAME agent tools the CLI uses — the two-tool Strands design.
from agent import (
    check_followthrough,
    draft_followup_message,
    extract_action_items,
)

BASE_DIR = Path(__file__).resolve().parent
SAMPLE_DIR = BASE_DIR / "sample_data"

STATUS_BADGE = {
    "DONE": "✅ DONE",
    "IN_PROGRESS": "🔄 IN_PROGRESS",
    "NOT_MENTIONED": "⚠️ NOT_MENTIONED",
}

# Colors for the status pills / row highlights.
STATUS_STYLE = {
    "DONE": ("#0f5132", "#d1e7dd"),          # green
    "IN_PROGRESS": ("#664d03", "#fff3cd"),   # amber
    "NOT_MENTIONED": ("#842029", "#f8d7da"),  # red
}


def _load_sample(name: str) -> str:
    path = SAMPLE_DIR / name
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _pill(status: str) -> str:
    fg, bg = STATUS_STYLE.get(status, ("#333", "#eee"))
    label = STATUS_BADGE.get(status, status)
    return (
        f"<span style='background:{bg};color:{fg};padding:3px 10px;"
        f"border-radius:12px;font-weight:600;font-size:0.85rem;white-space:nowrap'>"
        f"{label}</span>"
    )


# ---------------------------------------------------------------------------
# Page setup + light custom styling
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Meeting Follow-Through Agent",
    page_icon="✅",
    layout="wide",
)

st.markdown(
    """
    <style>
      .hero {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        color: #fff; padding: 1.6rem 1.8rem; border-radius: 16px; margin-bottom: 1rem;
      }
      .hero h1 { color:#fff; margin:0 0 .3rem 0; font-size:1.9rem; }
      .hero p  { color:#e9e7ff; margin:0; font-size:1.02rem; }
      .badge-row span {
        display:inline-block; background:rgba(255,255,255,.18); color:#fff;
        padding:3px 10px; border-radius:20px; font-size:.8rem; margin-right:.4rem;
      }
      .nudge {
        border-left:4px solid #7c3aed; background:#faf9ff; padding:.8rem 1rem;
        border-radius:8px; margin-bottom:.7rem;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <h1>✅ Meeting Follow-Through Agent</h1>
      <p>The action item you agreed to last week? Nobody checked if it got done — until now.</p>
      <div class="badge-row" style="margin-top:.7rem">
        <span>Built With: Strands Agents SDK</span>
        <span>Amazon Bedrock</span>
        <span>Agents for Humans · Professional track</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    "This agent extracts commitments from one meeting, **remembers** them, then "
    "checks the *next* meeting's transcript to see which were done, which are in "
    "progress, and which quietly fell through — and drafts a polite nudge for the "
    "ones at risk. It's more than a summarizer: it has **memory and "
    "follow-through across meetings**."
)

with st.expander("How it works (two-tool Strands design)"):
    st.markdown(
        "- **Tool A — `extract_action_items`**: pulls structured action items "
        "(description, owner, deadline) from a transcript.\n"
        "- **Tool B — `check_followthrough`**: compares the *prior* meeting's "
        "items against the *current* transcript and tags each `DONE`, "
        "`IN_PROGRESS`, or `NOT_MENTIONED` (at risk).\n"
        "- **Drafting**: for every at-risk item, the LLM writes a follow-up "
        "message to the owner.\n\n"
        "Both tools use Amazon Bedrock (Claude Sonnet 4 family) for the "
        "language reasoning."
    )

# ---------------------------------------------------------------------------
# Inputs — two transcripts, prefilled with the bundled samples
# ---------------------------------------------------------------------------
col1, col2 = st.columns(2)
with col1:
    st.subheader("Meeting 1 (earlier)")
    meeting1 = st.text_area(
        "Paste the earlier meeting transcript",
        value=_load_sample("meeting_1_transcript.txt"),
        height=320,
        key="m1",
    )
with col2:
    st.subheader("Meeting 2 (later)")
    meeting2 = st.text_area(
        "Paste the later meeting transcript",
        value=_load_sample("meeting_2_transcript.txt"),
        height=320,
        key="m2",
    )

run = st.button("▶ Run the agent", type="primary", use_container_width=True)


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------
def _render_action_items(items: List[Dict[str, str]]) -> None:
    if not items:
        st.info("No action items found.")
        return
    df = pd.DataFrame(
        [
            {"#": i + 1, "Owner": it["owner"], "Deadline": it["deadline"], "Action item": it["description"]}
            for i, it in enumerate(items)
        ]
    ).set_index("#")
    st.dataframe(df, use_container_width=True)


def _render_followthrough(rows: List[Dict[str, str]]) -> None:
    done = sum(1 for r in rows if r["status"] == "DONE")
    prog = sum(1 for r in rows if r["status"] == "IN_PROGRESS")
    risk = sum(1 for r in rows if r["status"] == "NOT_MENTIONED")

    m1, m2, m3 = st.columns(3)
    m1.metric("✅ Done", done)
    m2.metric("🔄 In progress", prog)
    m3.metric("⚠️ At risk", risk)

    # Styled HTML table with colored status pills for visual impact.
    header = (
        "<table style='width:100%;border-collapse:collapse'>"
        "<thead><tr style='text-align:left;border-bottom:2px solid #ddd'>"
        "<th style='padding:8px'>Owner</th><th style='padding:8px'>Status</th>"
        "<th style='padding:8px'>Action item</th><th style='padding:8px'>Evidence</th>"
        "</tr></thead><tbody>"
    )
    body = ""
    for r in rows:
        body += (
            "<tr style='border-bottom:1px solid #eee'>"
            f"<td style='padding:8px;font-weight:600'>{r['owner']}</td>"
            f"<td style='padding:8px'>{_pill(r['status'])}</td>"
            f"<td style='padding:8px'>{r['description']}</td>"
            f"<td style='padding:8px;color:#555;font-size:.9rem'>{r['evidence']}</td>"
            "</tr>"
        )
    st.markdown(header + body + "</tbody></table>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Main flow — mirrors main.py, rendered in the browser
# ---------------------------------------------------------------------------
if run:
    if not meeting1.strip() or not meeting2.strip():
        st.error("Please provide both meeting transcripts.")
        st.stop()

    try:
        with st.status("Running the two-tool follow-through flow…", expanded=True) as status:
            st.write("**Tool A** · extracting Meeting 1 action items (persistent memory)…")
            meeting1_items = json.loads(extract_action_items(meeting1))

            st.write("**Tool A** · extracting Meeting 2's new action items…")
            meeting2_items = json.loads(extract_action_items(meeting2))

            st.write("**Tool B** · checking follow-through of Meeting 1 items vs Meeting 2…")
            followthrough = json.loads(
                check_followthrough(json.dumps(meeting1_items), meeting2)
            )

            at_risk = [r for r in followthrough if r["status"] == "NOT_MENTIONED"]
            by_desc = {it["description"]: it for it in meeting1_items}
            followups: List[Dict[str, str]] = []
            for r in at_risk:
                st.write(f"**Drafting** · follow-up nudge for {r['owner']}…")
                original = by_desc.get(r["description"], {})
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
            status.update(label="Done", state="complete", expanded=False)
    except Exception as exc:  # surface a friendly error instead of a stack trace
        st.error(
            "The agent run failed. This usually means AWS Bedrock credentials "
            "or model access aren't configured in this environment.\n\n"
            f"Details: {exc}"
        )
        st.stop()

    st.divider()
    st.header("Results")

    st.subheader("(a) Meeting 2 — new action items")
    _render_action_items(meeting2_items)

    st.subheader("(b) Follow-through on Meeting 1's action items")
    _render_followthrough(followthrough)

    st.subheader("(c) Drafted follow-up messages for at-risk items")
    if not followups:
        st.success("🎉 Nothing at risk — every Meeting 1 item was addressed.")
    else:
        for fm in followups:
            st.markdown(
                f"<div class='nudge'><b>✉️ To {fm['owner']}:</b><br>{fm['message']}</div>",
                unsafe_allow_html=True,
            )

    with st.expander("Raw JSON (Meeting 1 memory / follow-through report)"):
        st.json({"meeting_1_action_items": meeting1_items, "followthrough": followthrough})
else:
    st.info("Sample transcripts are pre-filled. Click **Run the agent** to see the follow-through report.")
