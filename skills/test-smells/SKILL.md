---
name: test-smells
description: Detect and avoid test smells (anti-patterns in test code) such as Assertion Roulette, Eager Test, Mystery Guest, Sleepy Test, Conditional Test Logic, over-mocking and order-dependent tests. Use when reviewing, auditing or refactoring existing tests ("review my tests", "why are these tests flaky", "are these good tests", "clean up this test file"), and whenever writing new unit or integration tests in any language or framework (pytest, unittest, JUnit, Jest, Vitest, Go, Rust, etc.) so the new tests come out smell-free.
---

# Test Smells

A test smell is a pattern in test code that makes tests harder to understand, slower, flaky, or less able to catch bugs. Smells are signals, not hard rules: always weigh the context before reporting or "fixing" one.

This skill has two modes:

- **Review mode** — the user asks to review, audit or improve existing tests. Find smells, explain them, propose fixes.
- **Writing mode** — you are writing or changing tests. Apply the catalog silently while writing; do not produce a smell report unless asked.

## Catalog

Detailed definitions, detection signals, before/after examples and legitimate exceptions for every smell are in [references/catalog.md](references/catalog.md). Read the relevant entries before reporting a smell you are not certain about. Framework-specific signals (pytest, unittest, JUnit, Jest/Vitest, Go, Rust) are in [references/frameworks.md](references/frameworks.md). How verdicts change between unit, integration, API and E2E tests, plus smells specific to each level, is in [references/test-levels.md](references/test-levels.md).

Severity: **High** = the test can pass while the code is broken, or fails randomly. **Medium** = the test is hard to read, diagnose or maintain. **Low** = cosmetic or context-dependent.

### Tests that can lie (High)

| Smell | Signal | Fix |
|---|---|---|
| Empty Test | Test body has no executable statements | Implement it or delete it |
| Unknown Test | No assertion and no expected-exception check | Assert on the observable outcome |
| Redundant Assertion | Assertion that is always true/false (`assert x == x`, `assertTrue(true)`) | Assert against an independent expected value |
| Conditional Test Logic | `if`/`switch`/loops/ternaries deciding what gets asserted | Split into separate tests or parametrize |
| Exception Handling | `try/catch` in the test that swallows or manually checks exceptions | Use the framework's exception assertion |
| Ignored Test | Skipped/disabled test with no reason or tracking issue | Fix, delete, or add a reason + ticket |
| Tautological Test | Expected value is computed with the same logic as the code under test | Hard-code an independently derived expected value |

### Tests that fail randomly (High)

| Smell | Signal | Fix |
|---|---|---|
| Sleepy Test | `sleep` used to wait for async work or time to pass | Wait on a condition, use fake clocks, await properly |
| Mystery Guest | Depends on real files, DB, network, env vars not set up in the test | Create the resource in the test or use a fake/temp resource |
| Resource Optimism | Assumes an external resource exists or is in a given state | Create/verify the resource in setup |
| Order-Dependent Tests | Tests share mutable state; pass alone but fail together (or vice versa) | Fresh state per test; no shared mutable globals |
| Nondeterministic Input | Uses current time, random values, unordered collections without control | Inject clock/seed; sort or compare as sets |

### Tests that are hard to understand or maintain (Medium)

| Smell | Signal | Fix |
|---|---|---|
| Assertion Roulette | Many assertions with no messages; failure doesn't say which/why | Fewer assertions per test, descriptive messages, or one structured comparison |
| Eager Test | One test exercises several unrelated behaviors | One behavior per test |
| General Fixture | Shared setup builds much more than each test needs | Smaller, test-specific fixtures/builders |
| Over-Mocking | Mocks for everything, including simple value objects and the unit under test | Mock only slow/external boundaries; use real objects otherwise |
| Implementation-Coupled Test | Asserts on private methods, internal calls or call order instead of behavior | Assert on public, observable outcomes |
| Sensitive Equality | Compares `toString()`/`repr`/serialized output to check state | Compare fields or use proper equality |
| Magic Number Test | Unexplained literals in assertions | Named constants or self-explanatory values |
| Obscure Test | Long, noisy test; the cause→effect relationship is hidden | Arrange-Act-Assert, helpers for irrelevant detail |

### Noise (Low)

| Smell | Signal | Fix |
|---|---|---|
| Redundant Print | `print`/`console.log`/`println` in tests | Remove; rely on assertion messages |
| Duplicate Assert | Same assertion repeated in one test | Remove, or split into separate tests if checking different stages |
| Constructor Initialization | Test class constructor sets up state instead of the framework's setup hook | Use the setup hook/fixture |
| Lazy Test | Several tests call the same production method with near-identical setup | Consider parametrizing; often fine as-is |
| Placeholder Test | Generated example tests left in the codebase (`ExampleUnitTest`, `test_example`) | Delete |

## Review mode

1. **Scope.** Identify the test files in scope. If the user did not specify, ask or use the tests touched in the current diff. Note the language, framework and test level (unit, integration, API, E2E). For anything other than unit tests, read [references/test-levels.md](references/test-levels.md): a real database or a multi-step scenario can be correct there.
2. **Read the code under test too**, at least the parts being exercised. Many smells (Tautological Test, Implementation-Coupled Test, Over-Mocking) cannot be judged from the test alone.
3. **Scan by severity.** Look for High-severity smells first; they matter most.
4. **Check exceptions before reporting.** Each catalog entry lists cases where the pattern is legitimate (e.g. multiple assertions on one result object are fine; `sleep` in a test of a timeout may be intentional). Do not report those.
5. **Report** in the format below. Group repeated occurrences of the same smell instead of listing each one.
6. **Fix only if asked.** If the user asked to fix, apply fixes one smell at a time, keep behavior coverage the same or better, and run the tests afterward.

### Report format

```
## Test smell review: <scope>

**Summary:** <N> findings (<h> high, <m> medium, <l> low). <one sentence on overall test health>

### High
- **<Smell>** — `path/to/test_file.py:42` `test_name`
  <What is wrong here, concretely, in one or two sentences.>
  Fix: <specific change, with a short code snippet if useful>

### Medium
...

### Low
...

### Looks good
<Optional: one or two things the tests do well, so the user knows what to keep.>
```

Omit empty severity sections. If no smells are found, say so plainly; do not invent findings.

## Writing mode

When writing tests, follow these defaults so the result is smell-free:

- **One behavior per test**, named after that behavior (`test_rejects_expired_token`, not `test_token_2`).
- **Arrange-Act-Assert** structure; keep the Arrange step minimal and specific to this test.
- **Assert on observable outcomes** (return values, public state, emitted events, calls to external boundaries), never on private internals.
- **Hard-code expected values** derived independently from the implementation.
- **No branching or loops** in test bodies; use the framework's parametrization for multiple cases.
- **Use the framework's exception assertion** (`pytest.raises`, `assertThrows`, `expect(...).toThrow`).
- **Control nondeterminism**: inject clocks, seed randomness, use temp directories, avoid real network.
- **No `sleep`** to wait for async results; await, poll with a timeout, or use fake timers.
- **Mock at boundaries only** (network, filesystem, time, third-party services). Prefer real objects and simple fakes elsewhere (see "Choosing a test double" under Over-Mocking in the catalog).
- **Each test sets up its own state** and leaves none behind.
- **Assertion messages** when a test has several assertions that could fail independently.

If an existing test file you are extending already contains smells, follow these defaults for the new tests and mention the existing smells briefly at the end, without fixing them unless asked.
