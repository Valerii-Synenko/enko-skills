# Test Smells by Test Level

The same pattern can be a smell in a unit test and the whole point of an integration or E2E test. Decide the level first, then judge. Use this together with [catalog.md](catalog.md).

## Identifying the level

Judge by what the test actually touches, not only by the folder it lives in.

| Level | Typical signals |
|---|---|
| Unit | One module or class; no real I/O; runs in milliseconds; `tests/unit/`, `*_test.go` next to the code, `#[cfg(test)]` |
| Integration | Real database, filesystem, message broker or test container; several modules wired together; markers like `@pytest.mark.integration`, `@Tag("integration")`, `//go:build integration` |
| API | HTTP client against a running service (`TestClient`, `supertest`, `RestAssured`, `httpx`); asserts on status, headers and body |
| E2E / UI | Browser or device driver (Playwright, Cypress, Selenium, Appium); user-level actions like clicks and form fills |

If a test mixes levels (a "unit" test that opens a real DB connection), report that mismatch itself: it is usually a Mystery Guest or a misplaced test.

## Same pattern, different verdict

| Pattern | Unit | Integration | API | E2E |
|---|---|---|---|---|
| Real DB / filesystem | Smell (Mystery Guest) | Expected, if the test creates and cleans up its own data | Expected behind the service | Expected |
| Real third-party network (payments, email, SaaS APIs) | Smell | Smell; use a stub server or container | Smell; stub at the HTTP level | Stub, except in a dedicated smoke suite |
| Several act-assert steps | Smell (Eager Test) | Usually Eager Test | Fine for a named workflow (create → read → delete) | Normal: a user journey is a scenario |
| Mocks | Boundaries only | Mock only what is out of scope; mocking the integration being tested defeats the test | Never mock the service under test | Nothing internal; stub third parties at the network level |
| Fixed `sleep` | Smell | Smell; poll with timeout | Smell; poll async jobs for completion | The most common smell; use auto-waiting locators and condition waits |
| Data shared between tests | Smell | Smell; transaction rollback or unique data per test | Smell; unique IDs per test | Smell; each test seeds its own user, cart, order |
| Long test body | Usually Obscure Test | Often acceptable setup; extract builders | Acceptable if steps form one workflow | Acceptable if every step is part of the journey; extract page objects |
| Assertion on full output | Fine | Fine | Watch volatile fields (IDs, timestamps): ignore or match them | Smell if it is a full-page screenshot without masking dynamic regions |

## Smells specific to a level

### Integration

- **Unit test in disguise.** Called an integration test, but mocks the database or service it claims to integrate with. Either drop the mock or move the test to the unit suite.
- **Leftover data.** No cleanup, so the test passes only on a fresh database or fails on the second run. Use per-test transactions, unique keys, or truncate in teardown.

### API

- **Status-only assertion.** `assert resp.status_code == 200` and nothing else is a variant of Unknown Test: a wrong body still passes. Assert on the fields that matter.
- **Volatile-field equality.** Comparing the whole JSON body including `id`, `created_at` or request IDs causes Nondeterministic Input failures. Compare the stable fields, or use matchers (`ANY`, `expect.any(String)`).
- **Hard-coded environment.** Base URLs, tokens or tenant IDs inline in the test are a Mystery Guest. Take them from configuration set up by the suite.

### E2E / UI

- **Brittle selectors.** CSS paths (`form > div:nth-child(3) > button`), generated class names (`.css-1x9fz2k`) and XPath by position break on any layout change. Use roles, labels or dedicated test IDs (`getByRole`, `data-testid`).
- **Setup through the UI.** Logging in or creating data via the UI in every test is slow and makes unrelated tests fail when the login page breaks. Seed through the API or reuse a stored session (Playwright `storageState`, Cypress `cy.session`).
- **Fixed waits.** `waitForTimeout`, `cy.wait(3000)`, `Thread.sleep` in Selenium. Use web-first assertions that retry (`await expect(locator).toBeVisible()`) or explicit waits for a condition.
- **Pre-existing accounts.** Depending on a shared `qa@example.com` user that some environment happens to have is Resource Optimism, and tests running in parallel will clash on it. Create a user per test or per worker.
- **Wrong level.** Business rules (pricing tiers, validation matrices) checked through the browser are slow and fragile. Suggest moving the cases to unit tests and keeping one E2E path. Report this as a suggestion, not as a smell.
