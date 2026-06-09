import streamlit as st
import networkx as nx
from pyvis.network import Network
import pandas as pd
import json
import os
import tempfile
import streamlit.components.v1 as components
from collections import Counter

st.set_page_config(
    page_title="SET50 Shareholder Network",
    page_icon="🕸️",
    layout="wide"
)

# ═══════════════════════ Load Data ═══════════════════════

_possible_paths = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "shareholders.json"),
    os.path.join(os.getcwd(), "shareholders.json"),
    "shareholders.json",
]

DATA_PATH = None
for _p in _possible_paths:
    if os.path.exists(_p):
        DATA_PATH = _p
        break

if DATA_PATH is None:
    st.error("❌ ไม่พบไฟล์ shareholders.json — กรุณาตรวจสอบว่าอัปโหลดไฟล์นี้ขึ้น GitHub แล้ว")
    st.info(f"Searched paths: {_possible_paths}")
    st.info(f"Files in cwd ({os.getcwd()}): {os.listdir(os.getcwd())}")
    st.stop()


@st.cache_data
def load_data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


try:
    raw = load_data()
except Exception as e:
    st.error(f"❌ Error loading data: {e}")
    st.stop()


# ═══════════════════════ SET50 Sector Mapping ═══════════════════════

SECTORS = {
    "ADVANC": "ICT",
    "AOT": "Transport",
    "AWC": "Property",
    "BANPU": "Energy",
    "BBL": "Banking",
    "BDMS": "Healthcare",
    "BEM": "Transport",
    "BH": "Healthcare",
    "BJC": "Commerce",
    "BTS": "Transport",
    "CBG": "Food & Bev",
    "CCET": "Electronics",
    "CENTEL": "Tourism",
    "COM7": "Commerce",
    "CPALL": "Commerce",
    "CPF": "Food & Bev",
    "CPN": "Property",
    "CRC": "Commerce",
    "DELTA": "Electronics",
    "EGCO": "Energy",
    "GPSC": "Energy",
    "GULF": "Energy",
    "HMPRO": "Commerce",
    "IVL": "Petrochem",
    "KBANK": "Banking",
    "KKP": "Banking",
    "KTB": "Banking",
    "KTC": "Finance",
    "LH": "Property",
    "MINT": "Tourism",
    "MTC": "Finance",
    "OR": "Energy",
    "OSP": "Food & Bev",
    "PTT": "Energy",
    "PTTEP": "Energy",
    "PTTGC": "Petrochem",
    "RATCH": "Energy",
    "SAWAD": "Finance",
    "SCB": "Banking",
    "SCC": "Construction",
    "SCGP": "Packaging",
    "TCAP": "Banking",
    "TIDLOR": "Finance",
    "TISCO": "Banking",
    "TLI": "Insurance",
    "TOP": "Energy",
    "TRUE": "ICT",
    "TTB": "Banking",
    "TU": "Food & Bev",
    "WHA": "Property",
}

SECTOR_COLORS = {
    "Banking": "#1a5276",
    "Energy": "#d35400",
    "Commerce": "#27ae60",
    "ICT": "#8e44ad",
    "Transport": "#2980b9",
    "Healthcare": "#c0392b",
    "Food & Bev": "#16a085",
    "Property": "#f1c40f",
    "Electronics": "#2c3e50",
    "Petrochem": "#7f8c8d",
    "Finance": "#e67e22",
    "Tourism": "#e74c3c",
    "Construction": "#95a5a6",
    "Packaging": "#bdc3c7",
    "Insurance": "#1abc9c",
}


# ═══════════════════════ Helper Functions ═══════════════════════

def safe_float(value):
    try:
        return float(value)
    except Exception:
        return 0.0


# ═══════════════════════ Build Graph ═══════════════════════

def build_graph(selected_sectors, min_conn):
    G = nx.Graph()

    filtered = {
        symbol for symbol, sector in SECTORS.items()
        if sector in selected_sectors
    }

    edges = []

    for sym in filtered:
        for h in raw.get(sym, []):
            shareholder_name = str(h.get("name", "")).strip()
            pct = safe_float(h.get("pct", 0))

            if shareholder_name:
                edges.append((sym, shareholder_name, pct))

    shareholder_count = Counter(shareholder for _, shareholder, _ in edges)

    valid_shareholders = {
        shareholder for shareholder, count in shareholder_count.items()
        if count >= min_conn
    }

    for sym in filtered:
        has_edge = any(
            str(h.get("name", "")).strip() in valid_shareholders
            for h in raw.get(sym, [])
        )

        if has_edge or min_conn <= 1:
            G.add_node(
                sym,
                node_type="company",
                sector=SECTORS[sym]
            )

    for sym, shareholder, pct in edges:
        if shareholder in valid_shareholders and sym in G:
            if shareholder not in G:
                G.add_node(
                    shareholder,
                    node_type="shareholder",
                    sector=""
                )

            G.add_edge(
                sym,
                shareholder,
                weight=pct
            )

    return G


# ═══════════════════════ Render Network ═══════════════════════

