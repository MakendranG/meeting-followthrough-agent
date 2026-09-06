# Meeting Follow-Through Agent

*An "Agents for Humans" hackathon submission — Professional Agents track.*
**Built With: Strands Agents SDK.**

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
├── demo.sh                      # one-command setup + run for judges
├── requirements.txt
├── .env.example                 # copy to .env and fill in (no secrets committed)
├── .gitignore
├── LICENSE                      # MIT
├── ARCHITECTURE.md              # Mermaid diagram + flow explanation
├── sample_data/
│   ├── meeting_1_transcript.txt # 4 action items, distinct owners
│   └── meeting_2_transcript.txt # 2 done, 1 in progress, 1 never mentioned
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
