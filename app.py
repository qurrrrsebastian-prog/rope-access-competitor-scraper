"""Rope Access Competitor Tracker — Interactive Streamlit App.

Bintang-5 conversion of the original ``scraper.py`` batch script into an
interactive Ocean-Blue competitor-intelligence dashboard for PT RKARI:
filter competitors, see colour-coded price cards, and compare prices across
companies and locations. SQLite-backed search history, sanitized URL/domain
validation for the "Visit" links, and a loading skeleton.

Run with: ``streamlit run app.py``
"""
from __future__ import annotations

import hashlib
import os
import sys
from datetime import datetime
from typing import List, Optional
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core.database import (
    init_db,
    save_query,
    get_history,
    cache_result,
    get_cached_result,
)
from core.security import sanitize_input, generate_session_id
from core.theme import inject_phase1_theme, show_loading_skeleton

BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))
DATA_PATH: str = os.path.join(BASE_DIR, "data", "competitor_data.csv")
GENERATOR_PATH: str = os.path.join(BASE_DIR, "data", "generate_competitors.py")

ALL_LOCATIONS: List[str] = ["Jakarta", "Tangerang", "Bekasi", "Depok", "Bogor"]
ALL_SERVICES: List[str] = [
    "Pembersihan Kaca", "Maintenance Gedung", "Waterproofing", "Rope Access", "Sealant",
]
ALLOWED_TLDS: tuple = (".co.id", ".com", ".id", ".net", ".org")
MAX_CARDS: int = 12

BORDER_GREEN: str = "#22c55e"
BORDER_RED: str = "#ef4444"
BORDER_YELLOW: str = "#eab308"
CYAN: str = "#38bdf8"


st.set_page_config(
    page_title="Competitor Price Tracker",
    page_icon="🔍",
    layout="wide",
)
inject_phase1_theme()