def render_network(G, physics_on=False):
    net = Network(
        height="720px",
        width="100%",
        bgcolor="#ffffff",
        font_color="#111111",
        directed=False,
        cdn_resources="remote"
    )

    degrees = dict(G.degree())
    max_degree = max(degrees.values()) if degrees else 1

    # Add nodes
    for node, data in G.nodes(data=True):
        degree = degrees.get(node, 1)

        if data.get("node_type") == "company":
            sector = data.get("sector", "")
            color = SECTOR_COLORS.get(sector, "#888888")

            size = 14 + (degree / max_degree) * 22

            title = (
                f"🏢 {node}<br>"
                f"Sector: {sector}<br>"
                f"Degree: {degree}"
            )

            net.add_node(
                node,
                label=node,
                title=title,
                color={
                    "background": color,
                    "border": "#333333",
                    "highlight": {
                        "background": color,
                        "border": "#000000"
                    }
                },
                size=size,
                shape="dot",
                borderWidth=1.5,
                mass=2,
                font={
                    "size": 13,
                    "color": "#111111",
                    "strokeWidth": 3,
                    "strokeColor": "#ffffff"
                }
            )

        else:
            size = 12 + (degree / max_degree) * 22
            label = node if len(node) <= 28 else node[:28] + "..."

            title = (
                f"👤 {node}<br>"
                f"Connected companies: {degree}"
            )

            net.add_node(
                node,
                label=label,
                title=title,
                color={
                    "background": "rgba(255,107,107,0.28)",
                    "border": "rgba(255,107,107,0.95)",
                    "highlight": {
                        "background": "rgba(255,107,107,0.45)",
                        "border": "rgba(255,107,107,1)"
                    }
                },
                size=size,
                shape="dot",
                borderWidth=2,
                mass=1,
                font={
                    "size": 11,
                    "color": "#111111",
                    "strokeWidth": 3,
                    "strokeColor": "#ffffff"
                }
            )

    # Add edges
    for u, v, data in G.edges(data=True):
        weight = safe_float(data.get("weight", 1))

        # Cleaner relation lines: visible but not too thick
        width = 0.8 + min(weight, 50) / 14

        net.add_edge(
            u,
            v,
            title=f"Shareholding: {weight:.2f}%",
            width=width,
            color={
                "color": "rgba(70,70,70,0.30)",
                "highlight": "rgba(0,0,0,0.85)",
                "hover": "rgba(0,0,0,0.85)"
            },
            smooth={
                "enabled": True,
                "type": "continuous",
                "roundness": 0.2
            }
        )

    if physics_on:
        # Medium spacing, faster loading than the previous version
        net.force_atlas_2based(
            gravity=-110,
            central_gravity=0.008,
            spring_length=250,
            spring_strength=0.03,
            damping=0.70
        )
    else:
        net.toggle_physics(False)

    net.set_options("""
    {
      "interaction": {
        "hover": true,
        "tooltipDelay": 100,
        "navigationButtons": true,
        "keyboard": true,
        "dragNodes": true,
        "dragView": true,
        "zoomView": true
      },
      "nodes": {
        "shadow": {
          "enabled": true,
          "color": "rgba(0,0,0,0.10)",
          "size": 6,
          "x": 2,
          "y": 2
        }
      },
      "edges": {
        "selectionWidth": 3,
        "hoverWidth": 3
      },
      "physics": {
        "stabilization": {
          "enabled": true,
          "iterations": 150,
          "updateInterval": 25,
          "fit": true
        },
        "minVelocity": 1.5
      }
    }
    """)

    return net


# ═══════════════════════ UI ═══════════════════════

st.title("🕸️ SET50 Shareholder Network")

st.caption(
    "Social network mapping 50 SET-listed companies to their top 5 major shareholders "
    "as stakeholders — data scraped from set.or.th"
)

st.info(
    "Nodes represent SET50 companies and stakeholders/shareholders. "
    "Edges represent shareholding relationships. "
    "Node size reflects degree, and edge thickness reflects shareholding percentage."
)

# ═══════════════════════ Sidebar ═══════════════════════

st.sidebar.header("🔧 Filters")

all_sectors = sorted(set(SECTORS.values()))

selected_sectors = st.sidebar.multiselect(
    "Sectors",
    all_sectors,
    default=all_sectors
)

min_conn = st.sidebar.slider(
    "Min companies per shareholder",
    1,
    20,
    1,
    help="Use 1 to show all shareholders. Increase this value to focus on common shareholders."
)

physics = st.sidebar.checkbox(
    "Enable physics",
    False,
    help="Turn on only if you want the graph to rearrange automatically. It may load slower."
)

# ═══════════════════════ Create Graph ═══════════════════════

G = build_graph(selected_sectors, min_conn)

company_count = sum(
    1 for _, data in G.nodes(data=True)
    if data.get("node_type") == "company"
)

shareholder_count = sum(
    1 for _, data in G.nodes(data=True)
    if data.get("node_type") == "shareholder"
)

relationship_count = G.number_of_edges()

