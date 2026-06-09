import streamlit as st
import networkx as nx
from pyvis.network import Network
import pandas as pd
import json, os, tempfile
import streamlit.components.v1 as components
from collections import Counter

st.set_page_config(page_title="SET50 Shareholder Network", page_icon="🕸️", layout="wide")

# ═══════════════════════ Load Data ═══════════════════════

DATA_PATH = os.path.join(os.path.dirname(__file__), "shareholders.json")

@st.cache_data
def load_data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

raw = load_data()

# SET50 sector mapping (H1/2026)
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
    "Banking":"#1a5276","Energy":"#d35400","Commerce":"#27ae60",
    "ICT":"#8e44ad","Transport":"#2980b9","Healthcare":"#c0392b",
    "Food & Bev":"#16a085","Property":"#f1c40f","Electronics":"#2c3e50",
    "Petrochem":"#7f8c8d","Finance":"#e67e22","Tourism":"#e74c3c",
    "Construction":"#95a5a6","Packaging":"#bdc3c7","Insurance":"#1abc9c",
}

# ═══════════════════════ Build Graph ═══════════════════════

def build_graph(selected_sectors, min_conn):
    G = nx.Graph()

    filtered = {s for s, sec in SECTORS.items() if sec in selected_sectors}
    edges = []
    for sym in filtered:
        for h in raw.get(sym, []):
            edges.append((sym, h["name"], h["pct"]))

    sh_count = Counter(sh for _, sh, _ in edges)
    valid_sh = {sh for sh, c in sh_count.items() if c >= min_conn}

    for sym in filtered:
        has_edge = any(h["name"] in valid_sh for h in raw.get(sym, []))
        if has_edge or min_conn <= 1:
            G.add_node(sym, node_type="company", sector=SECTORS[sym])

    for sym, sh, pct in edges:
        if sh in valid_sh and sym in G:
            if sh not in G:
                G.add_node(sh, node_type="shareholder", sector="")
            G.add_edge(sym, sh, weight=pct)

    return G

def render_network(G, physics_on=True):
    net = Network(height="720px", width="100%", bgcolor="#0e1117",
                  font_color="white", directed=False, cdn_resources="remote")

    degs = dict(G.degree())
    max_d = max(degs.values()) if degs else 1

    for n, d in G.nodes(data=True):
        deg = degs.get(n, 1)
        if d.get("node_type") == "company":
            color = SECTOR_COLORS.get(d.get("sector",""), "#888")
            size = 12 + (deg / max_d) * 22
            title = f"🏢 {n}\nSector: {d.get('sector','')}\nConnections: {deg}"
            net.add_node(n, label=n, title=title, color=color,
                         size=size, shape="dot",
                         font={"size":12,"color":"white"})
        else:
            size = 15 + (deg / max_d) * 45
            title = f"👤 {n}\nHolds shares in {deg} companies"
            net.add_node(n, label=n[:30], title=title, color="#FF6B6B",
                         size=size, shape="diamond",
                         font={"size":10,"color":"white"})

    for u, v, d in G.edges(data=True):
        w = d.get("weight", 1)
        width = max(0.5, (w / 50) * 5)
        net.add_edge(u, v, title=f"{w:.2f}%", width=width,
                     color="rgba(200,200,200,0.2)")

    if physics_on:
        net.force_atlas_2based(gravity=-100, central_gravity=0.008,
                               spring_length=180, spring_strength=0.04,
                               damping=0.4)
    else:
        net.toggle_physics(False)

    net.set_options('{"interaction":{"hover":true,"tooltipDelay":100,"navigationButtons":true,"keyboard":true}}')
    return net

# ═══════════════════════ UI ═══════════════════════

st.title("🕸️ SET50 Shareholder Network")
st.caption("Social network mapping 50 SET-listed companies to their top 5 major shareholders — data scraped from set.or.th")

