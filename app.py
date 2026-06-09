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
    "Banking": "#1f77b4",
    "Energy": "#ff7f0e",
    "Commerce": "#2ca02c",
    "ICT": "#9467bd",
    "Transport": "#17becf",
    "Healthcare": "#d62728",
    "Food & Bev": "#8c564b",
    "Property": "#bcbd22",
    "Electronics": "#7f7f7f",
    "Petrochem": "#aec7e8",
    "Finance": "#ffbb78",
    "Tourism": "#e377c2",
    "Construction": "#c7c7c7",
    "Packaging": "#98df8a",
    "Insurance": "#9edae5",
}


# ═══════════════════════ Helper Functions ═══════════════════════

def safe_float(value):
    try:
        return float(value)
    except Exception:
        return 0.0


def build_graph(selected_sectors, min_conn, min_holding):
    G = nx.Graph()

    filtered_companies = [
        sym for sym, sec in SECTORS.items()
        if sec in selected_sectors
    ]

    edges = []

    for sym in filtered_companies:
        holders = raw.get(sym, [])

        for h in holders:
            shareholder_name = str(h.get("name", "")).strip()
            pct = safe_float(h.get("pct", 0))

            if shareholder_name and pct >= min_holding:
                edges.append((sym, shareholder_name, pct))

    shareholder_count = Counter(sh for _, sh, _ in edges)

    valid_shareholders = {
        sh for sh, count in shareholder_count.items()
        if count >= min_conn
    }

    for sym in filtered_companies:
        company_has_edge = False

        for company, shareholder, pct in edges:
            if company == sym and shareholder in valid_shareholders:
                company_has_edge = True
                break

        if company_has_edge:
            G.add_node(
                sym,
                node_type="company",
                sector=SECTORS.get(sym, "Unknown")
            )

    for company, shareholder, pct in edges:
        if company in G and shareholder in valid_shareholders:
            if shareholder not in G:
                G.add_node(
                    shareholder,
                    node_type="shareholder",
                    sector=""
                )

            G.add_edge(
                company,
                shareholder,
                weight=pct
            )

    return G


def render_network(G, show_edge_label=False):
    net = Network(
        height="760px",
        width="100%",
        bgcolor="#ffffff",
        font_color="#222222",
        directed=False,
        cdn_resources="remote"
    )

    degrees = dict(G.degree())
    max_degree = max(degrees.values()) if degrees else 1

    # Add nodes
    for node, data in G.nodes(data=True):
        degree = degrees.get(node, 1)
        node_type = data.get("node_type", "")

        if node_type == "company":
            sector = data.get("sector", "")
            color = SECTOR_COLORS.get(sector, "#1f77b4")

            node_size = 20 + (degree / max_degree) * 26

            title = (
                f"<b>Company:</b> {node}<br>"
                f"<b>Sector:</b> {sector}<br>"
                f"<b>Degree:</b> {degree}"
            )

            net.add_node(
                node,
                label=node,
                title=title,
                color={
                    "background": color,
                    "border": "#111111",
                    "highlight": {
                        "background": "#ffd166",
                        "border": "#111111"
                    }
                },
                size=node_size,
                shape="circle",
                borderWidth=2,
                font={
                    "size": 18,
                    "color": "#111111",
                    "face": "arial",
                    "strokeWidth": 3,
                    "strokeColor": "#ffffff"
                }
            )

        else:
            label = node if len(node) <= 24 else node[:24] + "..."
            node_size = 18 + (degree / max_degree) * 34

            title = (
                f"<b>Stakeholder / Shareholder:</b> {node}<br>"
                f"<b>Degree:</b> {degree}<br>"
                f"<b>Connected companies:</b> {degree}"
            )

            net.add_node(
                node,
                label=label,
                title=title,
                color={
                    "background": "#ff4d4d",
                    "border": "#111111",
                    "highlight": {
                        "background": "#ffd166",
                        "border": "#111111"
                    }
                },
                size=node_size,
                shape="circle",
                borderWidth=2,
                font={
                    "size": 13,
                    "color": "#111111",
                    "face": "arial",
                    "strokeWidth": 3,
                    "strokeColor": "#ffffff"
                }
            )

    # Add edges
    for u, v, data in G.edges(data=True):
        pct = safe_float(data.get("weight", 1))

        width = 1.2 + min(pct, 50) / 7
        edge_label = f"{pct:.1f}%" if show_edge_label else ""

        net.add_edge(
            u,
            v,
            title=f"Shareholding: {pct:.2f}%",
            label=edge_label,
            width=width,
            color={
                "color": "rgba(70,70,70,0.42)",
                "highlight": "#000000",
                "hover": "#000000"
            },
            smooth={
                "enabled": True,
                "type": "dynamic"
            },
            font={
                "size": 10,
                "color": "#111111",
                "strokeWidth": 3,
                "strokeColor": "#ffffff"
            }
        )

    # Force-directed SNA layout
    net.set_options("""
    {
      "nodes": {
        "scaling": {
          "min": 15,
          "max": 60
        }
      },
      "edges": {
        "smooth": {
          "enabled": true,
          "type": "dynamic"
        },
        "selectionWidth": 4,
        "hoverWidth": 4
      },
      "physics": {
        "enabled": true,
        "solver": "forceAtlas2Based",
        "forceAtlas2Based": {
          "gravitationalConstant": -130,
          "centralGravity": 0.018,
          "springLength": 180,
          "springConstant": 0.045,
          "damping": 0.55,
          "avoidOverlap": 0.85
        },
        "stabilization": {
          "enabled": true,
          "iterations": 400,
          "updateInterval": 25,
          "fit": true
        }
      },
      "interaction": {
        "hover": true,
        "tooltipDelay": 100,
        "navigationButtons": true,
        "keyboard": true,
        "dragNodes": true,
        "dragView": true,
        "zoomView": true,
        "multiselect": true
      }
    }
    """)

    return net


