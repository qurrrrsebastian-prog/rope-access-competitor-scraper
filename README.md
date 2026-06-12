# 🏗️ Rope Access Competitor Scraper & Analysis

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-2.1-150458?logo=pandas&logoColor=white)
![Matplotlib](https://img.shields.io/badge/Matplotlib-3.8-11557C)

Competitive pricing intelligence for the **Jakarta rope access / building maintenance market**. Analyzes 5 competitors across 3 service lines (rope access, glass cleaning, maintenance), benchmarks price ranges, and maps reputation (rating vs review volume) — the analysis a service business needs before setting its own pricing.

## ✨ Features

- 💰 **Price benchmarking** — grouped bar chart of average project price per service line per competitor
- ⭐ **Reputation map** — scatter of average rating vs total review count, labeled per company
- 🕵️ **Console intelligence report** — cheapest and most expensive player per service, best-rated competitor, and the price gap in each segment
- 🔄 **Self-healing data** — dataset auto-generates on first run if missing

## 🛠️ Tech Stack

Python · Pandas · Matplotlib

## 🚀 How to Run

```bash
cd rope-access-competitor-scraper
pip install -r requirements.txt
python data/generator.py
python scraper.py
```

Outputs: `price_comparison.png`, `rating_reviews.png`, plus a console report.

## 🔑 Key Insights

1. **Maintenance is the highest-value segment** with average project prices of Rp 32–46 jt — roughly 3x the glass cleaning segment (Rp 11–18 jt), making it the most attractive upsell path.
2. **Price gaps within a single service reach Rp 14.5 jt between competitors** (rope access: Altus Safety at Rp 18.1 jt vs HighRise Maintenance at Rp 32.6 jt) — the market has no anchored price, so a new entrant can position mid-range and still compete.
3. **HighRise Maintenance is simultaneously the best-rated (4.47/5) and the cheapest in two of three segments** — a value-leader strategy that makes it the most dangerous competitor to undercut on price alone.

## 👤 Author

**Avatar Putra Sigit**
🔗 [linkedin.com/in/avatarputrasigit](https://linkedin.com/in/avatarputrasigit) · 🐙 [github.com/qurrrrsebastian-prog](https://github.com/qurrrrsebastian-prog)