# Sidebar
st.sidebar.header("🔧 Filters")
all_sectors = sorted(set(SECTORS.values()))
sel_sectors = st.sidebar.multiselect("Sectors", all_sectors, default=all_sectors)
min_c = st.sidebar.slider("Min companies per shareholder", 1, 20, 2,
                           help="Show only shareholders connected to ≥ N companies")
physics = st.sidebar.checkbox("Enable physics", True)

G = build_graph(sel_sectors, min_c)
n_comp = sum(1 for _,d in G.nodes(data=True) if d.get("node_type")=="company")
n_sh   = sum(1 for _,d in G.nodes(data=True) if d.get("node_type")=="shareholder")

# Metrics
c1,c2,c3,c4 = st.columns(4)
c1.metric("Companies", n_comp)
c2.metric("Shareholders", n_sh)
c3.metric("Connections", G.number_of_edges())
c4.metric("Density", f"{nx.density(G):.4f}" if G.number_of_nodes()>1 else "0")

# Legend
with st.expander("Legend", expanded=True):
    lc1, lc2 = st.columns(2)
    with lc1:
        st.markdown("**Node shape:** ⬤ Company (color = sector) · ◆ Shareholder (red)")
    with lc2:
        parts = []
        for s in sorted(SECTOR_COLORS):
            c = SECTOR_COLORS[s]
            parts.append(f"<span style='color:{c}'>●</span> {s}")
        st.markdown(" · ".join(parts), unsafe_allow_html=True)

st.markdown("---")

# Network
if G.number_of_nodes() == 0:
    st.warning("No data for current filters. Lower the minimum connections slider.")
else:
    net = render_network(G, physics)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w") as f:
        net.save_graph(f.name)
        p = f.name
    with open(p, "r", encoding="utf-8") as f:
        components.html(f.read(), height=740, scrolling=True)
    os.unlink(p)

# Data tables
st.markdown("---")
st.subheader("📊 Data Tables")
t1, t2, t3 = st.tabs(["Top Shareholders (Hubs)", "All Connections", "Centrality"])

with t1:
    rows = []
    for n, d in G.nodes(data=True):
        if d.get("node_type") == "shareholder":
            nbrs = sorted(nb for nb in G.neighbors(n) if G.nodes[nb].get("node_type")=="company")
            rows.append({"Shareholder": n, "# Companies": len(nbrs), "Connected to": ", ".join(nbrs)})
    if rows:
        st.dataframe(pd.DataFrame(rows).sort_values("# Companies", ascending=False).reset_index(drop=True),
                     use_container_width=True)

with t2:
    rows = []
    for u, v, d in G.edges(data=True):
        comp = u if G.nodes[u].get("node_type")=="company" else v
        sh   = v if G.nodes[v].get("node_type")=="shareholder" else u
        rows.append({"Company": comp, "Sector": SECTORS.get(comp,""),
                     "Shareholder": sh, "Holding %": d.get("weight",0)})
    if rows:
        st.dataframe(pd.DataFrame(rows).sort_values(["Company","Holding %"], ascending=[True,False]).reset_index(drop=True),
                     use_container_width=True)

with t3:
    if G.number_of_nodes() > 1:
        dc = nx.degree_centrality(G)
        bc = nx.betweenness_centrality(G)
        cc = nx.closeness_centrality(G)
        rows = [{"Node": n, "Type": G.nodes[n].get("node_type",""),
                 "Degree": round(dc[n],4), "Betweenness": round(bc[n],4),
                 "Closeness": round(cc[n],4)} for n in dc]
        st.dataframe(pd.DataFrame(rows).sort_values("Degree", ascending=False).reset_index(drop=True),
                     use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.markdown("**Data:** Scraped from [SET](https://www.set.or.th)  \n"
                    "**Scraper:** `set50.py` (Selenium)  \n"
                    "**Course:** Social Network Analysis — HW1  \n"
                    "**Stack:** Streamlit · NetworkX · PyVis")
