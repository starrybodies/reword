# Agent readers

Use the `agent` destination when the reader is a model that will act on the text. That covers a prompt, a task brief, a handoff to a subagent, a ticket an agent will pick up, and standing instructions such as a system prompt or an `AGENTS.md` rule. Writing about agents for human readers keeps its ordinary destination.

```bash
python3 scripts/reword.py prompt ask.md --destination agent
python3 scripts/reword.py check ask.md brief.md --destination agent
```

## What changes

The [agent kernel](../assets/agent_kernel.txt) replaces the voice and editorial kernels. It asks for the outcome first, then the context the agent cannot discover, the limits on scope and permission, and the done condition when the source gives one. It cuts greetings, thanks, empty hedges, emphasis by capitals or repetition, and anything a capable agent already knows.

Reword leaves the author's prose voice out. Traits, sample habits and samples never enter an agent request, because a model reader gains nothing from them. Explicit preferences, avoid entries and phrase locks still apply, including general ones.

The rewrite adds nothing. The host reports a missing goal, scope or done condition to the author outside the rewritten text and never fills the gap with an invented requirement.

Compression comes from cutting content that changes nothing. Telegraphic wording that drops the grammar carrying who does what, in what order and under which condition saves few tokens and risks a wrong action.

## Checking a rewrite

`check` compares the candidate with its source differently for this destination. A path, command, code span, URL, quotation, number, quantity, date or lock counts as kept when at least one mention survives, because a brief states each thing once. Losing every mention blocks the result. So does a literal or number the source never contained. Putting an existing literal in backticks, or removing them, is not counted as a change.

The result carries an `efficiency` object with characters and estimated tokens for both texts, the tokens saved and the percentage. A candidate longer than its source is listed first under `review`, so each addition can be confirmed against the source.

## Preferences and named contexts

Record how the author likes agent text as explicit preferences. They apply to the next request without a learning pass.

```bash
python3 scripts/reword.py voice feedback STORE --kind preference --destination agent --prefer 'State the done condition last'
python3 scripts/reword.py voice feedback STORE --kind preference --destination agent/codex --avoid 'Role-play framing'
python3 scripts/reword.py prompt ask.md --destination agent/codex --voice STORE
```

A named context such as `agent/codex` or `agent/handoff` keeps preferences for one agent or one kind of brief. Agent destinations accept no writing samples and have no voice profile to refine, since text written for a model is not evidence of the author's prose voice. Corrections saved against an agent destination are kept as feedback and never wait on a refresh.

## Limits

Token counts are estimates of UTF-8 bytes divided by four. Pass an exact tokenizer through the Python API when a real count matters.

The checks are mechanical. They catch lost or invented literals and flag some changed relations, and they cannot confirm that every instruction survived. Read the candidate against the source before sending it.

No measurement here shows that an agent performs a task better from the rewritten text. The saving reported is in tokens only.
