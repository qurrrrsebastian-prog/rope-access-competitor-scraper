"""
Synthetic competitor generator. Author: Avatar Putra Sigit.

Produces 50 realistic rope-access / building-service competitor records and
writes them to ``data/competitor_data.csv``.

Columns: company_name, location, service_type, price_min, price_max,
contact, last_updated.

- Services : Pembersihan Kaca, Maintenance Gedung, Waterproofing, Rope Access, Sealant
- Locations: Jakarta, Tangerang, Bekasi, Depok, Bogor
- Prices   : Rp 15 jt - Rp 120 jt (stored in Rupiah; min < max)
- contact  : a company website URL (used for the "Visit" link + domain check)
- Reproducible via random seed=42.

Run with: ``python data/generate_competitors.py``
"""
from __future__ import annotations

import os
import random
from datetime import date, timedelta
from typing import Dict, List

import pandas as pd

BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))
OUT_PATH: str = os.path.join(BASE_DIR, "competitor_data.csv")

SERVICES: List[str] = [
    "Pembersihan Kaca",
    "Maintenance Gedung",
    "Waterproofing",
    "Rope Access",
    "Sealant",
]
LOCATIONS: List[str] = ["Jakarta", "Tangerang", "Bekasi", "Depok", "Bogor"]

PREFIXES: List[str] = ["PT", "CV", "PT", "CV", "PT"]
NAME_A: List[str] = [
    "Akses", "Bersih", "Tinggi", "Gedung", "Mega", "Prima", "Karya", "Sinar",
    "Mitra", "Cipta", "Jaya", "Anugerah", "Nusantara", "Citra", "Bangun",
]
NAME_B: List[str] = [
    "Abadi", "Sejahtera", "Mandiri", "Persada", "Utama", "Gemilang", "Lestari",
    "Sentosa", "Perkasa", "Makmur", "Indah", "Bersama",
]
SEED: int = 42


def _slug(name: str) -> str:
    """Turn a company name into a lowercase URL slug."""
    return "".join(ch for ch in name.lower() if ch.isalnum())


def generate_competitors(n: int = 50, seed: int = SEED) -> pd.DataFrame:
    """Generate ``n`` competitor records.

    Args:
        n: Number of records.
        seed: RNG seed for reproducibility.

    Returns:
        DataFrame with the 7 specified columns.
    """
    try:
        rng = random.Random(seed)
        today = date(2026, 6, 15)
        used_names: set = set()
        records: List[Dict[str, object]] = []

        while len(records) < n:
            name = f"{rng.choice(PREFIXES)} {rng.choice(NAME_A)} {rng.choice(NAME_B)}"
            if name in used_names:
                continue
            used_names.add(name)

            price_min = rng.randint(15, 110) * 1_000_000
            price_max = price_min + rng.randint(5, 30) * 1_000_000
            price_max = min(price_max, 120_000_000)
            slug = _slug(name)
            contact = f"https://www.{slug}.co.id"
            last_updated = (today - timedelta(days=rng.randint(0, 60))).strftime("%Y-%m-%d")

            records.append(
                {
                    "company_name": name,
                    "location": rng.choice(LOCATIONS),
                    "service_type": rng.choice(SERVICES),
                    "price_min": price_min,
                    "price_max": price_max,
                    "contact": contact,
                    "last_updated": last_updated,
                }
            )
        return pd.DataFrame(records)
    except Exception as exc:  # pragma: no cover - defensive
        print(f"[ERROR] Competitor generation failed: {exc}")
        return pd.DataFrame(
            columns=[
                "company_name", "location", "service_type",
                "price_min", "price_max", "contact", "last_updated",
            ]
        )


def main() -> None:
    """Generate and save the competitor dataset."""
    try:
        df = generate_competitors()
        if df.empty:
            raise SystemExit(1)
        os.makedirs(BASE_DIR, exist_ok=True)
        df.to_csv(OUT_PATH, index=False)
        print(f"[OK] Saved {len(df)} competitor records to {OUT_PATH}")
    except SystemExit:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        print(f"[ERROR] Failed to write competitor data: {exc}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
