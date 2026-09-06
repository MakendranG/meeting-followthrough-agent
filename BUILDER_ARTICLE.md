# Agents for Humans: I Built a Meeting Follow-Through Agent with the Strands Agents SDK and Amazon Bedrock

Meeting action items get agreed on out loud and then quietly evaporate. I built a Strands Agents SDK agent on Amazon Bedrock that extracts commitments from one meeting, remembers them, and checks the next meeting to see what actually got done — then drafts follow-up nudges for whatever slipped. Here's how it works and what I learned.

## The problem nobody builds for

Every recurring meeting ends the same way: people agree to do things, and then some of it quietly evaporates. Not because anyone is lazy — because there's no lightweight system that does **both** halves of the job:

1. **Extract** the commitments made in a meeting, and
2. **Check**, at the *next* meeting, whether they actually happened.

Most "meeting AI" tools only do the first half. They summarize one meeting in isolation and move on. The commitment that silently dies between meetings — the one that becomes a fire drill two weeks later — is exactly the one they don't catch.

So for the **Agents for Humans** hackathon (Professional Agents track), I built the **Meeting Follow-Through Agent**: an agent that has *memory and follow-through across meetings*.

## What it does

Give it two transcripts — an earlier meeting and a later one — and it produces:

- **Meeting 2's new action items** (owner + deadline each)
- A **follow-through report** on Meeting 1's items: `DONE`, `IN_PROGRESS`, or `NOT_MENTIONED` (treated as *at risk*)
- For every at-risk item, a **drafted, ready-to-send follow-up message** to the owner

Here's the follow-through table from the sample run:

| Owner | Status | Action item |
|-------|--------|-------------|
| Marcus | ✅ DONE | Deploy rate limiting on the invite endpoint |
| Dana | ✅ DONE | Finalize empty-state designs & hand off Figma |
| Leo | ⚠️ NOT_MENTIONED | Draft the launch blog post |
| Sam | 🔄 IN_PROGRESS | Build the conversion funnel dashboard |

**Summary: 2 done · 1 in progress · 1 at risk (not mentioned)**

Leo's blog post never came up in Meeting 2 — so the agent flags it and drafts the nudge automatically.

## The design: two Strands tools + memory

The whole thing is built with the [Strands Agents SDK](https://strandsagents.com/). What makes it more than a summarizer is a deliberate **two-tool design** plus a small persistent-memory layer.

**Tool A — `extract_action_items(transcript_text)`**
Parses one transcript into structured items: `description`, `owner`, `deadline` (or `"unspecified"`). It only keeps real commitments with a clear owner and drops anything explicitly parked.

**Tool B — `check_followthrough(previous_action_items, current_transcript_text)`**
Takes the *prior* meeting's items and scans the *current* transcript for evidence, tagging each `DONE` / `IN_PROGRESS` / `NOT_MENTIONED` — with a short evidence quote.

Both tools are plain Python functions decorated with `@tool`:

```python
from strands import Agent, tool

@tool
def extract_action_items(transcript_text: str) -> str:
    """Extract action items (description, owner, deadline) from a transcript."""
    ...

@tool
def check_followthrough(previous_action_items: str, current_transcript_text: str) -> str:
    """Tag each prior action item DONE / IN_PROGRESS / NOT_MENTIONED vs. the new transcript."""
    ...
```

Meeting 1's extracted items are written to a local JSON file that simulates memory between meetings — so Meeting 2 can be held accountable to Meeting 1's promises. That cross-meeting loop is the whole point.

## Where AWS comes in

The language reasoning inside both tools runs on **Amazon Bedrock**, via the Strands SDK's default Bedrock model provider using **Claude (Sonnet 4 family)**:

```python
MODEL_ID = os.environ.get(
    "BEDROCK_MODEL_ID",
    "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
)
```

Bedrock does the heavy lifting — understanding messy meeting dialogue, matching "I deployed it to production this morning" to the right prior commitment, and drafting a warm, non-accusatory nudge. Strands orchestrates the agent loop and tool calls; Bedrock provides the intelligence. Credentials are read from the environment only — there are no hardcoded secrets anywhere in the repo.

## Making it demo-friendly: keyless by default

I wanted anyone — including judges — to click a link and see it work, without me handing out AWS keys or funding everyone's tokens. So the Streamlit UI has two modes:

- **Demo mode (default, keyless):** if no AWS credentials are present, the app shows a *real, previously-generated* result (cached from a genuine Bedrock run). No credentials, no cost, nothing to break — perfect for a public link.
- **Live mode:** if credentials *are* configured, it runs the agent against Bedrock for real, with graceful fallback to the cached result.

There's also an optional "bring your own **temporary** STS credentials" panel so a curious user can run it live on their own AWS account — session-only, never stored. (A web app can't borrow your AWS Console session — browser cross-site isolation forbids it — so short-lived STS tokens are the practical, secure middle ground.)

## What I learned

- **Scope to one workflow, end-to-end.** A single thing that fully works ("did last week's commitments happen?") beats five half-features.
- **Put the LLM where judgment is needed, and keep everything else deterministic.** Bedrock handles the fuzzy language understanding; plain Python handles orchestration, storage, and formatting. That split makes the agent predictable and easy to debug.
- **`@tool` in Strands is genuinely low-friction.** A typed Python function with a good docstring *is* the tool — the SDK handles the rest of the agent loop.
- **Design your demo for zero-friction access.** Keyless demo mode turned "you need AWS to try this" into "just click the link."

## Try it

- **Live demo:** <https://meeting-followthrough-agent.streamlit.app/>
- **Project page:** <https://makendrang.github.io/meeting-followthrough-agent/>
- **Code (MIT):** <https://github.com/MakendranG/meeting-followthrough-agent>

Built with the Strands Agents SDK and Amazon Bedrock for the Agents for Humans hackathon. If you run recurring meetings, this is the teammate that quietly makes sure the things people promised actually get done.
