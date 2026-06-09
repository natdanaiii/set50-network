# 🕸️ SET50 Social Network Analysis

Interactive social network visualization mapping the relationships between **50 listed companies** and their **5 stakeholder types** within the **Stock Exchange of Thailand (SET)**.

## 📋 Assignment

**HW1 — Social Network Analysis**  
Create a social network visualization mapping the relationships between listed companies (SET 50) and their stakeholders (5) within the Stock Exchange of Thailand (SET).

## 🔗 5 Stakeholder Types

| # | Stakeholder Type | Description |
|---|---|---|
| 1 | **Major Shareholder Group** | Companies sharing a controlling shareholder or conglomerate (e.g., CP Group, PTT Group, Central Group, TCC Group) |
| 2 | **Board Interlock** | Companies sharing common board members or directors |
| 3 | **Sector Peer** | Companies operating in the same industry sector |
| 4 | **Business Partnership** | Strategic alliances, joint ventures, or supply-chain ties |
| 5 | **Institutional Co-Ownership** | Companies sharing major institutional investors (e.g., Thai NVDR, Ministry of Finance, Government Pension Fund) |

## 📊 Features

- Interactive force-directed network graph (drag, zoom, hover)
- Filter by stakeholder type and sector
- Centrality metrics (degree, betweenness, closeness)
- Color-coded nodes by sector, edges by stakeholder type
- Node size proportional to number of connections

## 🛠️ Tech Stack

- **Streamlit** — Web application framework
- **NetworkX** — Graph construction and analysis
- **PyVis** — Interactive network visualization
- **Pandas** — Data handling

## 🚀 Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 📦 Data Source

- [SET50 Index Constituents H1/2026](https://www.set.or.th/en/market/index/set50/overview) — Official Stock Exchange of Thailand
