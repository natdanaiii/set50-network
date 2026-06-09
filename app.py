import streamlit as st
import networkx as nx
from pyvis.network import Network
import pandas as pd
import json
import os
import tempfile
import streamlit.components.v1 as components
from collections import Counter
import math

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
    "ADVANC":"ICT","AOT":"Transport","AWC":"Property","BANPU":"Energy",
    "BBL":"Banking","BDMS":"Healthcare","BEM":"Transport","BH":"Healthcare",
    "BJC":"Commerce","BTS":"Transport","CBG":"Food & Bev","CCET":"Electronics",
    "CENTEL":"Tourism","COM7":"Commerce","CPALL":"Commerce","CPF":"Food & Bev",
    "CPN":"Property","CRC":"Commerce","DELTA":"Electronics","EGCO":"Energy",
    "GPSC":"Energy","GULF":"Energy","HMPRO":"Commerce","IVL":"Petrochem",
    "KBANK":"Banking","KKP":"Banking","KTB":"Banking","KTC":"Finance",
    "LH":"Property","MINT":"Tourism","MTC":"Finance","OR":"Energy",
    "OSP":"Food & Bev","PTT":"Energy","PTTEP":"Energy","PTTGC":"Petrochem",
    "RATCH":"Energy","SAWAD":"Finance","SCB":"Banking","SCC":"Construction",
    "SCGP":"Packaging","TCAP":"Banking","TIDLOR":"Finance","TISCO":"Banking",
    "TLI":"Insurance","TOP":"Energy","TRUE":"ICT","TTB":"Banking",
    "TU":"Food & Bev","WHA":"Property",
}

SECTOR_COLORS = {
    "Banking":"#4FC3F7",
    "Energy":"#FFB74D",
    "Commerce":"#81C784",
    "ICT":"#BA68C8",
    "Transport":"#64B5F6",
    "Healthcare":"#E57373",
    "Food & Bev":"#4DB6AC",
    "Property":"#FFF176",
    "Electronics":"#90A4AE",
    "Petrochem":"#B0BEC5",
    "Finance":"#FF8A65",
    "Tourism":"#F06292",
    "Construction":"#A1887F",
    "Packaging":"#BDBDBD",
    "Insurance":"#26C6DA",
}

# ═══════════════════════ Helper Functions ═══════════════════════

def safe_pct(value):
    try:
        return float(value)
    except Exception:
        return 0.0

def build_graph(selected_sectors, min_conn, min_holding):
    G = nx.Graph()

    selected_companies = [
        sym for sym, sec in SECTORS.items()
        if sec in selected_sectors
    ]

    edges = []
    for sym in selected_companies:
        for h in raw.get(sym, []):
            sh_name = h.get("name", "").strip()
            pct = safe_pct(h.get("pct", 0))

            if sh_name and pct >= min_holding:
                edges.append((sym, sh_name, pct))

    sh_count = Counter(sh for _, sh, _ in edges)
    valid_shareholders = {
        sh for sh, count in sh_count.items()
        if count >= min_conn
    }

    for sym in selected_companies:
        company_edges = [
            (s, sh, pct) for s, sh, pct in edges
            if s == sym and sh in valid_shareholders
        ]

        if company_edges:
            G.add_node(
                sym,
                node_type="company",
                sector=SECTORS[sym],
                level=0
            )

    for sym, sh, pct in edges:
        if sh in valid_shareholders and sym in G:
            if sh not in G:
                G.add_node(
                    sh,
                    node_type="shareholder",
                    sector="",
                    level=1
                )

            G.add_edge(
                sym,
                sh,
                weight=pct
            )

    return G

