import streamlit as st
import networkx as nx
from pyvis.network import Network
import pandas as pd
import tempfile
import os
import streamlit.components.v1 as components

# ───────────────────────── Page config ─────────────────────────
st.set_page_config(page_title="SET50 Social Network", page_icon="🕸️", layout="wide")

# ───────────────────────── Data ─────────────────────────

COMPANIES = {
    "ADVANC": {"name": "Advanced Info Service", "sector": "ICT"},
    "AOT":    {"name": "Airports of Thailand", "sector": "Transport"},
    "AWC":    {"name": "Asset World Corp", "sector": "Property"},
    "BANPU": {"name": "Banpu", "sector": "Energy"},
    "BBL":   {"name": "Bangkok Bank", "sector": "Banking"},
    "BDMS":  {"name": "Bangkok Dusit Medical", "sector": "Healthcare"},
    "BEM":   {"name": "Bangkok Expressway & Metro", "sector": "Transport"},
    "BH":    {"name": "Bumrungrad Hospital", "sector": "Healthcare"},
    "BJC":   {"name": "Berli Jucker", "sector": "Commerce"},
    "BTS":   {"name": "BTS Group Holdings", "sector": "Transport"},
    "CBG":   {"name": "Carabao Group", "sector": "Food & Bev"},
    "CCET":  {"name": "Cal-Comp Electronics", "sector": "Electronics"},
    "CENTEL":{"name": "Central Plaza Hotel", "sector": "Tourism"},
    "COM7":  {"name": "COM7", "sector": "Commerce"},
    "CPALL": {"name": "CP ALL", "sector": "Commerce"},
    "CPF":   {"name": "Charoen Pokphand Foods", "sector": "Food & Bev"},
    "CPN":   {"name": "Central Pattana", "sector": "Property"},
    "CRC":   {"name": "Central Retail Corp", "sector": "Commerce"},
    "DELTA": {"name": "Delta Electronics", "sector": "Electronics"},
    "EGCO":  {"name": "Electricity Generating", "sector": "Energy"},
    "GPSC":  {"name": "Global Power Synergy", "sector": "Energy"},
    "GULF":  {"name": "Gulf Development", "sector": "Energy"},
    "HMPRO": {"name": "Home Product Center", "sector": "Commerce"},
    "IVL":   {"name": "Indorama Ventures", "sector": "Petrochem"},
    "KBANK": {"name": "Kasikornbank", "sector": "Banking"},
    "KKP":   {"name": "Kiatnakin Phatra Bank", "sector": "Banking"},
    "KTB":   {"name": "Krung Thai Bank", "sector": "Banking"},
    "KTC":   {"name": "Krungthai Card", "sector": "Finance"},
    "LH":    {"name": "Land and Houses", "sector": "Property"},
    "MINT":  {"name": "Minor International", "sector": "Tourism"},
    "MTC":   {"name": "Muangthai Capital", "sector": "Finance"},
    "OR":    {"name": "PTT Oil and Retail", "sector": "Energy"},
    "OSP":   {"name": "Osotspa", "sector": "Food & Bev"},
    "PTT":   {"name": "PTT", "sector": "Energy"},
    "PTTEP": {"name": "PTT Exploration & Production", "sector": "Energy"},
    "PTTGC": {"name": "PTT Global Chemical", "sector": "Petrochem"},
    "RATCH": {"name": "RATCH Group", "sector": "Energy"},
    "SAWAD": {"name": "Srisawad Corporation", "sector": "Finance"},
    "SCB":   {"name": "SCB X", "sector": "Banking"},
    "SCC":   {"name": "Siam Cement", "sector": "Construction"},
    "SCGP":  {"name": "SCG Packaging", "sector": "Packaging"},
    "TCAP":  {"name": "Thanachart Capital", "sector": "Banking"},
    "TIDLOR":{"name": "Tidlor Holdings", "sector": "Finance"},
    "TISCO": {"name": "Tisco Financial Group", "sector": "Banking"},
    "TLI":   {"name": "Thai Life Insurance", "sector": "Insurance"},
    "TOP":   {"name": "Thai Oil", "sector": "Energy"},
    "TRUE":  {"name": "True Corporation", "sector": "ICT"},
    "TTB":   {"name": "TMBThanachart Bank", "sector": "Banking"},
    "TU":    {"name": "Thai Union Group", "sector": "Food & Bev"},
    "WHA":   {"name": "WHA Corporation", "sector": "Property"},
}

# ── 5 Stakeholder relationship types ──────────────────────────

