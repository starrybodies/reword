---
name: reword
description: Learn the author's writing voice and make agent writing sound like them in any context. Build and evolve a saved voice profile from chosen writing samples, relevant copy, author revisions and explicit preferences. Fit each piece to its reader and occasion, with named contexts for recurring ones. Also tighten prompts, briefs and instructions written for AI agents so they cost fewer tokens and keep every instruction. Use for learning my voice, writing in my style, personalized drafting, humanizing, rewriting, voice matching, context-aware style, prose review, and writing or tightening a prompt for an agent.
---

# Reword: write in the author's voice

Reword learns the author's writing voice from samples they choose and, with
their consent, from their later corrections. It keeps a private voice profile
and applies it whenever the agent drafts or edits for the author, fitted to
where the text is going.

Run bundled commands from the directory containing this file. Use Python 3.10+;
the scripts use only the standard library and make no model or network calls.
The host agent's model performs writing and semantic voice distillation. Follow
[installation](INSTALL.md) for supported host setup.

For “Build my voice” or continuing voice learning, read [voice collections](references/voice-collection.md).
Offer [the invitation](assets/voice_onboarding.txt) once. Use only deliberately
supplied material; distinguish authored samples from reference inspiration.
Create a chosen private collection outside the skill and public project folders.
Establish ongoing consent once before automatically saving later corrections.

Select a collection with `--voice STORE`.
An explicitly configured `REWORD_VOICE` selects a default; `--no-voice` bypasses it.
For original drafting, export the selected voice card and apply it to the current
brief's facts. Style samples never supply biography, experiences or other claims.

For editing, use [voice_kernel.txt](assets/voice_kernel.txt) with author guidance,
otherwise [editorial_kernel.txt](assets/editorial_kernel.txt). Fit the destination
and current explicit preferences. Use one writing pass and one bounded source
comparison; avoid repeated polishing loops. Return finished copy by default.

Establish the situation before writing: who reads this, what they need from it,
how the author relates to them, and where it appears. The built-in destinations
only set channel defaults. Any other occasion takes the nearest destination plus
`--audience`, `--purpose` and `--context` stating the situation. A recurring
occasion takes a named context, written `DESTINATION/NAME` such as `chat/family`
or `web-copy/acme`. It keeps its own samples, preferences and learned traits
over its channel's. Reuse a name listed under `named_contexts` in the collection
status before coining one. Read [contexts](references/context.md).

When the reader is an AI agent, as with a prompt, a task brief, a handoff or
standing instructions, use `--destination agent`. The
[agent kernel](assets/agent_kernel.txt) replaces the voice kernels, the author's
prose voice is left out, and `check` reports the estimated tokens saved. Read
[agent readers](references/agents.md).

`python3 scripts/reword.py prompt FILE --destination DESTINATION` assembles the
method, compact voice, destination card and sparse examples. Send `instructions`
as host instructions and `input` as data; `meta` is bookkeeping. Keep the default
4,000-character guidance cap. Required preferences must fit or fail visibly;
never silently discard them. Normal edits never load the saved corpus.

Preserve the original. Run `python3 scripts/reword.py check ORIGINAL CANDIDATE
--destination DESTINATION` with the same voice and overrides before replacement.
Resolve blocking differences and assess review warnings. These heuristic checks
do not establish truth or complete semantic equivalence.

With ongoing consent, save actual author corrections and explicit preferences;
refresh eligible evidence in bounded batches. Acceptance alone does not make
model prose authored evidence. Offer inspection, export, pause, forget and
rollback controls when requested.

Load [commands](references/cli.md), [contexts](references/context.md),
[agent readers](references/agents.md), [guidance budgets](references/budget.md),
or [the editorial method](references/editorial.md) only when needed. For the
public author pilot, follow [try Reword in your own agent](references/pilot.md).
