import threading
from dataclasses import dataclass
from datetime import date

TIERS = [(5, 0.15), (2, 0.10), (0, 0.0)]


@dataclass(frozen=True)
class Customer:
    name: str
    loyalty_years: int
    birthday: date | None = None


def loyalty_rate(customer: Customer) -> float:
    if customer.loyalty_years < 0:
        raise ValueError("loyalty_years must be non-negative")
    for years, rate in TIERS:
        if customer.loyalty_years >= years:
            return rate
    return 0.0


def apply_discount(amount: float, customer: Customer, today: date | None = None) -> float:
    if amount < 0:
        raise ValueError("amount must be non-negative")
    rate = loyalty_rate(customer)
    today = today or date.today()
    if customer.birthday and (customer.birthday.month, customer.birthday.day) == (today.month, today.day):
        rate += 0.05
    return round(amount * (1 - rate), 2)


class AuditLog:
    def __init__(self):
        self.entries = []

    def record(self, entry: str) -> None:
        self.entries.append(entry)


class RateRefresher:
    """Loads exchange rates in a background thread."""

    def __init__(self, fetch):
        self._fetch = fetch
        self._thread = None
        self.rates = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run)
        self._thread.start()

    def join(self, timeout: float | None = None) -> None:
        self._thread.join(timeout)

    def _run(self) -> None:
        self.rates = self._fetch()
