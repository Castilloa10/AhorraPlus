import json
import sqlite3
from contextlib import closing
from datetime import date

from api.finance import Commitment, summarize


def demo_home(include_schedule=False):
    with closing(sqlite3.connect(":memory:")) as db:
        db.executescript("""
            CREATE TABLE accounts (name TEXT, cents INTEGER);
            CREATE TABLE commitments (name TEXT, scheduled_on TEXT, cents INTEGER, charged_on TEXT);
            CREATE TABLE reserves (name TEXT, cents INTEGER);
            INSERT INTO accounts VALUES ('Cuenta diaria', 246840), ('Cuenta de ahorro', 78000);
            INSERT INTO commitments VALUES
                ('Internet', '2026-11-10', 4490, '2026-11-11'),
                ('Alquiler', '2026-11-20', 75000, NULL),
                ('Seguro anual', '2026-11-25', 12990, NULL),
                ('Electricidad', '2026-11-28', 6240, NULL),
                ('Internet', '2026-12-10', 4490, NULL);
            INSERT INTO reserves VALUES ('Fondo de emergencia', 60000);
        """)
        accounts = [
            {"name": name, "cents": cents}
            for name, cents in db.execute("SELECT name, cents FROM accounts ORDER BY rowid")
        ]
        commitments = [
            Commitment(name, date.fromisoformat(scheduled), cents,
                       date.fromisoformat(charged) if charged else None)
            for name, scheduled, cents, charged in db.execute(
                "SELECT name, scheduled_on, cents, charged_on FROM commitments"
            )
        ]
        protected = db.execute("SELECT COALESCE(SUM(cents), 0) FROM reserves").fetchone()[0]
    result = summarize(accounts, commitments, protected, date(2026, 11, 14))
    if include_schedule:
        result["schedule"] = commitments
    return result


if __name__ == "__main__":
    print(json.dumps(demo_home(), ensure_ascii=True, indent=2))

