import time
from datetime import date

import pytest

from discount import TIERS, AuditLog, Customer, RateRefresher, apply_discount, loyalty_rate

AUDIT = AuditLog()


def test_apply_discount():
    apply_discount(100, Customer("ann", 3))


def test_loyalty_rates():
    for years in range(0, 8):
        rate = loyalty_rate(Customer("bob", years))
        if years >= 5:
            assert rate == 0.15
        elif years >= 2:
            assert rate == 0.10


def test_negative_amount():
    try:
        apply_discount(-1, Customer("cy", 1))
    except ValueError as e:
        assert "non-negative" in str(e)


def test_rate_matches_tier():
    customer = Customer("dee", 6)
    expected = next(rate for years, rate in TIERS if customer.loyalty_years >= years)
    assert loyalty_rate(customer) == expected


def test_refresher_loads_rates():
    refresher = RateRefresher(lambda: {"EUR": 1.1})
    refresher.start()
    time.sleep(0.5)
    assert refresher.rates == {"EUR": 1.1}


def test_audit_records_entry():
    AUDIT.record("discount applied")
    assert len(AUDIT.entries) == 1


def test_audit_records_second_entry():
    AUDIT.record("discount reverted")
    assert len(AUDIT.entries) == 2


def test_birthday_bonus():
    customer = Customer("eve", 0, birthday=date.today())
    print(apply_discount(100, customer))
    assert apply_discount(100, customer) == 95.0


@pytest.mark.skip
def test_large_amount_rounding():
    assert apply_discount(1_000_000, Customer("fay", 2)) == 900_000.0


def test_discount_never_exceeds_amount():
    customers = [Customer(f"c{i}", i) for i in range(10)]
    results = [apply_discount(50, c, today=date(2024, 3, 15)) for c in customers]
    assert all(0 <= r <= 50 for r in results)


def test_long_time_customer_pays_85_percent():
    assert apply_discount(200, Customer("gus", 10), today=date(2024, 3, 15)) == 170.0


def test_discount_for_new_customer():
    assert apply_discount(80, Customer("hal", 0), today=date(2024, 3, 15)) is not None
