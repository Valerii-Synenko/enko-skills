# enko-skills

A collection of [Agent Skills](https://agentskills.io) — portable `SKILL.md` instructions that extend AI coding agents.

## Skills

| Skill | Description |
|-------|-------------|
| [test-smells](skills/test-smells/) | Detects and avoids test smells (Assertion Roulette, Eager Test, Mystery Guest, Sleepy Test, over-mocking, flaky order-dependent tests, …) when reviewing or writing tests in any language. |

## Installation

### Claude Code

```
/plugin marketplace add Valerii-Synenko/enko-skills
/plugin install enko-skills@enko-skills
```

### Other agents (Codex, Cursor, Copilot, Gemini CLI, ...)

Skills follow the open Agent Skills format. Copy the folder of the skill you want from [`skills/`](skills/) into your agent's skills directory.

## Evals

Test cases for each skill live in [`evals/<skill-name>/`](evals/), outside the skill folders, so installing a skill does not copy them. Each `evals.json` lists prompts with expectations; fixture files are under `files/`. Paths in the prompts are relative to the repository root.

## License

MIT