def inject_ui_layout_fixes() -> None:
    """Inject layout-only CSS (no color changes): KPI text + mobile grid."""
    st.markdown(
        """
        <style>
            [data-testid="stMetricLabel"], [data-testid="stMetricLabel"] p {
                white-space: normal !important; overflow: visible !important;
                font-size: 0.85rem !important; line-height: 1.2 !important;
            }
            [data-testid="stMetricValue"] {
                white-space: normal !important; overflow: visible !important;
                font-size: 1.4rem !important;
            }
            @media (max-width: 768px) {
                [data-testid="stHorizontalBlock"] {
                    flex-wrap: wrap !important; gap: 0.5rem !important;
                }
                [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
                    flex: 1 1 45% !important; min-width: 45% !important;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


inject_ui_layout_fixes()


# --------------------------------------------------------------------------- #
# Security helpers
# --------------------------------------------------------------------------- #
def validate_competitor_url(url: str) -> Optional[str]:
    """Sanitize and validate a competitor website URL / domain.

    Accepts only http(s) URLs whose host has an allowed TLD and contains no
    suspicious characters. Returns the cleaned URL, or None if invalid.

    Args:
        url: Raw URL string from the dataset.

    Returns:
        A safe URL string, or None when the URL fails validation.
    """
    try:
        cleaned = sanitize_input(str(url), max_length=200).strip()
        if not cleaned:
            return None
        parsed = urlparse(cleaned)
        if parsed.scheme not in ("http", "https"):
            return None
        host = parsed.netloc.lower()
        if not host or " " in host or ".." in host:
            return None
        if not any(host.endswith(tld) for tld in ALLOWED_TLDS):
            return None
        return cleaned
    except Exception:  # pragma: no cover - defensive
        return None


# --------------------------------------------------------------------------- #
# Data
# --------------------------------------------------------------------------- #
@st.cache_resource
def _bootstrap() -> bool:
    """Initialize the database once per process."""
    try:
        init_db()
        return True
    except Exception as exc:  # pragma: no cover - defensive
        st.warning(f"Bootstrap warning: {exc}")
        return False


@st.cache_data(show_spinner=False)
def load_competitors() -> pd.DataFrame:
    """Load competitor data, generating the CSV if missing.

    Returns:
        DataFrame with a derived ``price_avg`` column. Empty on failure.
    """
    try:
        if not os.path.exists(DATA_PATH):
            import subprocess

            subprocess.run([sys.executable, GENERATOR_PATH], check=True)
        df = pd.read_csv(DATA_PATH)
        df["price_avg"] = (df["price_min"] + df["price_max"]) / 2
        df["last_updated"] = pd.to_datetime(df["last_updated"])
        return df
    except Exception as exc:  # pragma: no cover - defensive
        st.error(f"Gagal memuat data kompetitor: {exc}")
        return pd.DataFrame()


def filter_competitors(
    df: pd.DataFrame,
    locations: List[str],
    services: List[str],
    price_range: tuple,
    sort_by: str,
) -> pd.DataFrame:
    """Filter and sort the competitor DataFrame per the sidebar controls.

    Args:
        df: Full competitor data with ``price_avg``.
        locations: Locations to include (empty = all).
        services: Services to include (empty = all).
        price_range: (min, max) in millions of Rupiah, against ``price_avg``.
        sort_by: One of the sidebar sort options.

    Returns:
        Filtered + sorted DataFrame (a copy).
    """
    try:
        out = df.copy()
        if locations:
            out = out[out["location"].isin(locations)]
        if services:
            out = out[out["service_type"].isin(services)]
        lo, hi = price_range[0] * 1_000_000, price_range[1] * 1_000_000
        out = out[(out["price_avg"] >= lo) & (out["price_avg"] <= hi)]
        if sort_by == "Harga Terendah":
            out = out.sort_values("price_avg", ascending=True)
        elif sort_by == "Harga Tertinggi":
            out = out.sort_values("price_avg", ascending=False)
        else:  # Terbaru
            out = out.sort_values("last_updated", ascending=False)
        return out.reset_index(drop=True)
    except Exception as exc:  # pragma: no cover - defensive
        st.error(f"Filter gagal: {exc}")
        return df


def _border_color(price_avg: float, market_avg: float) -> str:
    """Pick a card border color based on price vs market average."""
    if market_avg <= 0:
        return BORDER_YELLOW
    ratio = price_avg / market_avg
    if ratio < 0.98:
        return BORDER_GREEN
    if ratio > 1.02:
        return BORDER_RED
    return BORDER_YELLOW


def render_competitor_card(row: pd.Series, market_avg: float) -> None:
    """Render a single competitor card with colored border + Visit link."""
    try:
        color = _border_color(float(row["price_avg"]), market_avg)
        pmin = row["price_min"] / 1_000_000
        pmax = row["price_max"] / 1_000_000
        company = sanitize_input(str(row["company_name"]), max_length=80)
        service = sanitize_input(str(row["service_type"]), max_length=40)
        location = sanitize_input(str(row["location"]), max_length=40)
        updated = pd.to_datetime(row["last_updated"]).strftime("%d %b %Y")
        st.markdown(
            f"""
            <div style="border-left: 5px solid {color}; background: rgba(30,58,95,0.5);
                        border-radius: 12px; padding: 0.9rem 1rem; margin-bottom: 0.5rem;
                        min-height: 165px;">
                <div style="font-weight:700; font-size:1.02rem; color:#e2e8f0;">{company}</div>
                <span style="display:inline-block; background:{CYAN}22; color:{CYAN};
                             border:1px solid {CYAN}55; border-radius:8px;
                             padding:1px 8px; font-size:0.74rem; margin:6px 0;">{service}</span>
                <div style="color:#38bdf8; font-weight:600; margin-top:4px;">
                    Rp {pmin:.0f} jt - Rp {pmax:.0f} jt</div>
                <div style="color:#cbd5e1; font-size:0.82rem; margin-top:4px;">📍 {location}</div>
                <div style="color:#94a3b8; font-size:0.74rem; margin-top:2px;">🕒 update {updated}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        safe_url = validate_competitor_url(row.get("contact", ""))
        if safe_url:
            st.link_button("🔗 Visit", safe_url, width="stretch")
        else:
            st.caption("🔒 URL tidak valid")
    except Exception as exc:  # pragma: no cover - defensive
        st.error(f"Kartu gagal: {exc}")


def render_comparison_chart(df: pd.DataFrame) -> None:
    """Bar chart of average price per company (top 15 by price)."""
    try:
        top = df.nlargest(min(15, len(df)), "price_avg").sort_values("price_avg")
        fig = go.Figure(go.Bar(
            x=(top["price_avg"] / 1_000_000),
            y=top["company_name"],
            orientation="h",
            marker=dict(color=top["price_avg"] / 1_000_000, colorscale="Blues"),
        ))
        fig.update_layout(
            template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            height=460, margin=dict(t=50, l=20, r=20, b=30),
            title="Harga Rata-rata per Kompetitor (juta Rp)",
            xaxis_title="Harga Rata-rata (juta Rp)", yaxis_title="Kompetitor",
        )
        st.plotly_chart(fig, width="stretch")
    except Exception as exc:  # pragma: no cover - defensive
        st.error(f"Grafik perbandingan gagal: {exc}")


def render_location_chart(df: pd.DataFrame) -> None:
    """Grouped bar of average price per location per service."""
    try:
        pivot = (
            df.pivot_table(index="location", columns="service_type", values="price_avg", aggfunc="mean")
            / 1_000_000
        )
        fig = go.Figure()
        palette = ["#0c4a6e", "#0ea5e9", "#38bdf8", "#7dd3fc", "#bae6fd"]
        for i, service in enumerate(pivot.columns):
            fig.add_trace(go.Bar(
                x=pivot.index, y=pivot[service], name=service,
                marker_color=palette[i % len(palette)],
            ))
        fig.update_layout(
            template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            height=460, margin=dict(t=50, l=20, r=20, b=30), barmode="group",
            title="Harga Rata-rata per Lokasi & Jasa (juta Rp)",
            xaxis_title="Lokasi", yaxis_title="Harga Rata-rata (juta Rp)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig, width="stretch")
    except Exception as exc:  # pragma: no cover - defensive
        st.error(f"Grafik lokasi gagal: {exc}")


def render_sidebar_history() -> None:
    """Render the recent-search-history expander in the sidebar."""
    try:
        with st.sidebar.expander("🕒 Recent History", expanded=False):
            history = get_history(limit=5)
            if not history:
                st.caption("Belum ada riwayat pencarian.")
                return
            for row in history:
                st.markdown(
                    f"**{row.get('timestamp', '')[:16]}**  \n"
                    f"{row.get('query', '')}  \n"
                    f"<span style='color:#94a3b8'>{row.get('result_summary', '')}</span>",
                    unsafe_allow_html=True,
                )
    except Exception as exc:  # pragma: no cover - defensive
        st.sidebar.caption(f"History error: {exc}")


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> None:
    """Render the full competitor-tracker dashboard."""
    _bootstrap()

    if "session_id" not in st.session_state:
        st.session_state["session_id"] = generate_session_id()
    session_id: str = st.session_state["session_id"]

    df = load_competitors()
    if df.empty:
        st.error("Dataset tidak tersedia. Jalankan data/generate_competitors.py.")
        return

    # ---- Sidebar filters -------------------------------------------------
    st.sidebar.header("🎛️ Filter")
    location_filter = st.sidebar.multiselect("Lokasi", ALL_LOCATIONS, default=["Jakarta"])
    service_filter = st.sidebar.multiselect("Jasa", ALL_SERVICES, default=["Pembersihan Kaca"])
    price_range = st.sidebar.slider("Rentang Harga (Rp juta)", 15, 120, (15, 120))
    sort_by = st.sidebar.selectbox("Urutkan", ["Harga Terendah", "Harga Tertinggi", "Terbaru"])
    search_clicked = st.sidebar.button("🔍 Cari Kompetitor", type="primary")
    render_sidebar_history()

    st.title("🔍 Rope Access Competitor Tracker")
    st.caption("Monitor harga & layanan kompetitor PT RKARI")

    # ---- Filter (with skeleton) -----------------------------------------
    placeholder = st.empty()
    with placeholder.container():
        show_loading_skeleton("Memuat data kompetitor...")
    filtered = filter_competitors(df, location_filter, service_filter, price_range, sort_by)
    placeholder.empty()

    # ---- Search history + cache -----------------------------------------
    query_desc = sanitize_input(
        f"lokasi={location_filter or 'all'}, jasa={service_filter or 'all'}, "
        f"harga={price_range}, sort={sort_by}",
        max_length=160,
    )
    result_desc = f"{len(filtered)} kompetitor ditemukan"
    cache_key = hashlib.sha256(query_desc.encode("utf-8")).hexdigest()
    if get_cached_result(cache_key) is None:
        cache_result(cache_key, {"count": int(len(filtered))})
    if search_clicked:
        save_query(query_desc, result_desc, session_id)

    if filtered.empty:
        st.warning("Tidak ada kompetitor yang cocok dengan filter ini.")
        return

    # ---- KPI cards -------------------------------------------------------
    market_avg = float(filtered["price_avg"].mean())
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Kompetitor", f"{len(filtered)}")
    c2.metric("Harga Terendah", f"Rp {filtered['price_min'].min() / 1e6:.0f} jt")
    c3.metric("Harga Tertinggi", f"Rp {filtered['price_max'].max() / 1e6:.0f} jt")
    c4.metric("Avg Price", f"Rp {market_avg / 1e6:.0f} jt")

    # ---- Competitor cards (3 per row) -----------------------------------
    st.divider()
    shown = filtered.head(MAX_CARDS)
    st.subheader(f"🏢 Kompetitor ({len(shown)} dari {len(filtered)})")
    rows = shown.to_dict("records")
    for i in range(0, len(rows), 3):
        cols = st.columns(3)
        for col, record in zip(cols, rows[i:i + 3]):
            with col:
                render_competitor_card(pd.Series(record), market_avg)

    # ---- Analysis tabs ---------------------------------------------------
    st.divider()
    st.subheader("📊 Analisis Harga")
    tab_cmp, tab_loc, tab_tbl = st.tabs(["📈 Perbandingan", "📍 Per Lokasi", "📋 Tabel Lengkap"])
    with tab_cmp:
        render_comparison_chart(filtered)
    with tab_loc:
        render_location_chart(filtered)
    with tab_tbl:
        table = filtered.copy()
        table["price_min"] = (table["price_min"] / 1e6).round(0).astype(int)
        table["price_max"] = (table["price_max"] / 1e6).round(0).astype(int)
        table["price_avg"] = (table["price_avg"] / 1e6).round(1)
        table["last_updated"] = table["last_updated"].dt.strftime("%Y-%m-%d")
        show_cols = [
            "company_name", "location", "service_type",
            "price_min", "price_max", "price_avg", "contact", "last_updated",
        ]
        st.dataframe(table[show_cols], width="stretch", height=400)

    st.caption(f"Session: {session_id} • {len(filtered)} kompetitor • diurutkan: {sort_by}")


if __name__ == "__main__":
    main()
