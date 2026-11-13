# Install Reword 0.5.1

Reword is a folder-based agent skill. It needs a host that can read its files,
run Python 3.10+, and use a model for writing. Its Python helpers use the standard
library; no package installation, API key or separate Reword service is needed.
Your host's model access, permissions and normal data handling still apply.

Unzip `reword-0.5.1.zip` (or `reword-latest.zip`). Keep the complete `reword`
folder together: `SKILL.md`, scripts, references and assets are all needed.
Before replacing an existing installation, preserve any changes you made to it.
Keep personal voice stores outside this folder and outside public repositories.

## Claude Code

For local Claude Code, copy the extracted `reword` folder into
`~/.claude/skills/` for your user, or `.claude/skills/` inside a project.
The result must be `~/.claude/skills/reword/SKILL.md` (or its project equivalent).
Invoke it with `/reword Build my voice from these three samples`.

Personal local folders do not automatically make a skill available in Cowork or
cloud sessions. Follow the official host guidance for those environments.
Source: [Claude Code skills](https://code.claude.com/docs/en/skills).

## Codex CLI and IDE extension

Copy the extracted `reword` folder into `~/.agents/skills/` for your user, or
`.agents/skills/` inside a repository. The result must be
`~/.agents/skills/reword/SKILL.md` (or its project equivalent).
Use `/skills` to find it or invoke `$reword Build my voice from these three samples`.
Source: [OpenAI skill setup and discovery](https://learn.chatgpt.com/docs/build-skills).

## ChatGPT

Use a ChatGPT surface that offers standalone skills and a supported skill
installation flow. In the desktop app, open Skills; follow the import or creation
options available to your account, supplying the complete folder or ZIP when
the interface accepts it. Then select Reword with `@` and ask it to build your
voice. Availability and permitted uploads depend on the surface and workspace.
A ZIP attached to an ordinary chat is not proof of a persistent installation.
If your interface has no supported skill installer, use the local Codex or Claude
Code setup above. Full Reword functionality also needs Python execution and
durable private file storage in the host.
Source: [OpenAI skill support and invocation](https://learn.chatgpt.com/docs/build-skills).

## Verify and try it

From the extracted `reword` directory, run:

```bash
python3 scripts/reword.py --version
python3 scripts/reword.py voice onboard
python3 scripts/reword.py prompt draft.md --destination email
```

The version must be `0.5.1`. `draft.md` is a plain-text or Markdown draft you
supply. `prompt` returns a request for the host model; it does not rewrite the
file itself. On Windows, use your installed Python command if it differs.
Follow [the pilot guide](references/pilot.md) for a short real-use trial.

Installation references checked 2026-11-13. Host interfaces can change.
