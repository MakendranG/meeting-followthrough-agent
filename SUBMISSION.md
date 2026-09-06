# Submission Checklist — Agents for Humans Hackathon

**Track:** Professional Agents
**Project:** Meeting Follow-Through Agent
**Built With:** Strands Agents SDK + Amazon Bedrock
**Repository:** https://github.com/MakendranG/meeting-followthrough-agent (public)
**Deadline:** 15 Sept 2026 @ 5:30am GMT+5:30 — submit 3–4 hours early.

Use this to make sure nothing required is missing before submitting on Devpost.

## Required submission items

- [x] **Text description** — what it does, who it's for, how it works
      → see `README.md` (leads with the problem; names Strands Agents explicitly).
- [x] **Public URL to code repo** —
      https://github.com/MakendranG/meeting-followthrough-agent (public).
- [x] **All source code + setup instructions to run it** — `agent.py`, `main.py`,
      `demo.sh`, `requirements.txt`, `.env.example`, `sample_data/`.
- [x] **MIT or Apache license** — `LICENSE` (MIT) is present.
      - [x] **Visible in the repo's About/sidebar** — GitHub auto-detected it
        (`gh repo view` reports `licenseInfo: MIT License`). Copyright line now
        reads "Makendran".
- [x] **README** — present, with cold-start setup a stranger can follow.
- [x] **Architecture diagram** — `ARCHITECTURE.md` (Mermaid).
- [ ] **Demo video (≤ 5 minutes)** — record using `DEMO_SCRIPT.md`. Must:
      - [ ] show the project working end-to-end (the follow-through table + nudge)
      - [ ] cover (1) the problem, (2) who it's for, (3) why it matters
      - [ ] be uploaded publicly to YouTube or Vimeo; put the link on Devpost
      - [ ] say "Strands Agents SDK" out loud / on a slide
- [ ] **AWS Builder ID** — create one at the AWS Builder ID portal and add it to
      the Devpost submission form.
- [ ] *(Optional, scores higher)* **Live demo link** — deploy the Streamlit app
      (`app.py`) to Streamlit Community Cloud (**no Secrets needed** — it defaults
      to keyless Demo mode using the real cached `sample_data/demo_result.json`).
      Add AWS Secrets only if you want the hosted app to run live on Bedrock.
      Add the URL to Devpost and to `docs/index.html`. A visual GitHub Pages
      landing page is in `docs/` (enable via Settings → Pages → branch `main`
      / `/docs`).
- [ ] *(Optional bonus points)* **builder.aws.com post** — publish your build
      journey with "Agents for Humans" in the title before the deadline.

### Amazon Bedrock AgentCore — optional
Per the rules, AgentCore deployment "strengthens your Technical Implementation
score, but it's not required." The project already runs on Amazon Bedrock via
the Strands SDK. Treat AgentCore as a stretch enhancement, not a requirement.

## "Impossible to miss" Strands usage (per organizer tips)

- [x] Named in the README title/summary and a **Built With** section.
- [x] Two custom `@tool` functions in `agent.py` (`extract_action_items`,
      `check_followthrough`) — the core of the agent.
- [ ] Shown clearly in the demo video.

## Security / hygiene (per organizer tips)

- [x] **No hardcoded secrets** — all credentials come from environment variables;
      `agent.py`/`main.py` read `AWS_*` / `BEDROCK_MODEL_ID` from the env only.
      The Streamlit app's optional "bring your own temporary credentials" panel
      keeps pasted STS tokens **in memory for one run only** (never stored/logged;
      env restored after the call).
- [x] `.env` is git-ignored (only `.env.example` with placeholders is committed).
- [x] `.venv/` and generated `memory/*.json` are git-ignored.
- [x] **Repo scanned before pushing** — verified no secrets in tracked source
      (matches appeared only inside the git-ignored `.venv/`). Re-verify after
      any future edits with a grep for `AKIA` / `aws_secret_access_key`.

## Judging-criteria self-check

- **Technological Implementation** — non-trivial two-tool Strands design; runs
  end-to-end on Amazon Bedrock. (Optional: deploy to Bedrock AgentCore or add a
  live demo to strengthen this score.)
- **Design** — complete product experience: clear CLI report, persistent memory,
  drafted follow-ups — not just a proof of concept.
- **Potential Impact** — specific audience (people running recurring meetings)
  and a concrete pain (commitments dying between meetings).
- **Creativity & Originality** — the follow-through *check across meetings* is
  the non-obvious part; most tools stop at summarizing one meeting.
- **Presentation** — `DEMO_SCRIPT.md` keeps the video ≤ 5 min and on-message.

## Before you click submit

- [x] Repo is **public** — https://github.com/MakendranG/meeting-followthrough-agent
- [x] Copyright name filled in `LICENSE` ("Makendran").
- [ ] `demo.sh` runs clean from a fresh clone (test on a machine without the
      `.venv` already present).
- [ ] Video link works in an incognito window.
- [ ] Save a Devpost **draft** early; you can keep editing until the deadline.