density = nx.density(G) if G.number_of_nodes() > 1 else 0

# ═══════════════════════ Metrics ═══════════════════════

col1, col2, col3, col4 = st.columns(4)

col1.metric("Companies", company_count)
col2.metric("Stakeholders", shareholder_count)
col3.metric("Relationships", relationship_count)
col4.metric("Density", f"{density:.4f}")

# ═══════════════════════ Legend ═══════════════════════

with st.expander("Legend and Methodology", expanded=True):
    st.markdown("""
    **Network design**

    - **Company nodes:** SET50 listed companies, colored by sector  
    - **Stakeholder nodes:** Top 5 major shareholders, shown as transparent red circles  
    - **Edges:** Shareholding relationships  
    - **Edge thickness:** Shareholding percentage  
    - **Node size:** Degree, or number of connected relationships  
    - **Graph type:** Undirected weighted graph  

    **Interpretation**

    A stakeholder connected to many companies can be interpreted as a hub.  
    Companies connected to the same stakeholder may have an indirect relationship through common ownership.
    """)

    sector_parts = []

    for sector in sorted(SECTOR_COLORS):
        color = SECTOR_COLORS[sector]
        sector_parts.append(
            f"<span style='color:{color}'>●</span> {sector}"
        )

    st.markdown("**Sector colors:**", unsafe_allow_html=True)
    st.markdown(" · ".join(sector_parts), unsafe_allow_html=True)

st.markdown("---")

# ═══════════════════════ Network Visualization ═══════════════════════

st.subheader("Network Visualization")

if G.number_of_nodes() == 0:
    st.warning("No data for current filters. Lower the minimum connections slider.")
else:
    net = render_network(G, physics)

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".html",
        mode="w",
        encoding="utf-8"
    ) as f:
        net.save_graph(f.name)
        html_path = f.name

    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    components.html(
        html_content,
        height=740,
        scrolling=True
    )

    os.unlink(html_path)

# ═══════════════════════ Data Tables ═══════════════════════

st.markdown("---")
st.subheader("📊 Data Tables")

tab1, tab2, tab3 = st.tabs(
    [
        "Top Shareholders / Hubs",
        "All Relationships",
        "Centrality"
    ]
)

with tab1:
    rows = []

    for node, data in G.nodes(data=True):
        if data.get("node_type") == "shareholder":
            connected_companies = sorted(
                neighbor for neighbor in G.neighbors(node)
                if G.nodes[neighbor].get("node_type") == "company"
            )

            rows.append({
                "Shareholder / Stakeholder": node,
                "# Companies": len(connected_companies),
                "Connected Companies": ", ".join(connected_companies)
            })

    if rows:
        df_hubs = pd.DataFrame(rows)
        df_hubs = df_hubs.sort_values(
            "# Companies",
            ascending=False
        ).reset_index(drop=True)

        st.dataframe(
            df_hubs,
            use_container_width=True
        )
    else:
        st.info("No shareholder hub data available for the selected filters.")

with tab2:
    rows = []

    for u, v, data in G.edges(data=True):
        if G.nodes[u].get("node_type") == "company":
            company = u
            shareholder = v
        else:
            company = v
            shareholder = u

        rows.append({
            "Company": company,
            "Sector": SECTORS.get(company, ""),
            "Shareholder / Stakeholder": shareholder,
            "Holding %": round(safe_float(data.get("weight", 0)), 4)
        })

    if rows:
        df_edges = pd.DataFrame(rows)
        df_edges = df_edges.sort_values(
            ["Company", "Holding %"],
            ascending=[True, False]
        ).reset_index(drop=True)

        st.dataframe(
            df_edges,
            use_container_width=True
        )
    else:
        st.info("No relationship data available for the selected filters.")

with tab3:
    if G.number_of_nodes() > 1:
        degree_centrality = nx.degree_centrality(G)
        betweenness_centrality = nx.betweenness_centrality(G)
        closeness_centrality = nx.closeness_centrality(G)

        rows = []

        for node in degree_centrality:
            rows.append({
                "Node": node,
                "Type": G.nodes[node].get("node_type", ""),
                "Degree": G.degree(node),
                "Degree Centrality": round(degree_centrality[node], 4),
                "Betweenness Centrality": round(betweenness_centrality[node], 4),
                "Closeness Centrality": round(closeness_centrality[node], 4)
            })

        df_centrality = pd.DataFrame(rows)
        df_centrality = df_centrality.sort_values(
            "Degree Centrality",
            ascending=False
        ).reset_index(drop=True)

        st.dataframe(
            df_centrality,
            use_container_width=True
        )
    else:
        st.info("Not enough nodes to calculate centrality.")

# ═══════════════════════ Footer ═══════════════════════

st.sidebar.markdown("---")
st.sidebar.markdown(
    "**Data:** Scraped from [SET](https://www.set.or.th)  \n"
    "**Scraper:** `set50.py`  \n"
    "**Course:** Social Network Analysis — HW1  \n"
    "**Stack:** Streamlit · NetworkX · PyVis"
)