# ═══════════════════════ UI ═══════════════════════

st.title("🕸️ SET50 Shareholder Network")

st.caption(
    "Social network visualization mapping SET50 listed companies and their top 5 major shareholders as stakeholders."
)

st.info(
    "Each node represents either a SET50 company or a stakeholder/shareholder. "
    "Each edge represents a shareholding relationship. "
    "Node size is based on degree, and edge thickness is based on shareholding percentage."
)

# ═══════════════════════ Sidebar Filters ═══════════════════════

st.sidebar.header("🔧 Filters")

all_sectors = sorted(set(SECTORS.values()))

selected_sectors = st.sidebar.multiselect(
    "Select sectors",
    all_sectors,
    default=all_sectors
)

min_conn = st.sidebar.slider(
    "Minimum companies per shareholder",
    min_value=1,
    max_value=20,
    value=1,
    help="Use 1 to show all stakeholders. Increase this value to focus on hub shareholders."
)

min_holding = st.sidebar.slider(
    "Minimum holding percentage",
    min_value=0.0,
    max_value=50.0,
    value=0.0,
    step=0.5,
    help="Filter out smaller shareholding relationships."
)

show_edge_label = st.sidebar.checkbox(
    "Show holding % on edges",
    value=False,
    help="Turn on only when the graph is not too crowded."
)

G = build_graph(
    selected_sectors=selected_sectors,
    min_conn=min_conn,
    min_holding=min_holding
)

company_count = sum(
    1 for _, data in G.nodes(data=True)
    if data.get("node_type") == "company"
)

shareholder_count = sum(
    1 for _, data in G.nodes(data=True)
    if data.get("node_type") == "shareholder"
)

edge_count = G.number_of_edges()

density = nx.density(G) if G.number_of_nodes() > 1 else 0

# ═══════════════════════ Metrics ═══════════════════════

m1, m2, m3, m4 = st.columns(4)

m1.metric("Companies", company_count)
m2.metric("Stakeholders", shareholder_count)
m3.metric("Relationships", edge_count)
m4.metric("Density", f"{density:.4f}")

# ═══════════════════════ Legend ═══════════════════════

