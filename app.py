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

# NOTE: we do NOT import the Strands agent at module load. The agent's tools
# call Amazon Bedrock, which needs AWS credentials. This app supports a fully
# **keyless Demo mode** for public deploys, so we import the agent lazily —
# only when the user actually runs Live mode. This keeps the public app working
# with zero AWS credentials and zero cost.

BASE_DIR = Path(__file__).resolve().parent
SAMPLE_DIR = BASE_DIR / "sample_data"
DEMO_RESULT_FILE = SAMPLE_DIR / "demo_result.json"


def _creds_available() -> bool:
    """Detect whether AWS credentials appear to be configured.

    Returns True if any standard AWS credential source is present in the
    environment. On a fresh public Streamlit deploy none of these exist, so the
    app defaults to keyless Demo mode.
    """
    import os

    keys = (
        "AWS_ACCESS_KEY_ID",
        "AWS_BEARER_TOKEN_BEDROCK",
        "AWS_PROFILE",
        "AWS_ROLE_ARN",
        "AWS_CONTAINER_CREDENTIALS_RELATIVE_URI",  # ECS/Fargate task role
        "AWS_WEB_IDENTITY_TOKEN_FILE",             # IRSA / OIDC
    )
    return any(os.environ.get(k) for k in keys)


def _load_demo_result() -> dict:
    """Load the cached real-run output that powers keyless Demo mode."""
    return json.loads(DEMO_RESULT_FILE.read_text(encoding="utf-8"))

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
# Mode selection — keyless Demo (default) vs Live (calls Bedrock)
# ---------------------------------------------------------------------------
env_creds = _creds_available()

with st.sidebar:
    st.header("Run mode")

    # --- Optional: bring-your-own TEMPORARY AWS credentials -----------------
    # A web app cannot borrow a visitor's AWS Console login session (browser
    # cross-site cookie isolation + AWS design). The safe, buildable way for a
    # visitor to run this live on *their own* AWS account is to paste SHORT-LIVED
    # STS session credentials (Access Key + Secret + Session Token) — e.g. from
    # `aws sts get-session-token` or an SSO "command line access" screen. These
    # expire on their own and are held ONLY in memory for the duration of one
    # run; they are never written to disk, logs, or the repo.
    byo_creds = None
    with st.expander("🔑 Advanced: use my own AWS (temporary session credentials)"):
        st.caption(
            "Optional. Paste **temporary** STS credentials to run the agent live "
            "on your own AWS account. Session-only — never stored. Prefer "
            "short-lived tokens from `aws sts get-session-token` or SSO."
        )
        byo_key = st.text_input("AWS Access Key ID (temporary)", type="password", key="byo_key")
        byo_secret = st.text_input("AWS Secret Access Key (temporary)", type="password", key="byo_secret")
        byo_token = st.text_input("AWS Session Token", type="password", key="byo_token")
        byo_region = st.text_input("AWS Region", value="us-east-1", key="byo_region")
        if byo_key and byo_secret and byo_token:
            byo_creds = {
                "AWS_ACCESS_KEY_ID": byo_key.strip(),
                "AWS_SECRET_ACCESS_KEY": byo_secret.strip(),
                "AWS_SESSION_TOKEN": byo_token.strip(),
                "AWS_REGION": (byo_region or "us-east-1").strip(),
                "AWS_DEFAULT_REGION": (byo_region or "us-east-1").strip(),
            }
            st.success("Temporary credentials captured for this session only.")
        elif any([byo_key, byo_secret, byo_token]):
            st.warning("Provide all three: Access Key ID, Secret, and Session Token.")

    # Live mode is possible if the host has creds OR the visitor supplied temp ones.
    live_available = env_creds or (byo_creds is not None)

    default_index = 1 if live_available else 0
    mode = st.radio(
        "How should the agent run?",
        options=["Demo (cached, no AWS keys)", "Live agent (calls Amazon Bedrock)"],
        index=default_index,
        help=(
            "Demo mode shows a real, previously-generated result and needs no "
            "AWS credentials — perfect for a public link. Live mode runs the "
            "Strands agent against Amazon Bedrock and needs AWS credentials "
            "(from the host, or your own temporary ones above)."
        ),
    )
    live_mode = mode.startswith("Live")
    if live_mode and not live_available:
        st.warning(
            "No AWS credentials available. Live mode will fall back to the "
            "cached Demo result. Add temporary credentials above to run live."
        )
    src = "host environment" if env_creds else ("your temporary credentials" if byo_creds else "none")
    st.caption(f"🔎 Credentials source: **{src}**")