STAKEHOLDER_TYPES = {
    "Major Shareholder Group": {
        "color": "#e74c3c",
        "desc": "Companies sharing a controlling shareholder or conglomerate group",
    },
    "Board Interlock": {
        "color": "#3498db",
        "desc": "Companies sharing common board members or directors",
    },
    "Sector Peer": {
        "color": "#2ecc71",
        "desc": "Companies operating in the same industry sector",
    },
    "Business Partnership": {
        "color": "#f39c12",
        "desc": "Strategic alliances, joint ventures, or supply-chain ties",
    },
    "Institutional Co-Ownership": {
        "color": "#9b59b6",
        "desc": "Companies sharing major institutional investors (e.g., Thai NVDR, Government Pension Fund)",
    },
}

# ── Edges ──────────────────────────────────────────────────────
# Each tuple: (source, target, stakeholder_type, label)

EDGES = [
    # ── Major Shareholder Group ──
    # CP Group
    ("CPALL", "CPF", "Major Shareholder Group", "CP Group"),
    ("CPALL", "TRUE", "Major Shareholder Group", "CP Group"),
    ("CPF", "TRUE", "Major Shareholder Group", "CP Group"),
    ("CPALL", "CCET", "Major Shareholder Group", "CP Group"),
    ("CPF", "CCET", "Major Shareholder Group", "CP Group"),
    # PTT Group
    ("PTT", "PTTEP", "Major Shareholder Group", "PTT Group"),
    ("PTT", "PTTGC", "Major Shareholder Group", "PTT Group"),
    ("PTT", "TOP", "Major Shareholder Group", "PTT Group"),
    ("PTT", "OR", "Major Shareholder Group", "PTT Group"),
    ("PTT", "GPSC", "Major Shareholder Group", "PTT Group"),
    ("PTTEP", "PTTGC", "Major Shareholder Group", "PTT Group"),
    ("PTTGC", "TOP", "Major Shareholder Group", "PTT Group"),
    ("OR", "TOP", "Major Shareholder Group", "PTT Group"),
    # Central Group
    ("CPN", "CRC", "Major Shareholder Group", "Central Group"),
    ("CPN", "CENTEL", "Major Shareholder Group", "Central Group"),
    ("CRC", "CENTEL", "Major Shareholder Group", "Central Group"),
    ("CRC", "HMPRO", "Major Shareholder Group", "Central Group"),
    # TCC Group (Charoen Sirivadhanabhakdi)
    ("BJC", "AWC", "Major Shareholder Group", "TCC Group"),
    # SCG Group
    ("SCC", "SCGP", "Major Shareholder Group", "SCG Group"),
    # KTB + KTC (state-owned banking)
    ("KTB", "KTC", "Major Shareholder Group", "Krung Thai Group"),
    # Thanachart
    ("TCAP", "TTB", "Major Shareholder Group", "Thanachart-TMB"),
    ("TCAP", "TIDLOR", "Major Shareholder Group", "Thanachart Group"),
    # BTS + BEM (overlap via major shareholders / Sino-Thai)
    ("BTS", "BEM", "Major Shareholder Group", "Transport Conglom."),

    # ── Board Interlock ──
    ("PTT", "EGCO", "Board Interlock", "Shared directors"),
    ("PTT", "RATCH", "Board Interlock", "Shared directors"),
    ("KBANK", "MINT", "Board Interlock", "Shared directors"),
    ("SCB", "SCC", "Board Interlock", "Shared directors"),
    ("BBL", "IVL", "Board Interlock", "Shared directors"),
    ("BDMS", "BH", "Board Interlock", "Shared directors"),
    ("KTB", "AOT", "Board Interlock", "Shared directors"),
    ("CPF", "CPALL", "Board Interlock", "Shared directors"),
    ("CPN", "CRC", "Board Interlock", "Shared directors"),
    ("GULF", "GPSC", "Board Interlock", "Shared directors"),
    ("BANPU", "RATCH", "Board Interlock", "Shared directors"),
    ("TTB", "TCAP", "Board Interlock", "Shared directors"),
    ("LH", "TCAP", "Board Interlock", "Shared directors"),
    ("TISCO", "KKP", "Board Interlock", "Shared directors"),
    ("TLI", "SCB", "Board Interlock", "Shared directors"),

    # ── Sector Peer ──
    # Banking
    ("BBL", "KBANK", "Sector Peer", "Banking"),
    ("KBANK", "KTB", "Sector Peer", "Banking"),
    ("KTB", "SCB", "Sector Peer", "Banking"),
    ("SCB", "TTB", "Sector Peer", "Banking"),
    ("TTB", "TISCO", "Sector Peer", "Banking"),
    ("TISCO", "KKP", "Sector Peer", "Banking"),
    ("KKP", "BBL", "Sector Peer", "Banking"),
    ("BBL", "SCB", "Sector Peer", "Banking"),
    # Energy
    ("PTT", "BANPU", "Sector Peer", "Energy"),
    ("BANPU", "GULF", "Sector Peer", "Energy"),
    ("GULF", "EGCO", "Sector Peer", "Energy"),
    ("EGCO", "RATCH", "Sector Peer", "Energy"),
    ("GPSC", "RATCH", "Sector Peer", "Energy"),
    # Food & Bev
    ("CPF", "TU", "Sector Peer", "Food & Bev"),
    ("TU", "OSP", "Sector Peer", "Food & Bev"),
    ("OSP", "CBG", "Sector Peer", "Food & Bev"),
    ("CBG", "CPF", "Sector Peer", "Food & Bev"),
    # Healthcare
    ("BDMS", "BH", "Sector Peer", "Healthcare"),
    # Transport
    ("AOT", "BEM", "Sector Peer", "Transport"),
    ("BEM", "BTS", "Sector Peer", "Transport"),
    ("BTS", "AOT", "Sector Peer", "Transport"),
    # Commerce
    ("CPALL", "CRC", "Sector Peer", "Commerce"),
    ("CRC", "HMPRO", "Sector Peer", "Commerce"),
    ("HMPRO", "COM7", "Sector Peer", "Commerce"),
    ("COM7", "BJC", "Sector Peer", "Commerce"),
    # Property
    ("AWC", "LH", "Sector Peer", "Property"),
    ("LH", "WHA", "Sector Peer", "Property"),
    ("WHA", "CPN", "Sector Peer", "Property"),
    # Finance
    ("KTC", "MTC", "Sector Peer", "Finance"),
    ("MTC", "SAWAD", "Sector Peer", "Finance"),
    ("SAWAD", "TIDLOR", "Sector Peer", "Finance"),
    # ICT
    ("ADVANC", "TRUE", "Sector Peer", "ICT"),
    # Electronics
    ("DELTA", "CCET", "Sector Peer", "Electronics"),
    # Petrochem
    ("IVL", "PTTGC", "Sector Peer", "Petrochem"),
    # Tourism
    ("MINT", "CENTEL", "Sector Peer", "Tourism"),

    # ── Business Partnership ──
    ("OR", "CPALL", "Business Partnership", "Retail fuel & convenience"),
    ("PTT", "GULF", "Business Partnership", "Power purchase"),
    ("SCC", "WHA", "Business Partnership", "Industrial estate supply"),
    ("ADVANC", "DELTA", "Business Partnership", "Telecom infrastructure"),
    ("TRUE", "BTS", "Business Partnership", "Advertising & telecom on transit"),
    ("AOT", "MINT", "Business Partnership", "Airport F&B concessions"),
    ("AOT", "ADVANC", "Business Partnership", "Airport telecom services"),
    ("CPALL", "OR", "Business Partnership", "Co-located stores"),
    ("BDMS", "TLI", "Business Partnership", "Health insurance tie-up"),
    ("KBANK", "TIDLOR", "Business Partnership", "Fintech lending"),
    ("SCB", "SAWAD", "Business Partnership", "Micro-lending partnership"),
    ("CPN", "HMPRO", "Business Partnership", "Retail co-location"),
    ("BEM", "GULF", "Business Partnership", "Metro power supply"),
    ("CPF", "OR", "Business Partnership", "Food supply to retail"),
    ("TU", "BJC", "Business Partnership", "Distribution partnership"),
    ("GPSC", "SCC", "Business Partnership", "Industrial power supply"),
    ("BANPU", "EGCO", "Business Partnership", "JV power plants"),
    ("IVL", "TOP", "Business Partnership", "Petrochemical feedstock"),
    ("PTTGC", "IVL", "Business Partnership", "Petrochemical supply"),
    ("KTB", "TLI", "Business Partnership", "Bancassurance"),
    ("BBL", "TLI", "Business Partnership", "Bancassurance"),

    # ── Institutional Co-Ownership ──
    # Thai NVDR (top holder in many SET50 stocks)
    ("ADVANC", "KBANK", "Institutional Co-Ownership", "Thai NVDR"),
    ("KBANK", "PTT", "Institutional Co-Ownership", "Thai NVDR"),
    ("PTT", "AOT", "Institutional Co-Ownership", "Thai NVDR"),
    ("AOT", "BDMS", "Institutional Co-Ownership", "Thai NVDR"),
    ("BDMS", "CPN", "Institutional Co-Ownership", "Thai NVDR"),
    ("CPN", "ADVANC", "Institutional Co-Ownership", "Thai NVDR"),
    # Ministry of Finance (state enterprises)
    ("KTB", "PTT", "Institutional Co-Ownership", "Ministry of Finance"),
    ("PTT", "AOT", "Institutional Co-Ownership", "Ministry of Finance"),
    ("KTB", "AOT", "Institutional Co-Ownership", "Ministry of Finance"),
    ("KTB", "TTB", "Institutional Co-Ownership", "Ministry of Finance"),
    ("BEM", "AOT", "Institutional Co-Ownership", "Ministry of Finance"),
    # Government Pension Fund (GPF)
    ("BBL", "ADVANC", "Institutional Co-Ownership", "Gov. Pension Fund"),
    ("ADVANC", "CPALL", "Institutional Co-Ownership", "Gov. Pension Fund"),
    ("CPALL", "SCB", "Institutional Co-Ownership", "Gov. Pension Fund"),
    ("SCB", "DELTA", "Institutional Co-Ownership", "Gov. Pension Fund"),
    # Social Security Office (SSO)
    ("KBANK", "BBL", "Institutional Co-Ownership", "Social Security Office"),
    ("BBL", "SCB", "Institutional Co-Ownership", "Social Security Office"),
    ("SCB", "KTB", "Institutional Co-Ownership", "Social Security Office"),
    # Vanguard / Foreign funds
    ("DELTA", "ADVANC", "Institutional Co-Ownership", "Vanguard Fund"),
    ("ADVANC", "GULF", "Institutional Co-Ownership", "Vanguard Fund"),
    ("GULF", "BDMS", "Institutional Co-Ownership", "Vanguard Fund"),
]

