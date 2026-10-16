# 🎬 YouTube Trending Video Analytics

> Cross-Regional Algorithmic Virality, Sentiment Analysis & Lifecycle Intelligence across the United States (US), Canada (CA), and India (IN).

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![SQL](https://img.shields.io/badge/SQL-Window%20Functions-orange.svg)](sql/)
[![Tableau](https://img.shields.io/badge/Tableau-Ready-E97627.svg)](tableau/)
[![NLTK VADER](https://img.shields.io/badge/NLP-VADER%20Sentiment-brightgreen.svg)](src/sentiment_analysis.py)

---

## 📌 Project Overview
This project analyzes **119,121 daily trending video snapshots** (spanning **47,067 unique videos**) across 3 major YouTube markets: **United States (US)**, **Canada (CA)**, and **India (IN)**.

Using a multi-tool architecture combining **Python (Pandas, Seaborn, Matplotlib)**, **NLP Sentiment Analysis (NLTK VADER)**, **SQL (SQLite with Window Functions)**, and **Tableau**, we uncover the underlying mechanics governing viral shelf-life, emotional triggers, and regional audience preferences.

---

## 🚀 Key Insights & Discoveries

1. **The Negativity Viewership Premium:**
   - Video titles categorized with **Negative sentiment** ("SHOCKING", "Worst", "Tragedy", "Disaster", "Exposed") achieve the highest average viewership: **1,082,754 views**, outperforming **Positive titles** (962,987 views, **+12.4%**) and **Neutral titles** (885,809 views, **+22.2%**).
   - Positive titles, however, protect channel sentiment and secure the highest loyalty with an average **91.34% positive like ratio**.

2. **The 1-Day Cliff vs. Viral Retention Funnel:**
   - **48.95%** of all trending videos are "Flash Trends" that appear for only **1 single day** (averaging 321k views).
   - Only **2.57%** persist for **10 or more days** ("Viral Mega-Hits"), capturing an average of **4,940,876 peak views** (a 15.3x viewership multiple).

3. **Regional Genre Divergence:**
   - **United States:** Dominated by **Music** (6.03M average views) and **Film & Animation** (2.55M views).
   - **India:** Anchored by **Cinema & Movies** (3.86M views) and **Gaming** (3.44M views), while **Pets & Animals** generates the highest engagement rate (**8.47%**).
   - **Canada:** Driven by cross-border releases and entertainment (**Movies: 5.66M views**, **Music: 3.12M views**).

4. **Optimal Publishing Window:**
   - The global peak upload window is **14:00 – 17:00 UTC (10:00 AM – 1:00 PM EST)** on **Thursdays and Fridays**, generating **+18% higher view velocity**.

---

## 📊 Visualizations

| Figure | Description |
| :--- | :--- |
| **[Figure 1](reports/figures/fig1_region_category_comparison.png)** | Regional Category Rankings & View Comparison |
| **[Figure 2](reports/figures/fig2_sentiment_distribution_by_region.png)** | Sentiment Breakdown & VADER Continuous Polarity Density |
| **[Figure 3](reports/figures/fig3_trending_duration_dynamics.png)** | Shelf-Life Longevity Tiers & Monthly Upload-to-Trending Latency |
| **[Figure 4](reports/figures/fig4_sentiment_impact_matrix.png)** | Sentiment Impact Matrix: Views & Engagement Rate Distributions |
| **[Figure 5](reports/figures/fig5_publishing_window_heatmap.png)** | 24-Hour Publishing Activity & Virality Heatmap |
| **[Figure 6](reports/figures/fig6_correlation_matrix.png)** | Multi-Metric Correlation Matrix (Views, Likes, Comments, Sentiment) |

---

## 💻 Tech Stack & Architecture

- **Data Processing:** Python 3.12, Pandas, NumPy
- **Sentiment Analysis:** NLTK VADER with customized social media lexicon
- **Database & SQL:** SQLite3 (`youtube_analytics.db`) with `RANK()`, `DENSE_RANK()`, CTEs, and relational star schema
- **Visualizations:** Matplotlib, Seaborn (300 DPI)
- **Tableau Integration:** `tableau/youtube_trending_tableau.csv` & calculated fields guide
- **Executive Dashboard:** HTML5, Vanilla CSS (Dark Glassmorphic), Chart.js

---

## 🏃 Quick Start

### 1. Run Data Preprocessing & Sentiment Analysis
```bash
python src/data_preprocessing.py
```

### 2. Populate SQLite Database & Run SQL Queries
```bash
python src/sql_analysis.py
```

### 3. Generate Visualizations
```bash
python src/visualizations.py
```

### 4. Launch Interactive Web Dashboard
```bash
cd dashboard
python -m http.server 8089
# Open http://localhost:8089 in your browser
```

---

## 📄 Final Report
Read the comprehensive data storytelling report in [`reports/final_report.md`](reports/final_report.md).
