from dataclasses import dataclass
from datetime import date
from calendar import monthrange


@dataclass(frozen=True)
class Commitment:
    name: str
    scheduled_on: date
    cents: int
    charged_on: date | None = None


def summarize(accounts, commitments, protected, as_of):
    end = as_of.replace(day=monthrange(as_of.year, as_of.month)[1])
    pending = sorted(
        (item for item in commitments
         if item.scheduled_on <= end
         and (item.charged_on is None or item.charged_on > as_of)),
        key=lambda item: item.scheduled_on,
    )
    balance = sum(account["cents"] for account in accounts)
    committed = sum(item.cents for item in pending)
    return {
        "demo": True,
        "as_of": as_of.isoformat(),
        "through": end.isoformat(),
        "balance_cents": balance,
        "committed_cents": committed,
        "protected_cents": protected,
        "available_cents": balance - committed - protected,
        "accounts": accounts,
        "payments": [
            {"name": item.name, "date": item.scheduled_on.isoformat(), "cents": item.cents}
            for item in pending
        ],
    }