# ── Sector colors for nodes ──
SECTOR_COLORS = {
    "Banking":      "#1a5276",
    "Energy":       "#d35400",
    "Commerce":     "#27ae60",
    "ICT":          "#8e44ad",
    "Transport":    "#2980b9",
    "Healthcare":   "#c0392b",
    "Food & Bev":   "#16a085",
    "Property":     "#f1c40f",
    "Electronics":  "#2c3e50",
    "Petrochem":    "#7f8c8d",
    "Finance":      "#e67e22",
    "Tourism":      "#e74c3c",
    "Construction": "#95a5a6",
    "Packaging":    "#bdc3c7",
    "Insurance":    "#1abc9c",
}

# ───────────────────────── Build Graph ─────────────────────────

def build_graph(selected_types, selected_sectors):
    G = nx.Graph()

    # Filter companies by sector
    filtered = {
        k: v for k, v in COMPANIES.items() if v["sector"] in selected_sectors
    }

    # Add nodes
    for sym, info in filtered.items():
        G.add_node(
            sym,
            label=sym,
            title=f"{info['name']}\nSector: {info['sector']}",
            sector=info["sector"],
        )

    # Add edges
    for src, tgt, stype, label in EDGES:
        if stype in selected_types and src in filtered and tgt in filtered:
            G.add_edge(src, tgt, stakeholder=stype, label=label)

    return G