with st.expander("📌 Legend and Methodology", expanded=True):
    st.markdown("""
    **Graph representation**

    - **Nodes / vertices:** SET50 companies and stakeholders  
    - **Edges / links:** Shareholding relationships  
    - **Company nodes:** Colored by sector  
    - **Stakeholder nodes:** Red circles  
    - **Node size:** Degree, or number of connected relationships  
    - **Edge thickness:** Shareholding percentage  
    - **Graph type:** Undirected weighted graph  

    **Interpretation**

    A stakeholder with many connections can be considered a hub in the network.  
    Companies connected to the same stakeholder may have an indirect ownership relationship through common shareholders.
    """)

    sector_items = []

    for sector in sorted(SECTOR_COLORS):
        color = SECTOR_COLORS[sector]
        sector_items.append(f"<span style='color:{color}; font-size:18px;'>●</span> {sector}")

    st.markdown("**Company sector colors:**", unsafe_allow_html=True)
    st.markdown(" · ".join(sector_items), unsafe_allow_html=True)

st.markdown("---")

# ═══════════════════════ Network Visualization ═══════════════════════

st.subheader("🕸️ Network Visualization")

if G.number_of_nodes() == 0:
    st.warning("No data for current filters. Please lower the filter values.")
else:
    net = render_network(
        G=G,
        show_edge_label=show_edge_label
    )

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
        height=790,
        scrolling=True
    )

    os.unlink(html_path)

# ═══════════════════════ Data Tables ═══════════════════════

st.markdown("---")
st.subheader("📊 Network Data Tables")

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "Stakeholder Hubs",
        "All Relationships",
        "Centrality",
        "Company Summary"
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
                "Stakeholder": node,
                "Degree / # Connected Companies": len(connected_companies),
                "Connected Companies": ", ".join(connected_companies)
            })

    if rows:
        df_hubs = pd.DataFrame(rows)
        df_hubs = df_hubs.sort_values(
            "Degree / # Connected Companies",
            ascending=False
        ).reset_index(drop=True)

        st.dataframe(df_hubs, use_container_width=True)
    else:
        st.info("No stakeholder hub data available for the selected filters.")

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
            "Stakeholder / Shareholder": shareholder,
            "Holding %": round(safe_float(data.get("weight", 0)), 4)
        })

    if rows:
        df_edges = pd.DataFrame(rows)
        df_edges = df_edges.sort_values(
            ["Company", "Holding %"],
            ascending=[True, False]
        ).reset_index(drop=True)

        st.dataframe(df_edges, use_container_width=True)
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

        df_cent = pd.DataFrame(rows)
        df_cent = df_cent.sort_values(
            "Degree Centrality",
            ascending=False
        ).reset_index(drop=True)

        st.dataframe(df_cent, use_container_width=True)
    else:
        st.info("Not enough nodes to calculate centrality.")

with tab4:
    rows = []

    for company, sector in SECTORS.items():
        if company in G:
            holders = []

            for neighbor in G.neighbors(company):
                if G.nodes[neighbor].get("node_type") == "shareholder":
                    pct = safe_float(G.edges[company, neighbor].get("weight", 0))
                    holders.append(f"{neighbor} ({pct:.2f}%)")

            rows.append({
                "Company": company,
                "Sector": sector,
                "# Stakeholders shown": len(holders),
                "Stakeholders": ", ".join(holders)
            })

    if rows:
        df_company = pd.DataFrame(rows)
        df_company = df_company.sort_values(
            ["Sector", "Company"],
            ascending=[True, True]
        ).reset_index(drop=True)

        st.dataframe(df_company, use_container_width=True)
    else:
        st.info("No company summary available for the selected filters.")

# ═══════════════════════ Footer ═══════════════════════

st.sidebar.markdown("---")
st.sidebar.markdown(
    "**Data:** Scraped from [SET](https://www.set.or.th)  \n"
    "**Scraper:** `set50.py`  \n"
    "**Course:** Social Network Analysis — HW1  \n"
    "**Stack:** Streamlit · NetworkX · PyVis"
)
