# 🎬 Demo Video Script — Meeting Follow-Through Agent

**Hard limit: 5:00** (judges may stop at 5 minutes — front-load the good stuff).
No need to appear on camera; slides + screen recording + voiceover are fine.

**Required pitch coverage (per the rules):** (1) the problem → (2) who it's for →
(3) why it matters → (4) the project working end-to-end. Also say **"Strands
Agents SDK"** out loud and show it.

**Links to have open:**
- Live demo: https://meeting-followthrough-agent.streamlit.app/
- Project page: https://makendrang.github.io/meeting-followthrough-agent/
- Repo: https://github.com/MakendranG/meeting-followthrough-agent

**Total ≈ 4:45**, leaving buffer. Timings are cumulative.

---

## ⏱️ 0:00 – 0:35 — Hook + the problem  *(35s)*

**On screen:** Title slide → the project page hero.

**Say:**
> "Every recurring meeting ends the same way: people agree to do things — and then some of it quietly evaporates. Not because anyone's lazy, but because there's no lightweight system that does *both* halves of the job: **extract** what was promised, *and* **check at the next meeting whether it actually happened.** Most meeting tools only do the first half — they summarize one meeting and move on. So I built the **Meeting Follow-Through Agent** with the **Strands Agents SDK**."

## ⏱️ 0:35 – 1:05 — Who it's for + why it matters  *(30s)*

**On screen:** Three icons — team lead / project coordinator / scrum master.

**Say:**
> "This is for **anyone running recurring meetings** — managers, team leads, project coordinators. Today the only way to catch a dropped commitment is to manually diff last week's notes against this week's discussion, every single week. The item that slips through becomes a fire drill later. This agent does that cross-check automatically and surfaces what's at risk **before** it blows up."

## ⏱️ 1:05 – 1:35 — What it does + the two-tool idea  *(30s)*

**On screen:** The architecture diagram (`docs/architecture.png`).

**Say:**
> "It's a Strands agent with **two custom tools**. **Tool A — extract_action_items** — pulls every commitment from a meeting with its owner and deadline. **Tool B — check_followthrough** — takes the *previous* meeting's items and checks the new transcript to see what got done. Meeting 1's items are saved to memory, so Meeting 2 is held accountable to them. All the language reasoning runs on **Amazon Bedrock**. That memory across meetings is what makes it more than a summarizer."

## ⏱️ 1:35 – 3:45 — Live demo  *(the core — ~2:10)*

**On screen:** The live Streamlit app.

- **1:35–2:00 — Show the inputs.** "Here's the live app. Two transcripts — Meeting 1 and a later Meeting 2. Meeting 1 has four commitments from four different people." Scroll the two transcripts briefly.
- **2:00–2:20 — Run it.** Click **Run**. "One click kicks off the agent: Tool A extracts the items, Tool B compares them against Meeting 2, and it drafts follow-ups." (Narrate the status steps as they appear.)
- **2:20–3:10 — The money shot: the follow-through table.** Point at the colored stat cards and the table:
  > "Two done, one in progress — and Leo's blog post was **never mentioned** in Meeting 2, so it's flagged **at risk**. Notice the evidence column — the agent quotes *why* it made each call: 'deployed to production this morning' → DONE."
- **3:10–3:45 — The drafted nudge.** Scroll to the follow-up message:
  > "And for the at-risk item, it's already **drafted a polite nudge to Leo** — ready to send. That's the whole point: it doesn't just tell me something slipped, it does the next step for me."

## ⏱️ 3:45 – 4:15 — How it's built (credibility)  *(30s)*

**On screen:** Split — `agent.py` `@tool` functions on one side, the diagram on the other.

**Say:**
> "Under the hood: two Python functions decorated with Strands' **@tool**, each backed by **Amazon Bedrock / Claude**. Deterministic Python orchestrates and stores; the LLM handles the fuzzy language understanding. There's a CLI and this Streamlit UI over the *same* tools — and the public demo runs **keyless**, showing a real cached result so anyone can try it with zero setup."

## ⏱️ 4:15 – 4:45 — Close  *(30s)*

**On screen:** Project page with the three links + "Built With: Strands Agents SDK".

**Say:**
> "The **Meeting Follow-Through Agent** — built with the Strands Agents SDK and Amazon Bedrock — makes sure the things people promise in meetings actually get done. It's live, the code's on GitHub under MIT, and everything you need to run it is in the README. Thanks for watching."

---

## 🎥 Recording tips

- **Pre-warm the demo:** run it once before recording so any cold-start/model
  latency is out of the way; if using Live mode locally, confirm your AWS creds
  work first.
- **Record a clean take:** LLM wording varies slightly per run — capture one
  where the table reads clearly (2 DONE · 1 IN&nbsp;PROGRESS · 1 NOT&nbsp;MENTIONED).
- **Zoom the browser** to ~125–150% so the table and cards are readable on video.
- **Trim dead air** during the model call in editing (or speed it up 2×).
- **Say "Strands Agents SDK" out loud** at least once and show it on screen —
  judges review that first.
- **Export 1080p**, upload to YouTube/Vimeo (unlisted is fine), and paste the
  link into the Devpost "Video demo link" field.

## 🎙️ One-line version (if you need a 30-sec teaser)

> "Meeting action items get agreed on, then quietly disappear. The Meeting
> Follow-Through Agent — built with the Strands Agents SDK on Amazon Bedrock —
> extracts commitments from one meeting, remembers them, checks the next meeting
> for what actually got done, and drafts follow-up nudges for whatever slipped."