def graph_to_pyvis(G, height="720px", width="100%", physics_enabled=True):
    net = Network(
        height=height,
        width=width,
        bgcolor="#0e1117",
        font_color="white",
        directed=False,
        cdn_resources="remote",
    )

    # Add nodes with sector-based coloring & sizing by degree
    degrees = dict(G.degree())
    max_deg = max(degrees.values()) if degrees else 1

    for node in G.nodes(data=True):
        sym = node[0]
        data = node[1]
        sector = data.get("sector", "")
        color = SECTOR_COLORS.get(sector, "#888888")
        deg = degrees.get(sym, 1)
        size = 15 + (deg / max_deg) * 35

        net.add_node(
            sym,
            label=sym,
            title=data.get("title", sym),
            color=color,
            size=size,
            font={"size": 14, "color": "white"},
        )

    # Add edges with stakeholder-type coloring
    for u, v, data in G.edges(data=True):
        stype = data.get("stakeholder", "")
        color = STAKEHOLDER_TYPES.get(stype, {}).get("color", "#555555")
        net.add_edge(
            u,
            v,
            title=f"{stype}: {data.get('label', '')}",
            color=color,
            width=2,
        )

    # Physics
    if physics_enabled:
        net.force_atlas_2based(
            gravity=-80,
            central_gravity=0.01,
            spring_length=150,
            spring_strength=0.05,
            damping=0.4,
        )
    else:
        net.toggle_physics(False)

    net.set_options("""
    {
      "interaction": {
        "hover": true,
        "tooltipDelay": 100,
        "navigationButtons": true,
        "keyboard": true
      }
    }
    """)

    return net


