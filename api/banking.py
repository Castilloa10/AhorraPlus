"""Local synthetic Enable Banking-shaped data. No network transport."""
import csv
from datetime import date
from decimal import Decimal, InvalidOperation
import io
import json
from pathlib import Path

from api.csv_import import preview

FIXTURE = Path(__file__).resolve().parents[1] / "samples" / "bank-simulation.json"


def normalize_page(page):
    if page.get("continuation_key"):
        raise ValueError("Faltan páginas de movimientos")
    if not isinstance(page.get("transactions"), list):
        raise ValueError("Falta la lista de movimientos")
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "fecha", "concepto", "importe"])
    skipped = 0
    for transaction in page["transactions"]:
        if transaction.get("status") != "BOOK":
            skipped += 1
            continue
        try:
            reference = transaction["entry_reference"]
            if not isinstance(reference, str) or not reference.strip():
                raise ValueError("Falta una referencia estable")
            booking_date = date.fromisoformat(transaction["booking_date"]).isoformat()
            amount_data = transaction["transaction_amount"]
            if amount_data["currency"] != "EUR":
                raise ValueError("La simulación admite EUR")
            amount = Decimal(amount_data["amount"])
            if not amount.is_finite() or amount < 0 or amount > 1000000000:
                raise ValueError("Importe no válido")
            if amount * 100 != (amount * 100).to_integral_value():
                raise ValueError("El importe tiene más de dos decimales")
            direction = transaction["credit_debit_indicator"]
            if direction not in ("DBIT", "CRDT"):
                raise ValueError("Falta el sentido del movimiento")
            if direction == "DBIT":
                amount = -amount
            lines = transaction.get("remittance_information") or ["Movimiento bancario ficticio"]
            if not isinstance(lines, list) or not all(isinstance(line, str) for line in lines):
                raise ValueError("Concepto no válido")
            writer.writerow(["bank-simulation:" + reference, booking_date, " ".join(lines), format(amount, ".2f")])
        except (KeyError, TypeError, InvalidOperation) as error:
            raise ValueError("Movimiento bancario incompleto o no válido") from error
    content = output.getvalue()
    _, errors = preview(content)
    if errors:
        raise ValueError("\n".join(errors))
    return {"content": content, "skipped": skipped, "demo": True}


def simulated_import():
    return normalize_page(json.loads(FIXTURE.read_text(encoding="utf-8")))
