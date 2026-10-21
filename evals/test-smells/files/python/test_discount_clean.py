from datetime import date
from unittest.mock import Mock

import pytest

from discount import AuditLog, Customer, RateRefresher, apply_discount, loyalty_rate

TODAY = date(2024, 3, 15)


@pytest.mark.parametrize(
    ("years", "rate"),
    [(0, 0.0), (1, 0.0), (2, 0.10), (4, 0.10), (5, 0.15), (30, 0.15)],
    ids=["new", "one-year", "silver-lower", "silver-upper", "gold-lower", "gold-long"],
)
def test_loyalty_rate_by_tier(years, rate):
    assert loyalty_rate(Customer("ann", years)) == rate


def test_negative_loyalty_is_rejected():
    with pytest.raises(ValueError, match="non-negative"):
        loyalty_rate(Customer("bob", -1))


def test_negative_amount_is_rejected():
    with pytest.raises(ValueError, match="non-negative"):
        apply_discount(-1, Customer("cy", 1), today=TODAY)


def test_gold_customer_pays_85_percent():
    assert apply_discount(200, Customer("dee", 5), today=TODAY) == 170.0


def test_birthday_adds_five_percent():
    customer = Customer("eve", 0, birthday=date(1990, 3, 15))
    assert apply_discount(100, customer, today=TODAY) == 95.0


def test_discount_never_exceeds_amount():
    customers = [Customer(f"c{i}", i) for i in range(10)]
    results = [apply_discount(50, c, today=TODAY) for c in customers]
    assert all(0 <= r <= 50 for r in results)


def test_refresher_fetches_rates_once():
    fetch = Mock(return_value={"EUR": 1.1})
    refresher = RateRefresher(fetch)
    refresher.start()
    refresher.join(timeout=5)
    assert refresher.rates == {"EUR": 1.1}
    fetch.assert_called_once()


def test_audit_log_keeps_entries_in_order():
    log = AuditLog()
    log.record("first")
    log.record("second")
    assert log.entries == ["first", "second"]


@pytest.mark.xfail(strict=True, reason="float rounding: 2.675 rounds down, issue #42")
def test_half_cent_rounds_up():
    assert apply_discount(2.675, Customer("fay", 0), today=TODAY) == 2.68