# ───────────────────────── Streamlit UI ─────────────────────────

st.title("🕸️ SET50 Social Network Analysis")
st.markdown(
    "Interactive visualization of relationships between **50 listed companies** "
    "on the Stock Exchange of Thailand (SET) across **5 stakeholder types**."
)

# Sidebar filters
st.sidebar.header("🔧 Filters")

st.sidebar.subheader("Stakeholder Types")
selected_types = []
for stype, info in STAKEHOLDER_TYPES.items():
    if st.sidebar.checkbox(stype, value=True, key=stype):
        selected_types.append(stype)

st.sidebar.subheader("Sectors")
all_sectors = sorted(set(v["sector"] for v in COMPANIES.values()))
selected_sectors = st.sidebar.multiselect(
    "Select sectors to display",
    options=all_sectors,
    default=all_sectors,
)

st.sidebar.subheader("Layout")
physics = st.sidebar.checkbox("Enable physics simulation", value=True)

# Build & display
G = build_graph(selected_types, selected_sectors)

# ── Metrics row ──
col1, col2, col3, col4 = st.columns(4)
col1.metric("Nodes (Companies)", G.number_of_nodes())
col2.metric("Edges (Relationships)", G.number_of_edges())
col3.metric("Avg Degree", f"{(2 * G.number_of_edges() / max(G.number_of_nodes(), 1)):.1f}")
density = nx.density(G) if G.number_of_nodes() > 1 else 0
col4.metric("Density", f"{density:.3f}")

# ── Legend ──
st.markdown("### Legend")
leg_cols = st.columns(5)
for idx, (stype, info) in enumerate(STAKEHOLDER_TYPES.items()):
    with leg_cols[idx]:
        st.markdown(
            f"<span style='color:{info['color']}; font-size:24px'>●</span> "
            f"**{stype}**<br><small>{info['desc']}</small>",
            unsafe_allow_html=True,
        )

st.markdown("---")

# ── Network visualization ──
if G.number_of_nodes() == 0:
    st.warning("No companies match the current filters.")
else:
    net = graph_to_pyvis(G, physics_enabled=physics)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w") as f:
        net.save_graph(f.name)
        html_path = f.name

    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    components.html(html_content, height=740, scrolling=True)
    os.unlink(html_path)

# ── Detailed tables ──
st.markdown("---")
st.markdown("### 📊 Network Details")

tab1, tab2, tab3 = st.tabs(["Company List", "Relationship Table", "Degree Centrality"])

with tab1:
    rows = []
    for sym, info in sorted(COMPANIES.items()):
        if info["sector"] in selected_sectors:
            deg = G.degree(sym) if sym in G else 0
            rows.append({"Symbol": sym, "Company": info["name"], "Sector": info["sector"], "Connections": deg})
    if rows:
        df = pd.DataFrame(rows).sort_values("Connections", ascending=False).reset_index(drop=True)
        df.index += 1
        st.dataframe(df, use_container_width=True)

with tab2:
    edge_rows = []
    for u, v, data in G.edges(data=True):
        edge_rows.append({
            "Company A": u,
            "Company B": v,
            "Stakeholder Type": data.get("stakeholder", ""),
            "Detail": data.get("label", ""),
        })
    if edge_rows:
        edf = pd.DataFrame(edge_rows).sort_values("Stakeholder Type").reset_index(drop=True)
        edf.index += 1
        st.dataframe(edf, use_container_width=True)
    else:
        st.info("No edges to display.")

with tab3:
    if G.number_of_nodes() > 0:
        cent = nx.degree_centrality(G)
        betw = nx.betweenness_centrality(G)
        close = nx.closeness_centrality(G)
        cent_rows = []
        for sym in cent:
            cent_rows.append({
                "Symbol": sym,
                "Company": COMPANIES[sym]["name"],
                "Degree Centrality": round(cent[sym], 4),
                "Betweenness Centrality": round(betw[sym], 4),
                "Closeness Centrality": round(close[sym], 4),
            })
        cdf = pd.DataFrame(cent_rows).sort_values("Degree Centrality", ascending=False).reset_index(drop=True)
        cdf.index += 1
        st.dataframe(cdf, use_container_width=True)

# ── Sidebar info ──
st.sidebar.markdown("---")
st.sidebar.markdown(
    "**Data Source:** [SET50 H1/2026](https://www.set.or.th)  \n"
    "**Course:** Social Network Analysis (Ch1)  \n"
    "**Built with:** Streamlit · NetworkX · PyVis"
)