def render_network(G, layout_mode="Left-right", show_edge_label=False, physics_on=False):
    net = Network(
        height="780px",
        width="100%",
        bgcolor="#0e1117",
        font_color="white",
        directed=False,
        cdn_resources="remote"
    )

    degs = dict(G.degree())
    max_d = max(degs.values()) if degs else 1

    for node, data in G.nodes(data=True):
        deg = degs.get(node, 1)
        node_type = data.get("node_type", "")

        if node_type == "company":
            sector = data.get("sector", "")
            color = SECTOR_COLORS.get(sector, "#888888")
            size = 18 + (deg / max_d) * 20

            title = (
                f"<b>Company:</b> {node}<br>"
                f"<b>Sector:</b> {sector}<br>"
                f"<b>Connections:</b> {deg}"
            )

            net.add_node(
                node,
                label=node,
                title=title,
                color={
                    "background": color,
                    "border": "#FFFFFF",
                    "highlight": {
                        "background": color,
                        "border": "#FFFFFF"
                    }
                },
                size=size,
                shape="dot",
                level=0,
                font={
                    "size": 16,
                    "color": "white",
                    "face": "arial",
                    "strokeWidth": 3,
                    "strokeColor": "#000000"
                }
            )

        else:
            size = 14 + (deg / max_d) * 35
            short_label = node if len(node) <= 24 else node[:24] + "..."

            title = (
                f"<b>Shareholder / Stakeholder:</b> {node}<br>"
                f"<b>Connected companies:</b> {deg}"
            )

            net.add_node(
                node,
                label=short_label,
                title=title,
                color={
                    "background": "#FF6B6B",
                    "border": "#FFFFFF",
                    "highlight": {
                        "background": "#FF8A80",
                        "border": "#FFFFFF"
                    }
                },
                size=size,
                shape="diamond",
                level=1,
                font={
                    "size": 12,
                    "color": "white",
                    "face": "arial",
                    "strokeWidth": 3,
                    "strokeColor": "#000000"
                }
            )

    for u, v, data in G.edges(data=True):
        pct = safe_pct(data.get("weight", 0))

        company = u if G.nodes[u].get("node_type") == "company" else v
        shareholder = v if company == u else u

        sector = G.nodes[company].get("sector", "")
        edge_color = SECTOR_COLORS.get(sector, "#CCCCCC")

        width = 1.5 + math.log1p(pct) * 1.8
        edge_label = f"{pct:.1f}%" if show_edge_label else ""

        net.add_edge(
            company,
            shareholder,
            value=pct,
            width=width,
            label=edge_label,
            title=(
                f"<b>{company}</b> → <b>{shareholder}</b><br>"
                f"Shareholding: {pct:.2f}%"
            ),
            color={
                "color": edge_color,
                "opacity": 0.55,
                "highlight": "#FFFFFF",
                "hover": "#FFFFFF"
            },
            smooth={
                "enabled": True,
                "type": "continuous",
                "roundness": 0.25
            },
            font={
                "size": 10,
                "color": "white",
                "strokeWidth": 3,
                "strokeColor": "#000000"
            }
        )

    if layout_mode == "Left-right":
        options = """
        {
          "layout": {
            "hierarchical": {
              "enabled": true,
              "direction": "LR",
              "sortMethod": "directed",
              "levelSeparation": 420,
              "nodeSpacing": 150,
              "treeSpacing": 220,
              "blockShifting": true,
              "edgeMinimization": true,
              "parentCentralization": true
            }
          },
          "interaction": {
            "hover": true,
            "tooltipDelay": 100,
            "navigationButtons": true,
            "keyboard": true,
            "multiselect": true
          },
          "physics": {
            "enabled": false
          },
          "edges": {
            "selectionWidth": 4,
            "hoverWidth": 3
          }
        }
        """
    else:
        options = """
        {
          "layout": {
            "improvedLayout": true
          },
          "interaction": {
            "hover": true,
            "tooltipDelay": 100,
            "navigationButtons": true,
            "keyboard": true,
            "multiselect": true
          },
          "physics": {
            "enabled": true,
            "forceAtlas2Based": {
              "gravitationalConstant": -80,
              "centralGravity": 0.01,
              "springLength": 180,
              "springConstant": 0.05,
              "damping": 0.45
            },
            "solver": "forceAtlas2Based",
            "stabilization": {
              "enabled": true,
              "iterations": 150
            }
          },
          "edges": {
            "selectionWidth": 4,
            "hoverWidth": 3
          }
        }
        """

    if physics_on and layout_mode != "Left-right":
        net.force_atlas_2based(
            gravity=-80,
            central_gravity=0.01,
            spring_length=180,
            spring_strength=0.05,
            damping=0.45
        )

    net.set_options(options)
    return net

# ═══════════════════════ UI ═══════════════════════

st.title("🕸️ SET50 Shareholder Network")

st.caption(
    "This application visualizes a bipartite social network between SET50 listed companies "
    "and their top 5 major shareholders as stakeholders. Data was collected from the Stock Exchange of Thailand (SET)."
)

st.info(
    "How to read this network: company nodes are shown on the left, shareholder/stakeholder nodes are shown on the right. "
    "Each edge represents a shareholding relationship, and thicker edges represent higher shareholding percentage."
)

# ═══════════════════════ Sidebar Filters ═══════════════════════

st.sidebar.header("🔧 Network Filters")

all_sectors = sorted(set(SECTORS.values()))

sel_sectors = st.sidebar.multiselect(
    "Select sectors",
    all_sectors,
    default=all_sectors
)

min_c = st.sidebar.slider(
    "Minimum companies per shareholder",
    min_value=1,
    max_value=20,
    value=1,
    help="Use 1 to show all top shareholders. Increase this value to focus on hub shareholders."
)