if not live_available:
    st.info(
        "🔒 **Public keyless demo.** No AWS credentials are configured, so this "
        "app runs in **Demo mode** — it displays a real result previously "
        "generated by the live Strands + Amazon Bedrock agent (no per-click cost, "
        "nothing to break). To run it live, use the **Advanced** panel in the "
        "sidebar to paste your own temporary AWS credentials, or run locally — "
        "see the README."
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

_btn_label = "▶ Run the agent (live)" if live_mode else "▶ Show the follow-through report (demo)"
run = st.button(_btn_label, type="primary", use_container_width=True)


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
# Live run — lazily import and call the Strands agent (needs AWS creds)
# ---------------------------------------------------------------------------
def _run_live(meeting1_text: str, meeting2_text: str, temp_creds: dict | None = None) -> dict:
    """Execute the real two-tool flow against Amazon Bedrock.

    Imported lazily so keyless Demo mode never requires the agent/boto3 to be
    callable. Raises on failure so the caller can fall back to the demo result.

    If ``temp_creds`` is provided (a visitor's short-lived STS credentials), it
    is applied to the process environment ONLY for the duration of this call and
    restored afterwards. Nothing is written to disk or logged.
    """
    import os

    # Snapshot + apply temporary credentials for this run only.
    saved: dict[str, str | None] = {}
    if temp_creds:
        for k, v in temp_creds.items():
            saved[k] = os.environ.get(k)
            os.environ[k] = v

    try:
        from agent import (  # local import on purpose (see module docstring)
            check_followthrough,
            draft_followup_message,
            extract_action_items,
        )

        m1_items = json.loads(extract_action_items(meeting1_text))
        m2_items = json.loads(extract_action_items(meeting2_text))
        followthrough = json.loads(check_followthrough(json.dumps(m1_items), meeting2_text))

        by_desc = {it["description"]: it for it in m1_items}
        followups: List[Dict[str, str]] = []
        for r in followthrough:
            if r["status"] == "NOT_MENTIONED":
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
        return {
            "meeting_2_action_items": m2_items,
            "followthrough": followthrough,
            "followups": followups,
        }
    finally:
        # Restore the environment — temp creds never persist beyond this run.
        if temp_creds:
            for k, old in saved.items():
                if old is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = old


def _render_results(result: dict, source_label: str) -> None:
    st.divider()
    st.header("Results")
    st.caption(source_label)

    st.subheader("(a) Meeting 2 — new action items")
    _render_action_items(result.get("meeting_2_action_items", []))

    st.subheader("(b) Follow-through on Meeting 1's action items")
    _render_followthrough(result.get("followthrough", []))

    st.subheader("(c) Drafted follow-up messages for at-risk items")
    followups = result.get("followups", [])
    if not followups:
        st.success("🎉 Nothing at risk — every Meeting 1 item was addressed.")
    else:
        for fm in followups:
            st.markdown(
                f"<div class='nudge'><b>✉️ To {fm['owner']}:</b><br>{fm['message']}</div>",
                unsafe_allow_html=True,
            )

    with st.expander("Raw JSON"):
        st.json(result)


# ---------------------------------------------------------------------------
# Main flow — branch on Demo (keyless, cached) vs Live (Bedrock)
# ---------------------------------------------------------------------------
if run:
    if live_mode:
        if not meeting1.strip() or not meeting2.strip():
            st.error("Please provide both meeting transcripts.")
            st.stop()
        try:
            with st.status("Running the two-tool follow-through flow on Amazon Bedrock…", expanded=True) as status:
                st.write("**Tool A** · extracting action items…")
                st.write("**Tool B** · checking cross-meeting follow-through…")
                st.write("**Drafting** · nudges for at-risk items…")
                result = _run_live(meeting1, meeting2, temp_creds=byo_creds)
                status.update(label="Live run complete", state="complete", expanded=False)
            src_note = (
                "🟢 Live result — generated just now by the Strands agent via Amazon Bedrock"
                + (" using your temporary credentials." if byo_creds else ".")
            )
            _render_results(result, src_note)
        except Exception as exc:
            st.warning(
                "Live run failed (likely no AWS Bedrock credentials/model access "
                "in this environment). Falling back to the cached demo result.\n\n"
                f"Details: {exc}"
            )
            _render_results(
                _load_demo_result(),
                "📁 Cached demo result (fallback) — a real prior Strands + Bedrock run.",
            )
    else:
        # Keyless Demo mode: show the real cached result. No AWS call.
        _render_results(
            _load_demo_result(),
            "📁 Demo result — a real output previously generated by the live "
            "Strands + Amazon Bedrock agent (no AWS credentials used here).",
        )
else:
    st.info(
        "Sample transcripts are pre-filled. Click the button above to see the "
        "follow-through report."
    )
