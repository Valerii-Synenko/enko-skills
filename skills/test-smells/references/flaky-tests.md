# Diagnosing Flaky Tests

Use when a test is reported as flaky, intermittent, failing only on CI, or passing only locally. Reproduce first, then name the cause with evidence. Use this together with [catalog.md](catalog.md).

## 1. Reproduce

Run the test many times, with the same runner options CI uses (parallelism, random order, environment). Record the failure rate, e.g. "7 of 50 runs failed".

| Framework | Repeat | Random order / parallel |
|---|---|---|
| pytest | `pytest path::test_name --count=50 -x` (pytest-repeat) | `pytest -p randomly --randomly-seed=<seed>`; `-n auto` (xdist) vs `-n 0` |
| unittest | `for i in $(seq 50); do python -m unittest mod.Class.test \|\| break; done` | run the module alone vs. the full suite |
| JUnit 5 | `@RepeatedTest(50)` temporarily | `junit.jupiter.testmethod.order.default=org.junit.jupiter.api.MethodOrderer$Random`; `junit.jupiter.execution.parallel.enabled` |
| Jest | `for i in $(seq 50); do npx jest path -t "name" \|\| break; done` | `jest --randomize --seed=<seed>`; `--runInBand` vs default workers |
| Vitest | `test(..., { repeats: 50 })` temporarily | `vitest run --sequence.shuffle --sequence.seed=<seed>` |
| Go | `go test -run '^TestName$' -count=100` | `-shuffle=on` (prints the seed), `-race`, `-p 1` |
| Rust | `for i in $(seq 50); do cargo test name \|\| break; done` | default parallel vs `-- --test-threads=1` |
| Playwright | `npx playwright test file --repeat-each=30 --retries=0` | `--workers=1` vs default; `fullyParallel` |
| Cypress | wrap the test in `Cypress._.times(20, () => it(...))` temporarily | run the spec alone vs. the whole run |

If the test never fails locally after a reasonable number of runs, keep going with step 2 under CI-like conditions (CPU limits, parallel workers, CI environment variables) before concluding.

## 2. Narrow the cause

Change one condition at a time. Each experiment separates a class of causes.

| Experiment | If the outcome changes, suspect |
|---|---|
| Run the test alone vs. with the full suite | Order-Dependent Tests (shared globals, singletons, caches, DB rows) |
| Random order; then replay the failing seed | Order-Dependent Tests; the seed makes it reproducible |
| Serial vs. parallel workers | Shared resources: ports, temp files, DB rows, test accounts |
| Freeze time; run with `TZ=UTC` and `TZ=Pacific/Kiritimati`; near midnight or month end | Nondeterministic Input (clock, timezone, date math) |
| Fix random seeds | Nondeterministic Input (random, UUIDs, unordered collections) |
| Slow the machine (CPU limits, parallel load, `-race`) | Sleepy Test, race conditions, timeouts that are too tight |
| Disable or stub the network | Mystery Guest, Resource Optimism |
| Compare CI and local: env vars, locale, case-sensitive filesystem, container image, browser version | Mystery Guest, environment assumptions |

## 3. Report

- Reproduction rate before and after the fix (e.g. "7/50 → 0/200").
- The experiment that isolated the cause ("fails only when run after `test_audit_records_entry`").
- The smell name from the catalog and the concrete fix.

If nothing reproduced the failure, say so, list what was tried, and present the remaining suspects as hypotheses.

## Retries are not a fix

Retries (`--reruns`, Playwright `retries`, `@RetryingTest`, `jest.retryTimes`) hide flakiness and slow the suite. They are acceptable only as temporary quarantine with a tracking issue, never as the resolution.
