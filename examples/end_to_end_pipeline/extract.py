"""
Extract — Generate sample sales data for the end-to-end demo.

Creates a realistic-looking CSV of raw sales records that downstream
transform and load steps can consume.
"""

from __future__ import annotations

import csv
import logging
import random
from datetime import date, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(__file__).parent / "data"
OUTPUT_FILE = OUTPUT_DIR / "raw_sales.csv"

PRODUCTS = [
    ("P001", "Widget A", "Widgets", 9.99),
    ("P002", "Widget B", "Widgets", 14.99),
    ("P003", "Gadget X", "Gadgets", 29.99),
    ("P004", "Gadget Y", "Gadgets", 49.99),
    ("P005", "Doohickey", "Accessories", 4.99),
]

CUSTOMERS = [f"C{str(i).zfill(4)}" for i in range(1, 51)]
STORES = ["S01", "S02", "S03"]


def generate_sales(num_orders: int = 200, seed: int = 42) -> list[dict]:
    """Generate synthetic sales order data.

    Args:
        num_orders: Number of orders to generate.
        seed: Random seed for reproducibility.

    Returns:
        List of order-line dicts.
    """
    random.seed(seed)
    start_date = date(2025, 1, 1)
    rows: list[dict] = []
    order_num = 1000

    for _ in range(num_orders):
        order_num += 1
        order_id = f"ORD-{order_num}"
        order_date = start_date + timedelta(days=random.randint(0, 180))
        customer_id = random.choice(CUSTOMERS)
        store_id = random.choice(STORES)
        num_lines = random.randint(1, 4)

        for line in range(1, num_lines + 1):
            product = random.choice(PRODUCTS)
            qty = random.randint(1, 10)
            discount = round(random.uniform(0, qty * product[3] * 0.15), 2)
            tax = round((qty * product[3] - discount) * 0.08, 2)

            rows.append({
                "order_id": order_id,
                "line_item_number": line,
                "order_date": order_date.isoformat(),
                "customer_id": customer_id,
                "store_id": store_id,
                "product_id": product[0],
                "product_name": product[1],
                "category": product[2],
                "quantity": qty,
                "unit_price": product[3],
                "discount_amount": discount,
                "tax_amount": tax,
            })

    return rows


def write_csv(rows: list[dict], path: Path) -> None:
    """Write rows to a CSV file.

    Args:
        rows: List of dicts to write.
        path: Output file path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    logger.info("Wrote %d rows to %s", len(rows), path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    data = generate_sales()
    write_csv(data, OUTPUT_FILE)
    print(f"Sample data written to {OUTPUT_FILE}")
