"""Generate a synthetic competitor pricing dataset for rope access services.

Simulates market intelligence on 5 Jakarta-area competitors across three
service lines (rope access, glass cleaning, building maintenance) with
realistic price bands, ratings, and review counts. Saved to
``data/competitors.csv``.
"""

from __future__ import annotations

import os
import random
from typing import Dict, List, Tuple

import pandas as pd

SEED: int = 42

COMPETITORS: List[Dict[str, str]] = [
    {"name": "RopePro Indonesia", "location": "Jakarta Selatan", "website": "https://ropepro.co.id"},
    {"name": "Altus Safety", "location": "Jakarta Pusat", "website": "https://altussafety.id"},
    {"name": "Jakarta Rope Access", "location": "Jakarta Barat", "website": "https://jakartaropeaccess.com"},
    {"name": "SkyClean Services", "location": "Jakarta Utara", "website": "https://skyclean.id"},
    {"name": "HighRise Maintenance", "location": "Tangerang", "website": "https://highrisemaintenance.co.id"},
]

# Price bands per service type in IDR (project-based).
SERVICE_PRICE_BANDS: Dict[str, Tuple[int, int]] = {
    "rope_access": (15_000_000, 45_000_000),
    "glass_cleaning": (8_000_000, 25_000_000),
    "maintenance": (20_000_000, 60_000_000),
}


def generate_offering(company: Dict[str, str], service_type: str) -> Dict[str, object]:
    """Generate one company-service offering row.

    Args:
        company: Competitor profile (name, location, website).
        service_type: One of the keys in ``SERVICE_PRICE_BANDS``.

    Returns:
        Dict with pricing, rating, and review data for the offering.
    """
    try:
        band_min, band_max = SERVICE_PRICE_BANDS[service_type]
        price_min = random.randint(band_min, int((band_min + band_max) / 2))
        price_max = random.randint(price_min + 2_000_000, band_max)
        return {
            "company_name": company["name"],
            "service_type": service_type,
            "price_min": price_min,
            "price_max": price_max,
            "location": company["location"],
            "website": company["website"],
            "rating": round(random.uniform(3.5, 4.9), 1),
            "review_count": random.randint(8, 250),
        }
    except (KeyError, ValueError) as exc:
        print(f"[WARN] Failed offering for {company.get('name')}/{service_type}: {exc}")
        return {}


def generate_dataset() -> pd.DataFrame:
    """Generate the full competitor dataset (5 companies x 3 services).

    Returns:
        Competitor offerings DataFrame.

    Raises:
        RuntimeError: If no valid rows could be generated.
    """
    try:
        random.seed(SEED)
        rows = [
            generate_offering(company, service)
            for company in COMPETITORS
            for service in SERVICE_PRICE_BANDS
        ]
        rows = [r for r in rows if r]
        if not rows:
            raise RuntimeError("No valid competitor rows were generated.")
        return pd.DataFrame(rows)
    except Exception as exc:
        raise RuntimeError(f"Dataset generation failed: {exc}") from exc


def main() -> None:
    """Generate the dataset and save it next to this script."""
    try:
        df = generate_dataset()
        out_dir = os.path.dirname(os.path.abspath(__file__))
        out_path = os.path.join(out_dir, "competitors.csv")
        df.to_csv(out_path, index=False)
        print(f"[OK] Generated {len(df)} competitor offerings -> {out_path}")
        print(df.to_string(index=False))
    except (OSError, RuntimeError) as exc:
        print(f"[ERROR] {exc}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
