# Demo Video Script — Meeting Follow-Through Agent

A shot-by-shot outline for the submission video. **Hard limit: 5 minutes**
(judges may stop watching at 5:00 — front-load everything that matters). No need
to appear on camera; slides + screen recording + voiceover are fine.

**Pitch must cover, in order:** (1) the problem → (2) who it's for → (3) why it
matters → (4) the project working end-to-end. This script does exactly that.

---

## 0:00–0:35 · The problem (hook first)

**On screen:** Title slide → then a simple "before" graphic: a meeting, four
checkboxes, and three of them fading to grey.

**Say:**
> "Every recurring meeting ends the same way: people agree to do things — and
> then some of it quietly evaporates. Not because anyone's lazy, but because
> there's no lightweight system that both captures what was promised AND checks,
> at the next meeting, whether it actually happened. Note-takers and summarizers
> only do the first half. The commitment that silently dies between meetings is
> the one that becomes a fire drill later."

## 0:35–1:00 · Who it's for

**On screen:** Three icons — team lead, project coordinator, scrum master.

**Say:**
> "This is for anyone running recurring meetings — managers, team leads, project
> coordinators. The same people commit to work week after week, and today the
> only way to catch dropped items is to manually diff last week's notes against
> this week's discussion. Every week. By hand."

## 1:00–1:30 · Why it matters + what it is

**On screen:** One line — "Extract → Remember → Check follow-through → Nudge."
Name-drop: **Built With: Strands Agents SDK** + **Amazon Bedrock**.

**Say:**
> "The Meeting Follow-Through Agent automates that cross-check. It's a Strands
> Agents SDK agent with two custom tools: one extracts action items from a
> meeting; the second takes the *previous* meeting's items and checks the new
> transcript for evidence each was done. It has memory across meetings — that's
> what makes it more than a summarizer. Anything at risk, it drafts a polite
> nudge for. Let me show it running."

## 1:30–4:15 · Live run (the core of the video)

**On screen:** Terminal. Run:
```bash
AWS_REGION=us-east-1 ./demo.sh
```

Narrate each step as it prints:

- **1:30–2:00 — Show the two transcripts** briefly (Meeting 1 and Meeting 2 side
  by side). "Two real-world-style transcripts. Meeting 1 has four commitments
  from four different people."
- **2:00–2:35 — STEP 1 extract + memory.** "Tool A pulls out the four action
  items with owner and deadline, and writes them to a JSON memory file — that's
  the agent remembering across meetings." Show `memory/meeting_1_action_items.json`.
- **2:35–3:00 — STEP 2/3.** "Now Meeting 2. Tool A grabs the *new* items, and
  Tool B compares Meeting 1's stored items against Meeting 2's transcript."
- **3:00–3:50 — The money shot: the follow-through table.** Zoom in:
  ```
  Marcus     ✅ DONE           Deploy rate limiting on the invite…
  Dana       ✅ DONE           Finalize empty-state designs and hand…
  Leo        ⚠️  NOT_MENTIONED Draft the launch blog post and send for…
  Sam        🔄 IN_PROGRESS    Build conversion funnel dashboard
  Summary: 2 done · 1 in progress · 1 at risk (not mentioned)
  ```
  "Two done, one in progress — and Leo's blog post was never mentioned. The
  agent flags it as at risk."
- **3:50–4:15 — The drafted nudge.** Show the follow-up message to Leo. "And it
  drafts the follow-up for me — polite, specific, ready to send."

## 4:15–4:45 · How it works (architecture)

**On screen:** The Mermaid diagram from `ARCHITECTURE.md`.

**Say:**
> "Under the hood: two Strands tools, both using Amazon Bedrock for the language
> reasoning, plus a persistent memory layer that carries commitments from one
> meeting to the next. Deterministic Python just orchestrates and formats."

## 4:45–5:00 · Close

**On screen:** Repo URL + "Built With: Strands Agents SDK" + MIT license badge.

**Say:**
> "Meeting Follow-Through Agent — it makes sure the things people promise in
> meetings actually get done. Code and setup are in the repo. Thanks for
> watching."

---

## Recording tips
- Do a dry run first — the LLM output wording varies slightly per run; record a
  take where the table reads cleanly.
- Pre-create the `.venv` before recording so `demo.sh` doesn't spend screen time
  on `pip install` (or cut that portion in editing).
- Keep the terminal font large enough to read the follow-through table.
- Say "Strands Agents SDK" out loud at least once — judges review that first.
