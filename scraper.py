"""Competitor pricing analysis for rope access services in Jakarta.

Loads competitor market data from ``data/competitors.csv`` and produces
two visualizations (average price per service, rating vs review count)
plus a console intelligence report: cheapest and most expensive player
per service, best-rated competitor, and the market price gap.

Run with: ``python scraper.py``
"""

from __future__ import annotations

import os
import subprocess
import sys
from typing import Optional

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))
DATA_PATH: str = os.path.join(BASE_DIR, "data", "competitors.csv")
GENERATOR_PATH: str = os.path.join(BASE_DIR, "data", "generator.py")

SERVICE_LABELS: dict = {
    "rope_access": "Rope Access",
    "glass_cleaning": "Glass Cleaning",
    "maintenance": "Maintenance",
}


def load_competitors() -> Optional[pd.DataFrame]:
    """Load the competitor dataset, generating it first if missing.

    Returns:
        Competitor DataFrame with an added ``price_avg`` column,
        or ``None`` on failure.
    """
    try:
        if not os.path.exists(DATA_PATH):
            print("[INFO] Dataset missing — running data/generator.py ...")
            subprocess.run([sys.executable, GENERATOR_PATH], check=True)
        df = pd.read_csv(DATA_PATH)
        df["price_avg"] = (df["price_min"] + df["price_max"]) / 2
        return df
    except (OSError, subprocess.CalledProcessError, pd.errors.ParserError, KeyError) as exc:
        print(f"[ERROR] Could not load competitor data: {exc}")
        return None


def save_price_comparison(df: pd.DataFrame) -> None:
    """Save a grouped bar chart of average price per service per company.

    Args:
        df: Competitor data with ``price_avg``.
    """
    try:
        pivot = df.pivot_table(
            index="service_type", columns="company_name", values="price_avg"
        ) / 1_000_000
        ax = pivot.plot(kind="bar", figsize=(12, 6), width=0.8)
        ax.set_title("Harga Rata-rata per Layanan — Kompetitor Rope Access Jakarta")
        ax.set_xlabel("Jenis Layanan")
        ax.set_ylabel("Harga Rata-rata (juta Rp)")
        ax.set_xticklabels(
            [SERVICE_LABELS.get(t.get_text(), t.get_text()) for t in ax.get_xticklabels()],
            rotation=0,
        )
        ax.legend(title="Kompetitor", fontsize=8)
        ax.grid(axis="y", alpha=0.3)
        plt.tight_layout()
        out_path = os.path.join(BASE_DIR, "price_comparison.png")
        plt.savefig(out_path, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"[OK] Saved {out_path}")
    except (KeyError, OSError, ValueError) as exc:
        print(f"[ERROR] Price comparison chart failed: {exc}")


def save_rating_scatter(df: pd.DataFrame) -> None:
    """Save a scatter plot of rating vs review count per company.

    Args:
        df: Competitor data.
    """
    try:
        agg = df.groupby("company_name").agg(
            rating=("rating", "mean"), review_count=("review_count", "sum")
        ).reset_index()
        plt.figure(figsize=(10, 6))
        plt.scatter(agg["review_count"], agg["rating"], s=160, alpha=0.7, edgecolors="black")
        for _, row in agg.iterrows():
            plt.annotate(
                row["company_name"],
                (row["review_count"], row["rating"]),
                textcoords="offset points",
                xytext=(8, 6),
                fontsize=9,
            )
        plt.title("Reputasi Kompetitor: Rating vs Jumlah Review")
        plt.xlabel("Total Review")
        plt.ylabel("Rating Rata-rata")
        plt.grid(alpha=0.3)
        plt.tight_layout()
        out_path = os.path.join(BASE_DIR, "rating_reviews.png")
        plt.savefig(out_path, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"[OK] Saved {out_path}")
    except (KeyError, OSError, ValueError) as exc:
        print(f"[ERROR] Rating scatter failed: {exc}")


def print_report(df: pd.DataFrame) -> None:
    """Print the competitive intelligence summary to stdout.

    Args:
        df: Competitor data with ``price_avg``.
    """
    try:
        print("\n" + "=" * 64)
        print("LAPORAN INTELIJEN KOMPETITOR — ROPE ACCESS JAKARTA")
        print("=" * 64)

        for service, label in SERVICE_LABELS.items():
            sub = df[df["service_type"] == service]
            if sub.empty:
                continue
            cheapest = sub.loc[sub["price_avg"].idxmin()]
            priciest = sub.loc[sub["price_avg"].idxmax()]
            gap = priciest["price_avg"] - cheapest["price_avg"]
            print(f"\n[{label}]")
            print(
                f"  Termurah   : {cheapest['company_name']} "
                f"(rata-rata Rp {cheapest['price_avg'] / 1e6:.1f} jt)"
            )
            print(
                f"  Termahal   : {priciest['company_name']} "
                f"(rata-rata Rp {priciest['price_avg'] / 1e6:.1f} jt)"
            )
            print(f"  Price gap  : Rp {gap / 1e6:.1f} jt")

        best = df.groupby("company_name")["rating"].mean().idxmax()
        best_rating = df.groupby("company_name")["rating"].mean().max()
        print(f"\nRating terbaik : {best} ({best_rating:.2f}/5.0)")
        print("=" * 64)
    except (KeyError, ValueError) as exc:
        print(f"[ERROR] Report failed: {exc}")


def main() -> None:
    """Run the full competitor analysis."""
    try:
        df = load_competitors()
        if df is None or df.empty:
            raise SystemExit(1)
        save_price_comparison(df)
        save_rating_scatter(df)
        print_report(df)
    except SystemExit:
        raise
    except Exception as exc:
        print(f"[ERROR] Analysis failed: {exc}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