min_holding = st.sidebar.slider(
    "Minimum holding percentage",
    min_value=0.0,
    max_value=50.0,
    value=0.0,
    step=0.5,
    help="Filter out small shareholding relationships."
)

layout_mode = st.sidebar.radio(
    "Network layout",
    ["Left-right", "Force-directed"],
    index=0,
    help="Left-right layout is easier to read for company-shareholder relationships."
)

show_edge_label = st.sidebar.checkbox(
    "Show holding % on edges",
    value=False,
    help="Turn on only when the graph is not too crowded."
)

physics = st.sidebar.checkbox(
    "Enable physics",
    value=False,
    help="Useful only for force-directed layout."
)

G = build_graph(sel_sectors, min_c, min_holding)

n_comp = sum(
    1 for _, data in G.nodes(data=True)
    if data.get("node_type") == "company"
)

n_sh = sum(
    1 for _, data in G.nodes(data=True)
    if data.get("node_type") == "shareholder"
)

# ═══════════════════════ Metrics ═══════════════════════

c1, c2, c3, c4 = st.columns(4)

c1.metric("Companies", n_comp)
c2.metric("Shareholders", n_sh)
c3.metric("Connections", G.number_of_edges())
c4.metric(
    "Density",
    f"{nx.density(G):.4f}" if G.number_of_nodes() > 1 else "0"
)

# ═══════════════════════ Legend ═══════════════════════

with st.expander("📌 Legend and Methodology", expanded=True):
    st.markdown("""
    **Network design**

    - **Circle nodes:** SET50 listed companies  
    - **Diamond nodes:** Top 5 major shareholders / stakeholders  
    - **Edges:** Shareholding relationships  
    - **Edge thickness:** Shareholding percentage  
    - **Company color:** Business sector  
    - **Node size:** Number of connections  

    **Interpretation**

    A shareholder connected to many companies can be interpreted as a network hub.  
    Companies sharing the same shareholder may be indirectly connected through common ownership.
    """)

    sector_parts = []
    for sector in sorted(SECTOR_COLORS):
        color = SECTOR_COLORS[sector]
        sector_parts.append(f"<span style='color:{color}'>●</span> {sector}")

    st.markdown("**Sector colors:**", unsafe_allow_html=True)
    st.markdown(" · ".join(sector_parts), unsafe_allow_html=True)

st.markdown("---")

# ═══════════════════════ Network Visualization ═══════════════════════

if G.number_of_nodes() == 0:
    st.warning("No data for current filters. Please lower the filter values.")
else:
    net = render_network(
        G,
        layout_mode=layout_mode,
        show_edge_label=show_edge_label,
        physics_on=physics
    )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8") as f:
        net.save_graph(f.name)
        html_path = f.name

    with open(html_path, "r", encoding="utf-8") as f:
        components.html(f.read(), height=800, scrolling=True)

    os.unlink(html_path)

# ═══════════════════════ Data Tables ═══════════════════════

st.markdown("---")
st.subheader("📊 Network Data Tables")

tab1, tab2, tab3 = st.tabs(
    ["Top Shareholders / Hubs", "All Connections", "Centrality"]
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
                "Shareholder": node,
                "# Companies": len(connected_companies),
                "Connected Companies": ", ".join(connected_companies)
            })

    if rows:
        df_hubs = pd.DataFrame(rows)
        df_hubs = df_hubs.sort_values(
            "# Companies",
            ascending=False
        ).reset_index(drop=True)

        st.dataframe(df_hubs, use_container_width=True)
    else:
        st.info("No shareholder hub data available for the selected filters.")

with tab2:
    rows = []

    for u, v, data in G.edges(data=True):
        company = u if G.nodes[u].get("node_type") == "company" else v
        shareholder = v if G.nodes[v].get("node_type") == "shareholder" else u

        rows.append({
            "Company": company,
            "Sector": SECTORS.get(company, ""),
            "Shareholder": shareholder,
            "Holding %": data.get("weight", 0)
        })

    if rows:
        df_edges = pd.DataFrame(rows)
        df_edges = df_edges.sort_values(
            ["Company", "Holding %"],
            ascending=[True, False]
        ).reset_index(drop=True)

        st.dataframe(df_edges, use_container_width=True)
    else:
        st.info("No connection data available for the selected filters.")

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

# ═══════════════════════ Footer ═══════════════════════

st.sidebar.markdown("---")
st.sidebar.markdown(
    "**Data:** Scraped from [SET](https://www.set.or.th)  \n"
    "**Scraper:** `set50.py`  \n"
    "**Course:** Social Network Analysis — HW1  \n"
    "**Stack:** Streamlit · NetworkX · PyVis"
)
