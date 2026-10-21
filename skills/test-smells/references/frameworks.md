# Framework-Specific Signals

How common smells show up in popular frameworks, and the idiomatic fix. Use this together with [catalog.md](catalog.md).

## Python — pytest

| Smell | What to look for | Idiomatic fix |
|---|---|---|
| Exception Handling | `try/except` + `assert False` | `with pytest.raises(ValueError, match="..."):` |
| Conditional Test Logic / Lazy Test | loops over cases, copy-pasted tests | `@pytest.mark.parametrize` with `ids=` |
| Ignored Test | `@pytest.mark.skip` without `reason=` | `skipif(cond, reason=...)`, `xfail(reason=..., strict=True)` |
| Sleepy Test | `time.sleep`, `asyncio.sleep` | `await` directly; `freezegun`/`time-machine`; poll helpers |
| Mystery Guest / Resource Optimism | hard-coded paths, `os.environ` | `tmp_path`, `monkeypatch.setenv`, fixtures |
| Order-Dependent | `scope="module"`/`"session"` fixtures returning mutable objects; module globals | function-scoped fixtures; `pytest-randomly` to detect |
| Over-Mocking | `mock.patch` stacks of 4+, patching the module under test | patch at boundaries; `autospec=True`; fakes |
| General Fixture | one large `conftest.py` fixture used everywhere | small composable fixtures, factory fixtures |
| Redundant Print | `print` | assertion messages; `caplog`/`capsys` when output is the subject |
| Assertion Roulette | usually fine thanks to assertion rewriting; still split unrelated behaviors | compare whole objects/dataclasses |

## Python — unittest

| Smell | What to look for | Idiomatic fix |
|---|---|---|
| Exception Handling | `try/except` + `self.fail` | `with self.assertRaises(...)` / `assertRaisesRegex` |
| Assertion Roulette | many `assertTrue(a == b)` (no diff on failure) | specific asserts (`assertEqual`, `assertIn`) with `msg=` |
| Conditional Test Logic | loops over cases | `with self.subTest(case=...)` |
| Constructor Initialization | `__init__` in `TestCase` | `setUp` |
| Order-Dependent | mutable state in `setUpClass` | `setUp`; `addCleanup` |

## Java — JUnit 5 (+ AssertJ / Mockito)

| Smell | What to look for | Idiomatic fix |
|---|---|---|
| Exception Handling | `try/catch` + `fail()`; JUnit 4 `@Test(expected=...)` (too broad) | `assertThrows` and assert on the returned exception |
| Assertion Roulette | many `assertTrue`/`assertEquals` without messages | `assertAll(...)`, AssertJ `SoftAssertions`, `usingRecursiveComparison()` |
| Ignored Test | `@Disabled` without reason | `@Disabled("reason, JIRA-123")`, `@EnabledOnOs`, `assumeTrue` |
| Lazy Test / Conditional Logic | copy-paste, loops | `@ParameterizedTest` + `@CsvSource`/`@MethodSource` |
| Constructor Initialization | constructor sets fields | `@BeforeEach` |
| Sleepy Test | `Thread.sleep` | Awaitility `await().atMost(...).until(...)`; injected `Clock` |
| Over-Mocking | mocking value objects, `spy` on the class under test, `verify` only | real objects; mock ports/adapters only |
| Sensitive Equality | `assertEquals("...", obj.toString())` | field/recursive comparison |
| Order-Dependent | `static` mutable fields; `@TestMethodOrder` used to make tests pass | per-test state; `@TestInstance(PER_METHOD)` (default) |

## JavaScript / TypeScript — Jest, Vitest

| Smell | What to look for | Idiomatic fix |
|---|---|---|
| Exception Handling | `try/catch` with `expect` inside | `expect(() => fn()).toThrow(...)`; `await expect(p).rejects.toThrow(...)` |
| Unknown Test (async) | promise not awaited/returned, so assertions never run | `await` everything; `expect.assertions(n)` for callbacks |
| Conditional Test Logic / Lazy Test | loops, copy-paste | `test.each` / `it.each` |
| Ignored Test | `it.skip`, `xit`, `describe.skip`, `test.only` left in | remove `.only`; `it.todo`; skip with comment + issue |
| Sleepy Test | `setTimeout` promises, `waitForTimeout` | `jest.useFakeTimers()` / `vi.useFakeTimers()`; `waitFor(...)` |
| Over-Mocking | `jest.mock` of many modules, mocking the module under test | mock network (`msw`), not internals |
| Order-Dependent | module-level `let` mutated in tests; `beforeAll` with mutable state | `beforeEach`; `jest.resetModules()`; `restoreMocks: true` |
| Tautological | unreviewed `toMatchSnapshot` on large objects | small inline snapshots or explicit expectations |
| Redundant Print | `console.log` | remove |

## Go — testing

| Smell | What to look for | Idiomatic fix |
|---|---|---|
| Lazy Test / Conditional Logic | copy-pasted tests | table-driven tests with `t.Run(tc.name, ...)` |
| Assertion Roulette | `t.Error("failed")` without values | `t.Errorf("Parse(%q) = %v, want %v", in, got, want)`; `cmp.Diff` |
| Sleepy Test | `time.Sleep` | channels, `sync.WaitGroup`, injected clock, `testing/synctest` |
| Mystery Guest | hard-coded paths, `os.Getenv` | `t.TempDir()`, `t.Setenv()`, `testdata/` directory |
| Order-Dependent | package-level vars mutated in tests | per-test setup; `t.Cleanup`; run with `-shuffle=on` |
| Ignored Test | `t.Skip()` without reason | `t.Skip("reason")`; `testing.Short()` for slow tests |
| Redundant Print | `fmt.Println` | `t.Log` / `t.Logf` (shown only on failure or `-v`) |

## Rust — built-in tests

| Smell | What to look for | Idiomatic fix |
|---|---|---|
| Exception Handling | `match` on `Result` with `panic!` in arms | return `Result<(), E>` from the test and use `?`; `assert!(matches!(r, Err(Error::X)))` |
| Unknown Test | `#[should_panic]` without `expected` | `#[should_panic(expected = "message")]` |
| Ignored Test | `#[ignore]` without reason | `#[ignore = "reason"]`; run in a separate CI job |
| Assertion Roulette | `assert!(a == b)` (no values printed) | `assert_eq!(a, b, "context")`; `pretty_assertions` |
| Sleepy Test | `std::thread::sleep`, `tokio::time::sleep` | `tokio::time::pause()` + `advance`; channels |
| Mystery Guest | hard-coded paths | `tempfile` crate; `env!("CARGO_MANIFEST_DIR")` for committed fixtures |
| Lazy Test | copy-pasted tests | `rstest` `#[case]`, or a macro generating tests |
| Order-Dependent | `static` + `Mutex`/`OnceLock` with mutable state; env var mutation (tests run in parallel by default) | per-test state; `serial_test` only as a last resort |
| Redundant Print | `println!`/`dbg!` | remove (output is captured anyway) |
