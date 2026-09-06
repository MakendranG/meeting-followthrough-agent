"""
app.py — Streamlit web UI for the Meeting Follow-Through Agent
=============================================================

A polished browser front-end over the exact same two Strands tools used by the
CLI (`extract_action_items` and `check_followthrough`) plus the LLM
`draft_followup_message` helper — see agent.py.

Two modes, auto-detected:
  • Demo (keyless, default): shows a real cached result — no AWS, no cost.
  • Live: runs the Strands agent on Amazon Bedrock (needs AWS credentials, from
    the host env or the optional "bring your own temporary credentials" panel).

Run:  streamlit run app.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import streamlit as st

# Optional .env convenience (same as main.py).
try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover
    pass

# NOTE: the Strands agent is imported lazily (only in Live mode) so keyless Demo
# mode never depends on Bedrock being reachable.

BASE_DIR = Path(__file__).resolve().parent
SAMPLE_DIR = BASE_DIR / "sample_data"
DEMO_RESULT_FILE = SAMPLE_DIR / "demo_result.json"


# ===========================================================================
# Helpers
# ===========================================================================
def _creds_available() -> bool:
    """True if any standard AWS credential source is present in the env."""
    import os

    keys = (
        "AWS_ACCESS_KEY_ID",
        "AWS_BEARER_TOKEN_BEDROCK",
        "AWS_PROFILE",
        "AWS_ROLE_ARN",
        "AWS_CONTAINER_CREDENTIALS_RELATIVE_URI",
        "AWS_WEB_IDENTITY_TOKEN_FILE",
    )
    return any(os.environ.get(k) for k in keys)


def _load_demo_result() -> dict:
    return json.loads(DEMO_RESULT_FILE.read_text(encoding="utf-8"))


def _load_sample(name: str) -> str:
    path = SAMPLE_DIR / name
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _run_live(meeting1_text: str, meeting2_text: str, temp_creds: dict | None = None) -> dict:
    """Execute the real two-tool flow against Amazon Bedrock.

    If ``temp_creds`` is provided (a visitor's short-lived STS credentials) it is
    applied to the process environment ONLY for the duration of this call and
    restored afterwards. Nothing is written to disk or logged.
    """
    import os

    saved: dict[str, str | None] = {}
    if temp_creds:
        for k, v in temp_creds.items():
            saved[k] = os.environ.get(k)
            os.environ[k] = v
    try:
        from agent import (
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
        if temp_creds:
            for k, old in saved.items():
                if old is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = old


# Status → (emoji, text color, background) for the pills.
STATUS_META = {
    "DONE": ("✅", "#065f46", "#d1fae5"),
    "IN_PROGRESS": ("🔄", "#92400e", "#fef3c7"),
    "NOT_MENTIONED": ("⚠️", "#991b1b", "#fee2e2"),
}


def _pill(status: str) -> str:
    emoji, fg, bg = STATUS_META.get(status, ("•", "#334155", "#e2e8f0"))
    return (
        f"<span style='background:{bg};color:{fg};padding:4px 12px;border-radius:999px;"
        f"font-weight:700;font-size:.8rem;white-space:nowrap'>{emoji} {status.replace('_',' ')}</span>"
    )


# ===========================================================================
# Page + theme
# ===========================================================================
st.set_page_config(
    page_title="Meeting Follow-Through Agent",
    page_icon="✅",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
      html, body, [class*="css"] { font-family:'Inter',sans-serif; }
      .block-container { padding-top:1.4rem; max-width:1200px; }

      /* Hero */
      .hero{
        background:linear-gradient(120deg,#4f46e5 0%,#7c3aed 55%,#9333ea 100%);
        border-radius:22px; padding:2.2rem 2.4rem; color:#fff;
        box-shadow:0 18px 40px -18px rgba(79,70,229,.6); margin-bottom:1.4rem;
      }
      .hero h1{ color:#fff; font-size:2.3rem; font-weight:800; margin:0 0 .5rem; letter-spacing:-.02em; }
      .hero .sub{ color:#ede9fe; font-size:1.12rem; max-width:760px; margin:0 0 1.1rem; line-height:1.55; }
      .chips span{
        display:inline-block; background:rgba(255,255,255,.16); backdrop-filter:blur(4px);
        border:1px solid rgba(255,255,255,.25); color:#fff; padding:5px 13px;
        border-radius:999px; font-size:.8rem; font-weight:600; margin:0 .45rem .45rem 0;
      }

      /* Section headings */
      .sec{ font-size:1.15rem; font-weight:700; color:#1e293b; margin:1.6rem 0 .6rem;
             display:flex; align-items:center; gap:.5rem; }
      .sec .n{ background:#ede9fe; color:#6d28d9; width:26px; height:26px; border-radius:8px;
               display:inline-flex; align-items:center; justify-content:center; font-size:.85rem; font-weight:800; }

      /* Stat cards */
      .stats{ display:grid; grid-template-columns:repeat(3,1fr); gap:14px; margin:.4rem 0 .6rem; }
      .stat{ border-radius:16px; padding:1.1rem 1.2rem; color:#fff; }
      .stat .k{ font-size:2.1rem; font-weight:800; line-height:1; }
      .stat .l{ font-size:.9rem; font-weight:600; opacity:.95; margin-top:.35rem; }
      .stat.done{ background:linear-gradient(135deg,#10b981,#059669); }
      .stat.prog{ background:linear-gradient(135deg,#f59e0b,#d97706); }
      .stat.risk{ background:linear-gradient(135deg,#ef4444,#dc2626); }

      /* Cards / tables */
      .card{ background:#fff; border:1px solid #eceef3; border-radius:16px; padding:.4rem 1.1rem;
             box-shadow:0 6px 20px -14px rgba(15,23,42,.25); }
      table.ft{ width:100%; border-collapse:collapse; }
      table.ft th{ text-align:left; padding:12px 10px; font-size:.78rem; text-transform:uppercase;
                   letter-spacing:.04em; color:#64748b; border-bottom:2px solid #eef2f7; }
      table.ft td{ padding:13px 10px; border-bottom:1px solid #f1f5f9; font-size:.95rem; color:#1e293b; vertical-align:top; }
      table.ft tr:last-child td{ border-bottom:none; }
      .owner{ font-weight:700; }
      .ev{ color:#64748b; font-size:.86rem; }

      /* Item chips */
      .item{ display:flex; gap:.7rem; align-items:flex-start; padding:.7rem .2rem; border-bottom:1px solid #f1f5f9; }
      .item:last-child{ border-bottom:none; }
      .item .idx{ background:#eef2ff; color:#4f46e5; min-width:26px; height:26px; border-radius:8px;
                  display:flex; align-items:center; justify-content:center; font-weight:800; font-size:.8rem; }
      .item .desc{ font-weight:600; color:#1e293b; }
      .item .meta{ color:#64748b; font-size:.85rem; margin-top:2px; }

      /* Nudge */
      .nudge{ border:1px solid #e9d5ff; border-left:5px solid #7c3aed; background:#faf5ff;
              padding:1rem 1.2rem; border-radius:12px; margin-bottom:.9rem; }
      .nudge .to{ font-weight:700; color:#6d28d9; margin-bottom:.3rem; }
      .nudge .msg{ color:#3b0764; line-height:1.55; }

      .srcbadge{ display:inline-block; padding:5px 12px; border-radius:999px; font-size:.82rem; font-weight:600; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <h1>✅ Meeting Follow-Through Agent</h1>
      <p class="sub">The action item you agreed to last week? Nobody checked if it got done — until now.
      This agent extracts commitments from one meeting, <b>remembers</b> them, then checks the
      <i>next</i> meeting to see what was done, what's in progress, and what quietly fell through —
      and drafts the nudge for you.</p>
      <div class="chips">
        <span>⚡ Built With: Strands Agents SDK</span>
        <span>🧠 Amazon Bedrock · Claude</span>
        <span>🏆 Agents for Humans · Professional track</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ===========================================================================
# Sidebar — run mode + optional temporary credentials
# ===========================================================================
env_creds = _creds_available()

with st.sidebar:
    st.markdown("### ⚙️ Run mode")

    byo_creds = None
    with st.expander("🔑 Advanced: use my own AWS (temporary session credentials)"):
        st.caption(
            "Optional. Paste **temporary** STS credentials to run live on your own "
            "AWS account. Session-only — never stored. Use short-lived tokens from "
            "`aws sts get-session-token` / `assume-role` or an SSO screen."
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

    live_available = env_creds or (byo_creds is not None)
    mode = st.radio(
        "How should the agent run?",
        options=["🧊 Demo (cached · no AWS keys)", "🟢 Live agent (Amazon Bedrock)"],
        index=1 if live_available else 0,
        help="Demo shows a real cached result and needs no credentials. Live runs the agent on Bedrock.",
    )
    live_mode = "Live" in mode
    if live_mode and not live_available:
        st.warning("No credentials available — Live will fall back to the cached Demo result.")

    src = "host environment" if env_creds else ("your temporary credentials" if byo_creds else "none (keyless)")
    st.markdown(f"<span class='srcbadge' style='background:#eef2ff;color:#4338ca'>🔎 Credentials: {src}</span>", unsafe_allow_html=True)

    st.divider()
    st.markdown(
        "**How it works**\n\n"
        "1. **Tool A** `extract_action_items` — pulls owner + deadline per item\n"
        "2. **Tool B** `check_followthrough` — DONE / IN&nbsp;PROGRESS / NOT&nbsp;MENTIONED\n"
        "3. **Draft** — a polite nudge for each at-risk item",
        unsafe_allow_html=True,
    )
    st.caption("Two Strands tools + memory across meetings — more than a summarizer.")


if not live_available:
    st.info(
        "🔒 **Public keyless demo.** No AWS credentials are configured, so results below come from a "
        "**real cached run** of the live Strands + Amazon Bedrock agent — no cost, nothing to break. "
        "To run it live, add temporary credentials in the sidebar **Advanced** panel, or run locally."
    )


# ===========================================================================
# Inputs
# ===========================================================================
st.markdown("<div class='sec'><span class='n'>›</span> Meeting transcripts</div>", unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    st.markdown("**🗓️ Meeting 1 — earlier**")
    meeting1 = st.text_area("Meeting 1 transcript", value=_load_sample("meeting_1_transcript.txt"),
                            height=300, key="m1", label_visibility="collapsed")
with col2:
    st.markdown("**🗓️ Meeting 2 — later**")
    meeting2 = st.text_area("Meeting 2 transcript", value=_load_sample("meeting_2_transcript.txt"),
                            height=300, key="m2", label_visibility="collapsed")

btn_label = "▶  Run the agent live" if live_mode else "▶  Show the follow-through report"
run = st.button(btn_label, type="primary", use_container_width=True)


# ===========================================================================
# Rendering
# ===========================================================================
def _render_action_items(items: List[Dict[str, str]]) -> None:
    if not items:
        st.info("No action items found.")
        return
    html = "<div class='card'>"
    for i, it in enumerate(items, 1):
        html += (
            "<div class='item'>"
            f"<div class='idx'>{i}</div>"
            f"<div><div class='desc'>{it['description']}</div>"
            f"<div class='meta'>👤 {it['owner']} &nbsp;·&nbsp; ⏰ {it['deadline']}</div></div>"
            "</div>"
        )
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def _render_followthrough(rows: List[Dict[str, str]]) -> None:
    done = sum(1 for r in rows if r["status"] == "DONE")
    prog = sum(1 for r in rows if r["status"] == "IN_PROGRESS")
    risk = sum(1 for r in rows if r["status"] == "NOT_MENTIONED")
    st.markdown(
        f"""
        <div class="stats">
          <div class="stat done"><div class="k">{done}</div><div class="l">✅ Done</div></div>
          <div class="stat prog"><div class="k">{prog}</div><div class="l">🔄 In progress</div></div>
          <div class="stat risk"><div class="k">{risk}</div><div class="l">⚠️ At risk (not mentioned)</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    rows_html = ""
    for r in rows:
        rows_html += (
            "<tr>"
            f"<td class='owner'>{r['owner']}</td>"
            f"<td>{_pill(r['status'])}</td>"
            f"<td>{r['description']}</td>"
            f"<td class='ev'>{r['evidence']}</td>"
            "</tr>"
        )
    st.markdown(
        "<div class='card'><table class='ft'><thead><tr>"
        "<th>Owner</th><th>Status</th><th>Action item</th><th>Evidence</th>"
        "</tr></thead><tbody>" + rows_html + "</tbody></table></div>",
        unsafe_allow_html=True,
    )


def _render_results(result: dict, source_html: str) -> None:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(source_html, unsafe_allow_html=True)

    st.markdown("<div class='sec'><span class='n'>a</span> Meeting 2 — new action items</div>", unsafe_allow_html=True)
    _render_action_items(result.get("meeting_2_action_items", []))

    st.markdown("<div class='sec'><span class='n'>b</span> Follow-through on Meeting 1's items</div>", unsafe_allow_html=True)
    _render_followthrough(result.get("followthrough", []))

    st.markdown("<div class='sec'><span class='n'>c</span> Drafted follow-up messages</div>", unsafe_allow_html=True)
    followups = result.get("followups", [])
    if not followups:
        st.success("🎉 Nothing at risk — every Meeting 1 item was addressed.")
    else:
        for fm in followups:
            st.markdown(
                f"<div class='nudge'><div class='to'>✉️ To {fm['owner']}</div>"
                f"<div class='msg'>{fm['message']}</div></div>",
                unsafe_allow_html=True,
            )
    with st.expander("🧾 Raw JSON"):
        st.json(result)


# ===========================================================================
# Main flow
# ===========================================================================
if run:
    if live_mode and live_available:
        if not meeting1.strip() or not meeting2.strip():
            st.error("Please provide both meeting transcripts.")
            st.stop()
        try:
            with st.status("Running the two-tool follow-through flow on Amazon Bedrock…", expanded=True) as status:
                st.write("🔍 **Tool A** · extracting action items…")
                st.write("🔗 **Tool B** · checking cross-meeting follow-through…")
                st.write("✍️ **Drafting** · nudges for at-risk items…")
                result = _run_live(meeting1, meeting2, temp_creds=byo_creds)
                status.update(label="Live run complete", state="complete", expanded=False)
            note = "generated just now via Amazon Bedrock" + (" using your temporary credentials" if byo_creds else "")
            _render_results(result, f"<span class='srcbadge' style='background:#d1fae5;color:#065f46'>🟢 Live result — {note}.</span>")
        except Exception as exc:
            st.warning(f"Live run failed — falling back to the cached demo result.\n\nDetails: {exc}")
            _render_results(_load_demo_result(), "<span class='srcbadge' style='background:#fef3c7;color:#92400e'>📁 Cached demo result (fallback).</span>")
    else:
        _render_results(
            _load_demo_result(),
            "<span class='srcbadge' style='background:#e0e7ff;color:#3730a3'>📁 Demo result — a real prior run of the live Strands + Bedrock agent (keyless).</span>",
        )
else:
    st.markdown(
        "<div class='card' style='padding:1.1rem 1.3rem;color:#475569'>"
        "👆 Sample transcripts are pre-filled. Click the button above to see the follow-through report."
        "</div>",
        unsafe_allow_html=True,
    )
