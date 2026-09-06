# Devpost Submission — Meeting Follow-Through Agent

Copy each section into the matching field on the Devpost "Enter a Submission" form.

---

## General info

### Project name  (≤60 chars)

```
Meeting Follow-Through Agent
```

### Elevator pitch  (≤200 chars)

```
Meeting action items get agreed on, then quietly evaporate. This Strands + Amazon Bedrock agent extracts commitments, remembers them, and checks the next meeting for what actually got done.
```

---

## Project details → Project Story  (paste into "About the project", Markdown)

## Inspiration

Every recurring meeting ends the same way: people agree to do things out loud, and then some of it quietly evaporates — not because anyone is lazy, but because there's no lightweight system that does **both** halves of the job: extract the commitments *and* check, at the next meeting, whether they actually happened. Most "meeting AI" tools only do the first half — they summarize one meeting in isolation. The commitment that silently dies between meetings is exactly the one they never catch. I wanted an agent that has **memory and follow-through across meetings**.

## What it does

Give it two transcripts — an earlier meeting and a later one — and it produces:

- **Meeting 2's new action items** (with owner and deadline)
- A **follow-through report** on Meeting 1's items: each tagged `DONE`, `IN_PROGRESS`, or `NOT_MENTIONED` (treated as *at risk*), with a supporting evidence quote
- A **drafted, ready-to-send follow-up message** for every at-risk item

In the sample run, Marcus's and Dana's tasks are detected as DONE, Sam's is IN_PROGRESS, and Leo's blog post — never mentioned in Meeting 2 — is flagged as at risk, with a polite nudge drafted automatically.

## How we built it

The agent is built with the **Strands Agents SDK** using a deliberate **two-tool design** plus a small persistent-memory layer:

- **Tool A — `extract_action_items(transcript_text)`**: parses one transcript into structured items (description, owner, deadline).
- **Tool B — `check_followthrough(previous_action_items, current_transcript_text)`**: compares the prior meeting's items against the new transcript and assigns each a status.

Both are plain Python functions decorated with `@tool`. Meeting 1's items are written to a JSON file that simulates memory *between* meetings, so Meeting 2 can be held accountable to Meeting 1's promises. The natural-language reasoning inside both tools — and the follow-up message drafting — runs on **Amazon Bedrock** (Claude Sonnet 4 family) via the Strands SDK's default Bedrock provider. There's a CLI (`main.py`) and a Streamlit web UI (`app.py`) that both call the exact same tools.

## Challenges we ran into

- **Making the public demo safe and free.** The agent calls Bedrock, which needs credentials and costs money. I built the Streamlit app to **auto-detect credentials and default to a keyless "Demo mode"** that shows a *real, cached* Bedrock result — so anyone can click the public link with zero AWS setup, zero cost, and nothing to break. A "Live mode" runs against Bedrock when credentials are present, with graceful fallback.
- **Letting curious users run it live without long-lived keys.** A web app can't borrow your AWS Console session (browser cross-site isolation forbids it), so I added an optional panel to paste **temporary STS credentials**, held in memory for one run only and never stored.
- **Robust JSON from an LLM.** Tool outputs are parsed defensively (fence-stripping + fallback extraction) and normalized so the downstream flow can trust the shape.

## What we learned

- Scope to one workflow end-to-end — a single thing that fully works beats five half-features.
- Put the LLM where judgment is needed and keep everything else deterministic; it makes the agent predictable and easy to debug.
- `@tool` in Strands is genuinely low-friction: a typed Python function with a good docstring *is* the tool.
- Design the demo for zero-friction access — keyless demo mode turned "you need AWS to try this" into "just click the link."

## What's next

- Wire real transcript sources (calendar / meeting-recording integrations).
- Swap the JSON memory for a managed store, and optionally deploy to Amazon Bedrock AgentCore for a fully hosted live agent.
- Email/Slack delivery of the drafted follow-up nudges.

---

## Built with  (tags — up to 25)

```
strands-agents-sdk
amazon-bedrock
anthropic-claude
python
streamlit
boto3
aws
github-pages
```

---

## "Try it out" links

```
Live demo: https://meeting-followthrough-agent.streamlit.app/
Project page: https://makendrang.github.io/meeting-followthrough-agent/
Code (GitHub): https://github.com/MakendranG/meeting-followthrough-agent
```

---

## Video demo link

```
<paste your YouTube/Vimeo URL here — ≤5 min, shows the project working + problem/who/why>
```
(Use `DEMO_SCRIPT.md` in the repo as the recording script.)

---

## PUBLIC URL to your code repo

```
https://github.com/MakendranG/meeting-followthrough-agent
```
(MIT license is present and detected by GitHub — visible in the repo's About section. README has full cold-start setup.)

---

## Architecture diagram (REQUIRED)

Upload the ready-made image: **`docs/architecture.png`** (1400×887 PNG) — already
in the repo. (Source: `docs/architecture.svg`; a Mermaid version is in
`ARCHITECTURE.md`.) Allowed: pdf, ppt, pptx, png, jpg, jpeg (max 35 MB).

---

## AWS Builder ID

Per the FAQ, **enter the email address you used to create your AWS Builder ID**
(create/manage one at https://profile.aws.amazon.com or via builder.aws.com).

```
<the email address for your AWS Builder ID>
```

---

## (Optional) Live demo link

```
https://meeting-followthrough-agent.streamlit.app/
```

### Testing instructions (if applicable)

```
Open the live demo link — it runs in keyless Demo mode and shows a real cached
agent result (no login/setup needed). To run it live on your own AWS: open the
sidebar "Advanced" panel, paste temporary STS credentials (aws sts get-session-token),
switch to "Live agent" mode, and click Run. Or clone the repo and run
`AWS_REGION=us-east-1 ./demo.sh` with AWS Bedrock access.
```

---

## Optional Bonus Blog Post URL  (must be on builder.aws.com, "Agents for Humans" in title)

```
<paste your builder.aws.com article URL here after publishing BUILDER_ARTICLE.md>
```

---

## FAQ-compliance notes (for your own reference — not form fields)

- **One track only:** submitted to **Professional Agents** only (the FAQ says a
  project may fall into just one track).
- **Newly created in the submission period:** built fresh during the Aug 10 –
  Sep 14, 2026 window using standard tools (Strands Agents SDK, AWS SDKs) and an
  AI coding assistant — which the rules explicitly allow. No pre-existing project
  was repackaged.
- **Synthetic data:** both sample transcripts are synthetic — no real meeting
  content, no PII — matching the FAQ's recommendation to use synthetic/anonymized
  data.
- **Public repo + license:** the repo is public with an MIT `LICENSE` detected in
  the About section.
- **No secrets:** credentials come from environment variables / Streamlit Secrets
  only; the public demo runs keyless.
