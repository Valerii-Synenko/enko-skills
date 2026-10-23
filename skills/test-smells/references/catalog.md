# Test Smell Catalog

Each entry: why it hurts, how to spot it, how to fix it, and when the pattern is **not** a smell. Examples alternate between languages; the ideas apply everywhere. Whether a pattern is a smell often depends on the test level (unit, integration, API, E2E): see [test-levels.md](test-levels.md).

## Contents

- Tests that can lie: [Empty Test](#empty-test) · [Unknown Test](#unknown-test) · [Weak Assertion](#weak-assertion) · [Redundant Assertion](#redundant-assertion) · [Conditional Test Logic](#conditional-test-logic) · [Exception Handling](#exception-handling) · [Ignored Test](#ignored-test) · [Tautological Test](#tautological-test)
- Tests that fail randomly: [Sleepy Test](#sleepy-test) · [Mystery Guest](#mystery-guest) · [Resource Optimism](#resource-optimism) · [Order-Dependent Tests](#order-dependent-tests) · [Nondeterministic Input](#nondeterministic-input)
- Hard to understand or maintain: [Assertion Roulette](#assertion-roulette) · [Eager Test](#eager-test) · [General Fixture](#general-fixture) · [Over-Mocking](#over-mocking) · [Implementation-Coupled Test](#implementation-coupled-test) · [Sensitive Equality](#sensitive-equality) · [Magic Number Test](#magic-number-test) · [Obscure Test](#obscure-test)
- Noise: [Redundant Print](#redundant-print) · [Duplicate Assert](#duplicate-assert) · [Constructor Initialization](#constructor-initialization) · [Lazy Test](#lazy-test) · [Placeholder Test](#placeholder-test)

---

## Tests that can lie

### Empty Test

**Why:** Always passes, shows up as green coverage, protects nothing.

**Signals:** Test body is empty, contains only comments, or only `pass` / `// TODO`.

**Fix:** Implement the test, or delete it. If it is a reminder, track it in an issue or mark it as an explicit pending/todo test (`it.todo`, `@pytest.mark.skip(reason=...)`).

**Not a smell:** Framework-required stubs that are explicitly marked as todo/pending.

### Unknown Test

**Why:** A test without an assertion only proves the code didn't crash. It will pass for most wrong results.

**Signals:** No `assert`/`expect`/`assertEquals`, no expected-exception check, no mock verification.

```python
# Smell
def test_parse_config():
    parse_config("app.toml")

# Fix
def test_parse_config_reads_port():
    config = parse_config(FIXTURE_PATH)
    assert config.port == 8080
```

**Not a smell:** Smoke tests whose stated purpose is "does not raise", when that is made explicit (name like `test_..._does_not_raise`, or a comment). Assertions hidden in a well-named helper (`assert_valid_response(resp)`) also count as assertions.

### Weak Assertion

**Why:** The test asserts something, but so little that almost any wrong result passes. It looks covered and catches nothing that matters.

**Signals:** `assert result`, `assert x is not None`, `assertNotNull(x)`, `expect(x).toBeTruthy()` / `toBeDefined()`, `len(items) > 0`, `assertTrue(list.size() > 0)`, type-only checks (`isinstance`), wildcard matchers (`ANY`, `expect.anything()`, `any()`) on values that matter.

```javascript
// Smell
test("creates an order", async () => {
  const order = await createOrder(cart);
  expect(order).toBeDefined();
  expect(order.items.length).toBeGreaterThan(0);
});

// Fix
test("creates an order with the cart items and total", async () => {
  const order = await createOrder(cart);
  expect(order).toMatchObject({ items: [{ sku: "MUG-42", qty: 2 }], total: 40 });
});
```

**Fix:** Assert the specific expected value. If part of the value is unstable, assert the stable parts precisely and match only the volatile fields loosely.

**Not a smell:** A not-null check used as a guard before precise assertions in the same test; smoke tests explicitly named as such; wildcards on genuinely volatile fields (generated IDs, timestamps).

### Redundant Assertion

**Why:** The assertion cannot fail (or cannot pass), so it tests nothing.

**Signals:** `assert x == x`, `assertTrue(true)`, `expect(1).toBe(1)`, comparing an object to itself, asserting a mock returns the value you just configured it to return.

**Fix:** Assert the result of the code under test against an independently known value.

**Not a smell:** None. Even `assertTrue(true)` used as a "reached this line" marker should be replaced with an assertion on actual state.

### Conditional Test Logic

**Why:** Branches in a test mean some assertions may never run, and the test itself now needs testing. A loop over cases hides which case failed.

**Signals:** `if`, `else`, `switch`/`match`, `for`/`while`, ternaries or early `return` in a test body that control what is asserted.

```javascript
// Smell
test("discounts", () => {
  for (const [qty, expected] of cases) {
    if (qty > 0) expect(discount(qty)).toBe(expected);
  }
});

// Fix
test.each(cases)("discount(%i) is %f", (qty, expected) => {
  expect(discount(qty)).toBe(expected);
});
```

**Not a smell:** Loops that only build input data (e.g. creating 100 items) with assertions outside the loop. Conditionals in shared test helpers that are themselves simple and well-named.

### Exception Handling

**Why:** Hand-written `try/catch` in tests either swallows unexpected exceptions (test passes when it shouldn't) or forgets to fail when no exception is thrown.

**Signals:** `try/catch`/`try/except` in the test body; `catch` blocks with `assert` inside; `fail()` after the call; `throw` in tests.

```java
// Smell
@Test void rejectsNegative() {
    try {
        account.withdraw(-5);
    } catch (IllegalArgumentException e) {
        assertEquals("amount must be positive", e.getMessage());
    }
}   // passes if nothing is thrown!

// Fix
@Test void rejectsNegative() {
    var e = assertThrows(IllegalArgumentException.class, () -> account.withdraw(-5));
    assertEquals("amount must be positive", e.getMessage());
}
```

**Not a smell:** Cleanup in `finally` when the framework has no better hook; letting a checked exception propagate via `throws Exception` on the test signature.

### Ignored Test

**Why:** Disabled tests rot. Nobody remembers why they were turned off, and the code they guarded is unprotected.

**Signals:** `@Ignore`, `@Disabled`, `@pytest.mark.skip`, `it.skip`, `xit`, `#[ignore]`, `t.Skip()`, commented-out tests — without a reason or tracking link.

**Fix:** Fix and re-enable, delete, or add a reason and an issue link. Prefer conditional skips (`skipif`, `assumeTrue`) for platform-specific tests.

**Not a smell:** Skips with a clear condition and reason (`skipif(sys.platform == "win32", reason="uses fork")`); `#[ignore]` for slow tests that run in a separate CI job; expected-failure markers with a linked bug.

### Tautological Test

**Why:** The expected value is computed with the same logic (or the same function) as the code under test, so a bug in the logic is reproduced in the expectation and the test still passes.

**Signals:** The expected value is calculated by calling the function under test, a copy of its algorithm, or a mock configured with the same output; snapshot tests accepted without review.

```python
# Smell
def test_tax():
    assert calculate_tax(100) == 100 * TAX_RATE   # same formula as the implementation

# Fix
def test_tax_is_20_percent():
    assert calculate_tax(100) == 20
```

**Not a smell:** Property-based tests and oracle tests that compare against a *different*, trusted implementation (e.g. a slow reference implementation, a standard library function).

---

## Tests that fail randomly

### Sleepy Test

**Why:** Fixed sleeps are either too short (flaky on a slow CI machine) or too long (slow suite). Usually both, at different times.

**Signals:** `time.sleep`, `Thread.sleep`, `setTimeout` in tests, `await sleep(...)`, `std::thread::sleep`, `time.Sleep`.

**Fix:** Await the operation directly; poll for a condition with a timeout; use fake timers/clocks (`jest.useFakeTimers`, `freezegun`, `tokio::time::pause`); inject a clock.

```typescript
// Smell
test("debounced search fires once", async () => {
  search.type("cat");
  await new Promise((r) => setTimeout(r, 500));
  expect(api.search).toHaveBeenCalledTimes(1);
});

// Fix
test("debounced search fires once", () => {
  vi.useFakeTimers();
  search.type("cat");
  vi.advanceTimersByTime(300);
  expect(api.search).toHaveBeenCalledTimes(1);
});
```

**Not a smell:** Tests of timing behavior itself when no fake clock is available, with a generous margin and a comment explaining why.

### Mystery Guest

**Why:** The test depends on something outside it — a file on disk, a database row, an env var, a remote service. A reader cannot see the input, and the test breaks when the environment changes.

**Signals:** Hard-coded paths (`/tmp/data.csv`, `../fixtures/big.json` with no visible link to the assertion), real DB/HTTP connections, `os.environ[...]` reads, tests that only pass on one machine.

**Fix:** Create the input inside the test (inline data, temp dir/file fixtures), or use a clearly named fixture file kept next to the test with the relevant values visible in the assertion. Use fakes or local test containers for databases and services.

```python
# Smell
def test_import_counts_rows():
    result = import_csv("/home/dev/data/customers.csv")
    assert result.imported == 3          # why 3? what is in the file?

# Fix
def test_import_counts_rows(tmp_path):
    csv = tmp_path / "customers.csv"
    csv.write_text("name,email\nAnn,a@x.io\nBob,b@x.io\nCyd,c@x.io\n")
    result = import_csv(csv)
    assert result.imported == 3
```

**Not a smell:** Integration tests whose purpose is to exercise the real resource, when they set up and tear down that resource themselves and are marked/isolated as integration tests. Golden files that are versioned with the test.

### Resource Optimism

**Why:** The test assumes a resource (file, directory, port, DB schema, running service) exists and is in a particular state. Works locally, fails in CI or on a fresh checkout.

**Signals:** Opening files that the test did not create; assuming a port is free; assuming tables or seed data exist.

**Fix:** Create the resource in setup (temp dirs, ephemeral ports, migrations in the fixture) and clean it up after.

**Not a smell:** Resources guaranteed by the repository itself (fixture files committed next to the test).

### Order-Dependent Tests

**Why:** Tests share mutable state (globals, singletons, class-level fields, a shared DB, module-level caches). They pass in one order and fail in another, or fail only when run in parallel.

**Signals:** Module-level mutable variables modified in tests; `setUpClass`/`beforeAll` creating mutable state; tests that rely on data created by an earlier test; failures that disappear when running a single test.

**Fix:** Fresh state per test (`setUp`/`beforeEach`/function-scoped fixtures); reset singletons and caches; transaction rollback per test for DBs. Verify with random ordering (`pytest-randomly`, `--order random` in JUnit 5, `jest --randomize`).

```python
# Smell
registry = UserRegistry()                # module-level, shared by every test

def test_register_adds_user():
    registry.register("ann")
    assert registry.count() == 1

def test_registry_starts_empty():
    assert registry.count() == 0         # fails if the test above ran first

# Fix
@pytest.fixture
def registry():
    return UserRegistry()

def test_register_adds_user(registry):
    registry.register("ann")
    assert registry.count() == 1
```

**Not a smell:** Expensive *immutable* shared setup (e.g. loading a read-only model once per module).

### Nondeterministic Input

**Why:** Current time, random numbers, UUIDs, hash/dict ordering, locale and timezone change between runs, so assertions sometimes fail.

**Signals:** `datetime.now()`, `new Date()`, `Math.random()`, `uuid4()` in test inputs or expected values; comparing lists produced from sets/maps in order; date assertions near midnight or month end.

**Fix:** Inject a clock or freeze time; seed random generators; compare unordered collections as sets or sort them first; pin timezone/locale in the test.

```go
// Smell
func TestGreeting(t *testing.T) {
	if got := Greeting(); got != "Good morning" { // passes only when CI runs before noon
		t.Errorf("Greeting() = %q", got)
	}
}

// Fix
func TestGreetingBeforeNoon(t *testing.T) {
	at := time.Date(2024, 1, 1, 9, 0, 0, 0, time.UTC)
	if got := GreetingAt(at); got != "Good morning" {
		t.Errorf("GreetingAt(%v) = %q, want %q", at, got, "Good morning")
	}
}
```

**Not a smell:** Property-based/fuzz tests that use randomness on purpose and report the failing seed.

---

## Hard to understand or maintain

### Assertion Roulette

**Why:** When one of many unlabelled assertions fails, the failure message doesn't say which one or why. Debugging means reading the test line by line.

**Signals:** Many assertions in one test, especially on different objects or behaviors, with no messages; frameworks where the failure output does not show the expression (older JUnit `assertTrue`).

**Fix:** Split into focused tests; add assertion messages; replace a series of field assertions with one structured comparison (`assert result == Expected(...)`, `assertThat(obj).usingRecursiveComparison()`, `toEqual({...})`), which shows a diff on failure.

```java
// Smell
@Test void parsesOrder() {
    Order order = parser.parse(json);
    assertTrue(order.getId() == 7);
    assertTrue(order.getItems().size() == 2);
    assertTrue(order.isPaid());
}   // failure says "expected: <true> but was: <false>" — which one?

// Fix
@Test void parsesOrder() {
    Order order = parser.parse(json);
    assertThat(order).usingRecursiveComparison()
        .isEqualTo(new Order(7, List.of(apple, pear), Status.PAID));
}
```

**Not a smell:** Several assertions on *one* result in frameworks with expressive failure output (pytest assertion rewriting, Jest `expect`, AssertJ). Soft-assertion APIs (`assertAll`, `assertj SoftAssertions`) that report every failure.

### Eager Test

**Why:** A test that checks several behaviors stops at the first failure, hides the others, and has a vague name. When it fails, you don't know which behavior broke.

**Signals:** Test calls many different methods of the object under test with assertions in between; names like `test_user`, `testEverything`, `test_flow`; Act-Assert-Act-Assert pattern.

```python
# Smell
def test_cart():
    cart = Cart()
    cart.add(apple)
    assert cart.total == 1.0
    cart.remove(apple)
    assert cart.is_empty()
    cart.add(apple, qty=3)
    assert cart.total == 3.0

# Fix
def test_adding_item_increases_total(): ...
def test_removing_last_item_empties_cart(): ...
def test_total_multiplies_price_by_quantity(): ...
```

**Not a smell:** End-to-end or scenario tests whose stated purpose is to verify a workflow (name it as a scenario). Calling getters to inspect the result of a single action.

### General Fixture

**Why:** A shared setup creates everything any test might need. Each test only uses a part, so readers can't tell which setup matters, and setup is slower than necessary.

**Signals:** A large `setUp`/`beforeEach`/fixture where each test uses only a few of the fields; tests that override half of the shared setup.

**Fix:** Smaller fixtures composed per test; builder or factory helpers with sensible defaults (`make_user(age=17)`) so each test states only what matters.

**Not a smell:** Small shared setup that every test actually uses.

### Over-Mocking

**Why:** When everything is mocked, the test checks that the code calls the mocks you configured — not that it works. Refactors break the tests while real bugs slip through.

**Signals:** Mocking value objects, data classes or pure functions; mocking the class under test (partial mocks/spies on itself); more mock setup than assertions; mock returning mock returning mock; assertions only on `verify`/`assert_called_with`.

**Fix:** Mock only boundaries that are slow, nondeterministic or external (network, filesystem, clock, third-party APIs, message queues). Use real collaborators or simple in-memory fakes elsewhere. Assert on outcomes rather than on calls.

```python
# Smell
def test_checkout_total():
    item = Mock(price=10)                    # value object mocked
    cart = Mock(items=[item, item])
    pricing = Mock()
    pricing.total.return_value = 20
    assert Checkout(cart, pricing).total() == 20   # only proves the mock returns 20

# Fix
def test_checkout_total_sums_item_prices():
    cart = Cart([Item(price=10), Item(price=10)])
    assert Checkout(cart, Pricing()).total() == 20
```

**Choosing a test double.** Prefer them in this order: real object → fake → stub → mock.

| Double | What it is | Use it for |
|---|---|---|
| Dummy | Passed in but never used | Filling a required parameter the test does not care about |
| Stub | Returns canned answers | Controlling input the code reads from a boundary (an exchange-rate API returns `1.1`) |
| Fake | A working lightweight implementation (in-memory repository, fake clock, local SMTP sink) | Stateful collaborators; usually the best default for repositories and clocks |
| Spy / Mock | Records calls so the test can assert on them | Only when the call itself is the behavior under test |

A stub that is also asserted on (`stub.assert_called_with(...)` when the call is not the point) turns into a mock and couples the test to implementation.

**Not a smell:** Verifying a call to an external boundary *is* the behavior (e.g. "sends exactly one email", "publishes an event").

### Implementation-Coupled Test

**Why:** Tests that check *how* code works (private methods, internal call order, internal data structures) break on every refactor, even when behavior is unchanged. They discourage improving the code.

**Signals:** Accessing private/underscore members; reflection to read private fields; asserting call order between internal collaborators; asserting intermediate state that callers never see.

**Fix:** Test through the public interface and assert on observable results. If a private piece is complex enough to need its own tests, extract it into its own unit with a public interface.

```typescript
// Smell
test("applies coupon", () => {
  const cart = new Cart([{ price: 50 }]);
  const spy = vi.spyOn(cart as any, "recalculate");
  cart.applyCoupon("SAVE10");
  expect(spy).toHaveBeenCalled();
  expect((cart as any)._discounts).toHaveLength(1);
});

// Fix
test("SAVE10 takes 10% off the total", () => {
  const cart = new Cart([{ price: 50 }]);
  cart.applyCoupon("SAVE10");
  expect(cart.total).toBe(45);
});
```

**Not a smell:** Tests of a module's own internals deliberately placed next to it (e.g. Rust `#[cfg(test)] mod tests` testing a private helper) when those internals are a stable, meaningful unit.

### Sensitive Equality

**Why:** Comparing `toString()`/`repr()`/JSON output to check state couples the test to formatting. A cosmetic change to the string breaks the test; a real state bug that prints the same passes.

**Signals:** `assertEquals("User(name=Bob, age=3)", user.toString())`, `assert repr(obj) == ...`, `expect(JSON.stringify(x)).toBe(...)` used to check object state.

**Fix:** Compare fields, use the type's equality, or a structured/recursive comparison.

**Not a smell:** Tests whose subject *is* the string format (testing `__repr__`, a serializer, a formatter).

### Magic Number Test

**Why:** Unexplained literals make the reader guess where a value comes from and whether it matters.

**Signals:** `assert result == 86400`, `assertEquals(42, calc.run(7, 3))` where the relationship between input and output isn't obvious.

**Fix:** Named constants (`SECONDS_PER_DAY`), or inputs chosen so the expected value is self-explanatory, or a short comment showing the derivation.

**Not a smell:** Obvious small values (`0`, `1`, `len == 3` right after adding three items); values that are visible in the Arrange step of the same short test.

### Obscure Test

**Why:** A long test full of irrelevant details hides the relationship between input and expected output. Readers can't tell what the test is about.

**Signals:** Tests longer than a screen; lots of setup unrelated to the assertion; no clear Arrange-Act-Assert separation; vague names.

**Fix:** Extract irrelevant setup into well-named helpers/builders; keep only the values that matter visible in the test; name the test after the behavior.

**Not a smell:** Long tests where every line is relevant to the scenario (rare; double-check).

---

## Noise

### Redundant Print

**Why:** Print statements clutter output, are rarely read, and are leftovers from debugging.

**Signals:** `print(...)`, `console.log`, `System.out.println`, `println!`, `fmt.Println` in tests.

**Fix:** Remove. Put the information into assertion messages or use the framework's logging (`t.Log`, `caplog`) if it should appear on failure.

**Not a smell:** Framework logging that is only shown on failure (`t.Log` in Go).

### Duplicate Assert

**Why:** The same assertion twice in a test adds no information; often a copy-paste mistake that hid an intended different assertion.

**Signals:** Identical assertion with identical arguments appearing more than once in one test.

**Fix:** Remove the duplicate, or check whether a different assertion was intended. If it checks the same property before and after an action, split into two tests or make the intent explicit.

**Not a smell:** Re-asserting an invariant after an action that should not change it — but name the test accordingly.

### Constructor Initialization

**Why:** Test-class constructors bypass the framework's lifecycle; failures there produce confusing errors and the setup may be shared unexpectedly.

**Signals:** Test classes with constructors that set fields (JUnit, C#), `__init__` in `unittest.TestCase` subclasses.

**Fix:** Use the framework's setup hook (`@BeforeEach`, `setUp`, fixtures).

**Not a smell:** Frameworks where the constructor *is* the per-test setup (xUnit.net creates a new instance per test and recommends constructors).

### Lazy Test

**Why:** Several tests call the same method with almost identical setup and only a different value. Duplication makes adding cases tedious.

**Signals:** Copy-pasted tests that differ only in one or two literals.

**Fix:** Parametrize (`@pytest.mark.parametrize`, `@ParameterizedTest`, `test.each`, table-driven tests in Go).

**Not a smell:** Several tests of one method that check genuinely different behaviors (edge cases with different meaning, different error paths). Multiple tests per method is normal; only duplicated *structure* is the smell.

### Placeholder Test

**Why:** Generated example tests (`ExampleUnitTest`, `test_example`, `it("works")` from a template) test nothing real and add noise.

**Signals:** Template names and bodies such as `assertEquals(4, 2 + 2)`.

**Fix:** Delete.

**Not a smell:** None.

---

## Sources

Smell names follow established literature; definitions and examples here are original.

- A. van Deursen, L. Moonen, A. van den Bergh, G. Kok. *Refactoring Test Code.* XP 2001.
- G. Meszaros. *xUnit Test Patterns: Refactoring Test Code.* Addison-Wesley, 2007.
- A. Peruma et al. *tsDetect: An Open Source Test Smells Detection Tool.* ESEC/FSE 2020, and the catalog at https://testsmells.org.
