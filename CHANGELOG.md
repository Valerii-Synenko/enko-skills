# Changelog

## 0.3.0 — 2026-10-23

### test-smells

- New Weak Assertion smell: `is not None`, `toBeTruthy`, `len > 0` and similar checks that pass for almost any result.
- New flaky-test mode with [references/flaky-tests.md](skills/test-smells/references/flaky-tests.md): reproduce with repeated runs, narrow the cause with targeted experiments, report the reproduction rate.
- Fixing now proves each changed test still catches bugs by temporarily breaking the production code.
- Playwright, Cypress and Selenium tables in [references/frameworks.md](skills/test-smells/references/frameworks.md).

### Repository

- `scripts/validate_skills.py` and a GitHub Actions workflow that runs it with the eval fixtures.
- Example report in the README.
- New evals for flaky-test diagnosis and fix verification.

## 0.2.0 — 2026-10-22

### test-smells

- Self-check before reporting: code evidence for every finding, no flakiness claims without running the tests.
- Report format depends on scope: a verdict and one table for small reviews, counts and a "Fix first" list for suites.
- Skill description mentions API and E2E/UI tests so the skill triggers for them.

## 0.1.0 — 2026-10-21

- First release with the `test-smells` skill: smell catalog with examples, framework-specific signals, guidance for unit, integration, API and E2E tests, and evals.
