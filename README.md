# enko-skills

A collection of [Agent Skills](https://agentskills.io) — portable `SKILL.md` instructions that extend AI coding agents.

## Skills

| Skill | Description |
|-------|-------------|
| [test-smells](skills/test-smells/) | Finds and avoids test smells (Sleepy Test, Mystery Guest, Assertion Roulette, over-mocking, order-dependent tests, …) when reviewing or writing tests in any language. Written from a test-automation perspective: knows what changes between unit, integration, API and E2E tests (brittle selectors, UI-driven setup, status-only API checks) and how to pick the right test double. Diagnoses flaky tests by reproducing them, and checks that fixed tests still fail when the code breaks. |

### Example: test-smells

Given this pytest file:

```python
AUDIT = AuditLog()

def test_refresher_loads_rates():
    refresher = RateRefresher(lambda: {"EUR": 1.1})
    refresher.start()
    time.sleep(0.5)
    assert refresher.rates == {"EUR": 1.1}

def test_audit_records_second_entry():
    AUDIT.record("discount reverted")
    assert len(AUDIT.entries) == 2

def test_discount_for_new_customer():
    assert apply_discount(80, Customer("hal", 0)) is not None
```

"Review these tests" produces a report along these lines:

> **Verdict:** The tests run, but two of them depend on timing and test order, and one passes for almost any result.
>
> | Severity | Smell | Where | Evidence | Fix |
> |---|---|---|---|---|
> | High | Sleepy Test | `test_refresher_loads_rates` | `time.sleep(0.5)` before the assertion; fails when the thread takes longer | `refresher.join(timeout=5)` |
> | High | Order-Dependent Tests | `test_audit_records_second_entry` | expects 2 entries in the module-level `AUDIT`; fails when run alone | fresh `AuditLog()` per test |
> | High | Weak Assertion | `test_discount_for_new_customer` | `is not None` passes for any number | `== 80.0` |

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

## Development

`python scripts/validate_skills.py` checks skill frontmatter, plugin manifests, Markdown links and eval files. CI runs it on every push and pull request, together with the eval fixtures. Changes are listed in [CHANGELOG.md](CHANGELOG.md); bump `version` in [`.claude-plugin/plugin.json`](.claude-plugin/plugin.json) with every release so installed plugins pick up the update.

## License

MIT
