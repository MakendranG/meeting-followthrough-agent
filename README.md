# Meeting Follow-Through Agent

*An "Agents for Humans" hackathon submission — Professional Agents track.*
**Built With: Strands Agents SDK.**

**Repository:** https://github.com/MakendranG/meeting-followthrough-agent

> **The action item you agreed to last week? Nobody checked if it got done.**
> This agent does. It reads a meeting, remembers who committed to what, and at
> the *next* meeting tells you exactly which promises were kept, which are still
> moving, and which quietly fell through — then drafts the nudge for you.

A professional AI agent that extracts the action items agreed on in a meeting,
*remembers* them, and then — at the **next** meeting — checks whether they were
actually done. For anything that quietly slipped, it drafts a polite follow-up
message to the person responsible. It's a lightweight follow-through system for
recurring meetings, not just another notes summarizer.

## Try it in one command

```bash
git clone https://github.com/MakendranG/meeting-followthrough-agent.git
cd meeting-followthrough-agent
AWS_REGION=us-east-1 ./demo.sh      # creates a venv, installs deps, runs the full demo
```
(Needs Python 3.10+ and AWS Bedrock credentials — see [Setup](#setup-from-a-cold-start).)

## The problem

After meetings, action items get agreed on verbally and then quietly evaporate —
not because people don't intend to do them, but because there's no lightweight
system that both **extracts** commitments from a meeting **AND checks**, at the
next meeting, whether they were actually done. Most tools only do the first half.

This agent deliberately goes **beyond simple meeting-notes summarization**. A
summarizer looks at one meeting in isolation. This agent has **memory** and
**follow-through over time**: it carries Meeting 1's commitments forward and
holds Meeting 2 accountable to them, surfacing the items that fell through the
cracks so a human can act on them.

## Who it's for — and why it matters

Managers, team leads, project coordinators, and scrum masters — **anyone running
recurring meetings** where the same group commits to work week after week.

For these people, the expensive failure isn't taking notes — it's the commitment
that silently dies between meetings. A dropped action item surfaces days or weeks
late, usually when something is already blocked or a deadline is already missed.
Today the only defense is a human manually cross-referencing last week's notes
against this week's discussion, every single week. This agent automates exactly
that cross-check and surfaces the at-risk items **before** they become fire
drills — turning "I thought someone was handling that" into a one-line status
you can act on immediately.

## How it works

The design is two connected Strands tools plus a small persistent-memory layer.
See [`ARCHITECTURE.md`](./ARCHITECTURE.md) for the full diagram and explanation.

- **Tool A — `extract_action_items(transcript_text)`**
  Parses one meeting transcript into a structured list of action items, each
  with a `description`, an `owner`, and a `deadline` (or `"unspecified"`).

- **Tool B — `check_followthrough(previous_action_items, current_transcript_text)`**
  Takes the **prior** meeting's action items and scans the **current** meeting's
  transcript for evidence, tagging each prior item `DONE`, `IN_PROGRESS`, or
  `NOT_MENTIONED` (treated as *at risk*).

Both tools use the LLM (through the Strands Agents SDK's Amazon Bedrock provider,
Claude Sonnet 4 family) for the natural-language extraction and comparison
reasoning. Meeting 1's extracted items are saved to
`memory/meeting_1_action_items.json` to simulate persistent memory between
meetings. A final LLM **drafting** step writes a friendly nudge for every
at-risk item. `main.py` orchestrates the whole flow and prints the report.

## Project layout

```
meeting-followthrough-agent/
├── agent.py                     # Strands agent + the two @tool functions + drafting
├── main.py                      # CLI entry point that runs the full flow
├── app.py                       # Streamlit web UI (live demo) over the same tools
├── demo.sh                      # one-command setup + run for judges
├── requirements.txt
├── .env.example                 # copy to .env and fill in (no secrets committed)
├── .gitignore
├── LICENSE                      # MIT
├── ARCHITECTURE.md              # Mermaid diagram + flow explanation
├── sample_data/
│   ├── meeting_1_transcript.txt # 4 action items, distinct owners
│   ├── meeting_2_transcript.txt # 2 done, 1 in progress, 1 never mentioned
│   └── demo_result.json         # real cached agent output → powers keyless Demo mode
├── scripts/
│   └── generate_demo_result.py  # regenerate demo_result.json from a live run
└── memory/                      # agent writes JSON here at runtime (git-ignored)
```

## Setup (from a cold start)

### Prerequisites
- **Python 3.10+**
- An **AWS account with Amazon Bedrock access** and a Claude Sonnet 4-family
  model enabled in your region
  ([enable model access](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access-modify.html)).

### 1. Install
```bash
git clone https://github.com/MakendranG/meeting-followthrough-agent.git
cd meeting-followthrough-agent
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure credentials (environment variables only — no secrets in code)
```bash
cp .env.example .env
# then edit .env with your AWS credentials + region
```
Any standard AWS credential source works: the `AWS_` env vars, `aws configure`,
an IAM role, or a Bedrock API key. At minimum set an AWS region that has Bedrock
access, e.g. `AWS_REGION=us-east-1`.

Optionally pin a specific model:
```bash
# defaults to us.anthropic.claude-sonnet-4-5-20250929-v1:0
export BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-5-20250929-v1:0
```

### 3. Run
```bash
python main.py
```
That runs the full flow against the bundled sample transcripts. To use your own:
```bash
python main.py --meeting1 path/to/earlier.txt --meeting2 path/to/later.txt
```

## Web UI (live demo)

Prefer a browser to a terminal? A Streamlit front-end (`app.py`) wraps the exact
same two Strands tools: paste two transcripts, click the button, and see the new
action items, the follow-through table, and the drafted nudges rendered live.

The app has **two modes**, and it auto-detects which to use:

- **Demo mode (default, keyless):** if no AWS credentials are present, the app
  shows a **real result previously generated by the live Strands + Amazon
  Bedrock agent** (cached in `sample_data/demo_result.json`). It makes **no AWS
  calls**, needs **no credentials**, costs nothing, and can't be abused — ideal
  for a public link.
- **Live mode:** if AWS credentials *are* configured, the app defaults to Live
  mode and runs the Strands agent against Amazon Bedrock for real. If a live run
  fails, it gracefully falls back to the cached demo result.

```bash
# from the project folder, with the venv active:
pip install -r requirements.txt

# keyless demo (no AWS needed):
streamlit run app.py

# live mode (uses your AWS Bedrock creds):
AWS_REGION=us-east-1 streamlit run app.py
```
Then open the URL Streamlit prints (default http://localhost:8501).

To regenerate the cached demo result after editing the transcripts:
```bash
AWS_REGION=us-east-1 python scripts/generate_demo_result.py
```

### Deploying a public live demo — no secrets required

Because the app defaults to keyless Demo mode, you can deploy it publicly with
**no AWS credentials at all**:

- **Streamlit Community Cloud (free, fastest):** go to <https://share.streamlit.io>,
  pick this repo, branch `main`, main file `app.py`, and **Deploy** — you can
  leave the Secrets box empty. The public app runs in keyless Demo mode.
- **Want the hosted app to run *live* on Bedrock?** Add AWS credentials as
  Streamlit **Secrets** (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`,
  `AWS_REGION`, optionally `BEDROCK_MODEL_ID`). The app then defaults to Live
  mode. Prefer a dedicated IAM user scoped to only `bedrock:InvokeModel*`.

> 💡 **Recommended:** keep the public link **keyless** (Demo mode) so it can
> never break or run up charges, and record your demo video running **Live mode
> locally** (where your AWS creds already work) so judges see the real Bedrock
> agent in action. Best of both.

> ⚠️ **Cost/security note:** in Live mode the agent calls Amazon Bedrock, which
> incurs per-request cost and needs credentials. A *public* Live deploy means
> every visitor's click spends against your AWS account. Never commit
> credentials — this repo keeps them in env vars / Streamlit Secrets only.

### Project landing page (GitHub Pages)

A static showcase page lives in [`docs/index.html`](./docs/index.html) — a
visual overview with the problem, the two-tool design, a sample follow-through
table, and buttons to the live demo / video / repo. To publish it:

1. Push this repo (done).
2. On GitHub: **Settings → Pages → Build and deployment → Source: Deploy from a
   branch**, then select **branch `main`, folder `/docs`**, and Save.
3. GitHub serves it at `https://MakendranG.github.io/meeting-followthrough-agent/`.
4. Edit the `#` placeholders in `docs/index.html` (`Launch live demo`,
   `Watch the video`) to point at your Streamlit URL and YouTube link.

> **Note:** GitHub Pages is *static hosting* — it presents the project and links
> out, but it can't run the Python agent or call Bedrock. The runnable live demo
> is the Streamlit app above; Pages is the polished front door to it.

### Is Amazon Bedrock AgentCore required? No.

Per the hackathon rules, deploying to **Bedrock AgentCore is optional** — it
"strengthens your Technical Implementation score, but it's not required." This
project runs on Amazon Bedrock today (via the Strands SDK's default provider).
AgentCore is a possible enhancement, not a prerequisite for a complete,
eligible submission.

## Sample output

Real console output from a run against the sample transcripts (abridged):

```
(a) MEETING 2 — NEW ACTION ITEMS
──────────────────────────────────────────────────────────────────────────────
  1. Wire up the empty-state designs
       Owner: Marcus       Deadline: this week
  2. Run the end-to-end QA pass on onboarding and log any bugs
       Owner: Marcus       Deadline: June 16
  3. Do the accessibility audit of the onboarding screens
       Owner: Dana         Deadline: June 18
  4. Compile the Q2 churn report
       Owner: Sam          Deadline: June 20

(b) FOLLOW-THROUGH ON MEETING 1'S ACTION ITEMS
──────────────────────────────────────────────────────────────────────────────
  OWNER      STATUS           ACTION ITEM
  --------------------------------------------------------------------------
  Marcus     ✅ DONE           Deploy rate limiting on the invite…
  Dana       ✅ DONE           Finalize empty-state designs and hand…
  Leo        ⚠️  NOT_MENTIONED Draft the launch blog post and send for…
  Sam        🔄 IN_PROGRESS    Build the conversion funnel dashboard
  --------------------------------------------------------------------------
  Summary: 2 done · 1 in progress · 1 at risk (not mentioned)

(c) DRAFTED FOLLOW-UP MESSAGES FOR AT-RISK ITEMS
──────────────────────────────────────────────────────────────────────────────

  ✉️  To Leo:
      Hi Leo! I wanted to check in on the launch blog post — I noticed we
      didn't get a chance to cover it in our last meeting. How's it coming
      along, and is there anything I can help with to move it forward?
```

The exact wording of extracted phrases and the drafted message will vary
slightly between runs because they are generated by the LLM.

## A note on the data

The transcripts in `sample_data/` are **synthetic sample data** created for this
demo. They contain **no real meeting content** and no real personal information.

## Built With

- **[Strands Agents SDK](https://strandsagents.com/)** (Python) — the agent
  framework and the `@tool` abstraction powering both custom tools.
- **Amazon Bedrock** (Claude Sonnet 4 family) — the default model provider.

## License

Released under the [MIT License](./LICENSE).
