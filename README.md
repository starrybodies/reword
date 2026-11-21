# Reword

Reword is an open-source agent skill for Claude Code and Codex that learns your writing voice. Give it writing you choose, and it builds a compact voice profile your agent uses to draft and edit in your writing style. It fits each piece to its reader and occasion, whether that is an email, a group chat, a membership application, or web copy for one of your ventures, and it can learn from your revisions and stated preferences when you opt in. Reword also tightens the prompts and briefs you write for AI agents.

[Installation](INSTALL.md) · [Commands](references/cli.md) · [Website](https://reword.symbai.studio/)

## Install

```bash
npx skills add starrybodies/reword
```

The [skills CLI](https://skills.sh/starrybodies/reword) asks which agent to install for, and whether to install for you or for one project. It sends anonymous install telemetry to skills.sh (the skill name, its files, and a timestamp) unless you set `DISABLE_TELEMETRY=1`. Reword itself sends nothing anywhere.

Reword works with a host agent that can read skill files, run **Python 3.10+**, and save private files. The helpers use only the Python standard library. Your agent's model performs the writing and voice distillation; Reword does not train a model or call a separate writing service.

You can also clone the repository into your agent's skills folder:

| Host | Install | Invoke |
| --- | --- | --- |
| Claude Code | `git clone https://github.com/starrybodies/reword ~/.claude/skills/reword` | `/reword Build my voice` |
| Codex CLI or IDE | `git clone https://github.com/starrybodies/reword ~/.agents/skills/reword` | `$reword Build my voice` |
| ChatGPT with supported skills | Import the [repository ZIP](https://github.com/starrybodies/reword/archive/refs/heads/main.zip) through Skills | Select Reword with `@` |

To update, run `npx skills update`, or `git pull` in a cloned folder. See [INSTALL.md](INSTALL.md) for setup details and host limitations.

## Use it

Start with one to five pieces you wrote and deliberately choose to share:

> Build my voice from these three samples. Keep it in a private collection. Ask before enabling ongoing learning.

Then give it a draft or a factual brief and a destination:

> Rewrite this email using my saved voice. Put the request first and keep the dates and commitments unchanged.

> Draft a LinkedIn post from these notes using my saved voice. Use only the facts in the notes.

### Any context

The built-in destinations cover common channels such as email, chat, LinkedIn, and web copy. For anything else, tell your agent who reads the piece and what it is for:

> Write my answers for this membership application in my saved voice. A committee of practitioners reads it, and each answer has a 150-word limit.

When you write differently in places that share a channel, name each one. Reword keeps separate samples, preferences, and learned habits for every [named context](references/context.md#named-contexts):

> Save these messages as my family group chat voice, and these as my work chat voice.

> Rewrite this landing page in my Acme voice.

### Writing for agents

Reword also edits text meant for a model. It puts the outcome first, keeps every limit and condition, and cuts the words that change nothing about what the agent does. Reword leaves your prose voice out, because a model has no use for it.

> Turn these notes into a brief for a coding agent. Keep every path and command exact, and tell me if the done condition is missing.

The check reports the estimated tokens saved. It blocks a rewrite that drops or invents a path, a command, a number, or a quoted error. [Agent readers](references/agents.md) covers the method and its limits.

### Learning and your data

With your consent, later corrections can improve the guide. You can inspect, export, pause learning, forget evidence, or restore an earlier guide. [Voice collections](references/voice-collection.md) explains those controls.

Your samples and voice collection stay in the private location you choose, outside the skill and public repositories. Your host's usual model processing and data rules still apply. Keep reference inspiration separate from your authored work; sample facts are never facts for a new draft.

## Local tools

From this folder:

```bash
python3 scripts/reword.py --version
python3 scripts/reword.py prompt draft.md --destination email
python3 scripts/reword.py check original.md candidate.md --destination email
python3 scripts/reword.py prompt draft.md --destination chat/family --voice STORE
python3 scripts/reword.py check notes.md brief.md --destination agent
```

`prompt` assembles a request for your host model; it does not rewrite the file. `check` flags possible changes to protected content and claims. These checks are heuristics, so review the result against the source.

## Help build it

If Reword is useful, **star this repository**. **Fork it** to try a change, open an issue with a synthetic example, or send a pull request. [CONTRIBUTING.md](CONTRIBUTING.md) covers the small test suite and contribution workflow.

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

The tests cover local runtime behavior, consent, persistence, bounded guidance, and content checks. They do not measure writing quality or voice fidelity.

## Questions

### What is Reword?

Reword is an open-source agent skill from Symbai Studios that makes an AI agent write in your voice. It builds a saved voice profile from writing samples you choose, and your agent uses that profile when it drafts or edits for you. Reword runs inside Claude Code, Codex, and other hosts that support folder-based skills, and it is free under the MIT license.

### How is Reword different from a humanizer skill?

A humanizer skill such as [blader/humanizer](https://github.com/blader/humanizer) edits a text to remove known signs of AI-generated writing, and it can match a writing sample you paste in for that edit. Reword keeps a saved voice profile built from samples you choose, and it reuses that profile in later sessions. Reword can also update the profile from your corrections when you opt in. The two skills do different jobs, and you can install both.

### Does Reword learn from my corrections?

Reword learns from your corrections when you opt in. It asks once before it saves later corrections and stated preferences, and it uses them to update your voice profile. You can inspect what is saved, pause learning, forget a piece of evidence, or restore an earlier version of the profile.

### Where does Reword keep my writing samples and voice profile?

Reword keeps your samples and voice profile in a private location that you choose, outside the skill folder and outside public repositories. The Python helpers make no model or network calls, and the skill has no telemetry. Your host agent's model still processes the text you give it, so that host's data rules apply.

### Which agents does Reword work with?

Reword works with Claude Code and with the Codex CLI and IDE extension. It also works in ChatGPT surfaces that support installed skills. Any other host needs to read skill files, run Python 3.10 or later, and save private files.

### Can Reword write emails, LinkedIn posts, and text messages in my voice?

Reword fits each draft to its destination, such as an email, a text message, a LinkedIn post, or a cover letter. You name the destination when you ask, and Reword applies your saved voice in the form that destination expects. Reword uses only the facts in your brief, and a writing sample never supplies facts for a new draft.

Made by [Symbai Studios](https://symbai.studio/). Released under the [MIT license](LICENSE).
