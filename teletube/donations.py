"""Telegram Stars donation amounts and payment receipts."""

import sqlite3
from pathlib import Path


AMOUNTS = (25, 50, 100)
PAYLOAD_PREFIX = "teletube-donation-v1:"


def payload_for(amount: int) -> str:
    if amount not in AMOUNTS:
        raise ValueError("Unsupported donation amount")
    return f"{PAYLOAD_PREFIX}{amount}"


def amount_from(payload: str, currency: str, total_amount: int) -> int | None:
    for amount in AMOUNTS:
        if currency == "XTR" and payload == payload_for(amount) and total_amount == amount:
            return amount
    return None


class DonationReceipts:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(path, timeout=30) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS donation_receipt (
                telegram_payment_charge_id TEXT PRIMARY KEY,
                payer_id INTEGER NOT NULL,
                amount INTEGER NOT NULL,
                received_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )""")

    def record(self, charge_id: str, payer_id: int, amount: int) -> bool:
        if not charge_id or payer_id <= 0 or amount not in AMOUNTS:
            raise ValueError("Invalid donation receipt")
        with sqlite3.connect(self.path, timeout=30) as db:
            result = db.execute("""INSERT OR IGNORE INTO donation_receipt
                                   (telegram_payment_charge_id, payer_id, amount)
                                   VALUES (?, ?, ?)""", (charge_id, payer_id, amount))
            return result.rowcount == 1
