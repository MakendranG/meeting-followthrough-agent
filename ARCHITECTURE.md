# Architecture

![Meeting Follow-Through Agent architecture](./docs/architecture.png)

*(Rendered diagram: `docs/architecture.png` — upload this file to the Devpost
"Architecture diagram" field. Source: `docs/architecture.svg` / the Mermaid
below.)*

## The five elements (per the hackathon FAQ)

The diagram labels each element the judges' FAQ asks for:

1. **User input / interface** — a **CLI** (`main.py`) and a **Streamlit web app**
   (`app.py`); the user provides a Meeting 1 and a Meeting 2 transcript.
2. **Strands Agents (core + agentic loop)** — the `meeting_followthrough_agent`
   Strands agent runs the loop *model → tools → reasoning → response*, calling
   its two `@tool` functions and the drafting step until the report is complete.
3. **Tools & integrations** — the two custom tools (`extract_action_items`,
   `check_followthrough`) plus a local **JSON memory store** that persists
   Meeting 1's items across meetings.
4. **AWS services** — **Amazon Bedrock** (Claude, Sonnet 4 family) provides all
   the language reasoning inside the tools and the follow-up drafting.
5. **Output** — a final report: (a) Meeting 2's new action items, (b) the
   follow-through status table (DONE / IN_PROGRESS / NOT_MENTIONED), and
   (c) drafted follow-up messages for at-risk items.

The Meeting Follow-Through Agent is built with the **Strands Agents SDK** and
uses a **two-tool design** plus a small local **persistent-memory** layer. That
combination is what makes it more than a plain meeting summarizer: it doesn't
just extract action items from one meeting, it *remembers* them and *checks*, at
the next meeting, whether they were actually done.

## Diagram

```mermaid
flowchart TD
    M1["Meeting 1 transcript<br/>(sample_data/meeting_1_transcript.txt)"]
    M2["Meeting 2 transcript<br/>(sample_data/meeting_2_transcript.txt)"]

    A1["Tool A: extract_action_items<br/>(LLM reasoning)"]
    A2["Tool A: extract_action_items<br/>(LLM reasoning)"]
    B["Tool B: check_followthrough<br/>(LLM reasoning)"]

    MEM[("Persistent memory<br/>memory/meeting_1_action_items.json")]
    DRAFT["LLM drafting layer<br/>draft_followup_message"]

    OUT["Final Report<br/>(a) Meeting 2 new items<br/>(b) follow-through table<br/>(c) follow-up messages"]

    %% Meeting 1: extract then remember
    M1 --> A1 --> MEM

    %% Meeting 2: extract NEW items
    M2 --> A2 --> OUT

    %% Follow-through: compare stored memory against Meeting 2
    MEM --> B
    M2 --> B
    B --> OUT

    %% At-risk items get a drafted nudge
    B -->|NOT_MENTIONED / at risk| DRAFT --> OUT
```

## Flow explanation

Meeting 1's transcript is run through **Tool A (`extract_action_items`)**, and
the resulting structured commitments are written to a local JSON file that
simulates persistent memory across meetings. When Meeting 2 happens, Tool A runs
again to capture that meeting's **new** action items, while **Tool B
(`check_followthrough`)** loads Meeting 1's items back out of memory and compares
them against Meeting 2's transcript to decide whether each one is `DONE`,
`IN_PROGRESS`, or `NOT_MENTIONED` (at risk). Any at-risk item is passed to an
**LLM drafting layer** that writes a polite status-update nudge to the owner.
Both tools use the LLM (via the Strands SDK's Amazon Bedrock provider) for the
natural-language extraction and comparison reasoning — the deterministic Python
code only orchestrates the tools and formats the report. This memory-plus-
follow-through loop across two meetings is precisely what elevates the agent
above a one-shot transcript summarizer.
