# 🕸️ SET50 Shareholder Network Analysis

Interactive social network visualization mapping **50 SET-listed companies** to their **top 5 major shareholders**, revealing hidden ownership connections across Thailand's largest public companies.

## 📋 HW1 — Social Network Analysis

> Create a social network visualization mapping the relationships between listed companies (SET 50) and their stakeholders (5) within the Stock Exchange of Thailand (SET).

## 🔗 Network Structure

| Element | Description |
|---|---|
| **Company Nodes** (⬤) | 50 SET50 companies, colored by sector |
| **Shareholder Nodes** (◆) | Top 5 major shareholders per company (123 unique) |
| **Edges** | Ownership links, weighted by % holding |
| **Total Connections** | 250 (50 companies × 5 shareholders) |

### Top Hub Shareholders
| Shareholder | # Companies |
|---|---|
| Thai NVDR Company Limited | 44 |
| กองทุนรวม วายุภักษ์หนึ่ง | 18 |
| SOCIAL SECURITY OFFICE | 17 |
| SOUTH EAST ASIA UK (TYPE C) NOMINEES LIMITED | 15 |
| UBS AG SINGAPORE BRANCH | 7 |

## 📊 Features

- Interactive force-directed network graph (drag, zoom, hover)
- Filter by sector and minimum shareholder connections
- Node sizing proportional to degree (connections)
- Hub analysis & centrality metrics (degree, betweenness, closeness)
- Data tables with full company–shareholder mapping

## 🛠️ Tech Stack

- **Streamlit** — Web application
- **NetworkX** — Graph construction & analysis
- **PyVis** — Interactive network visualization
- **Selenium** — Data scraping from SET website

## 📦 Data Source

Data scraped directly from [set.or.th](https://www.set.or.th) using Selenium (`set50.py`).

### Re-scrape data (optional)
```bash
# Run in Google Colab or locally with Chrome installed
pip install selenium webdriver-manager pandas
python set50.py
# Output: shareholders.json
```

## 🚀 Deploy

```bash
pip install -r requirements.txt
streamlit run app.py
```
