def render_network(G, physics_on=True):
    net = Network(
        height="720px",
        width="100%",
        bgcolor="#0e1117",
        font_color="white",
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
                    "border": "#ffffff",
                    "highlight": {
                        "background": color,
                        "border": "#ffffff"
                    }
                },
                size=size,
                shape="dot",
                borderWidth=1.5,
                font={
                    "size": 13,
                    "color": "white"
                }
            )

        else:
            size = 14 + (degree / max_degree) * 24
            label = node if len(node) <= 30 else node[:30] + "..."

            title = (
                f"👤 {node}<br>"
                f"Connected companies: {degree}"
            )

            net.add_node(
                node,
                label=label,
                title=title,
                color={
                    "background": "rgba(255,107,107,0.32)",
                    "border": "rgba(255,107,107,0.95)",
                    "highlight": {
                        "background": "rgba(255,107,107,0.45)",
                        "border": "rgba(255,107,107,1)"
                    }
                },
                size=size,
                shape="dot",
                borderWidth=2,
                font={
                    "size": 11,
                    "color": "white"
                }
            )

    # Add edges
    for u, v, data in G.edges(data=True):
        weight = safe_float(data.get("weight", 1))

        width = 1.2 + min(weight, 50) / 10

        net.add_edge(
            u,
            v,
            title=f"Shareholding: {weight:.2f}%",
            width=width,
            color="rgba(220,220,220,0.45)",
            smooth={
                "enabled": True,
                "type": "continuous",
                "roundness": 0.2
            }
        )

    if physics_on:
        net.force_atlas_2based(
            gravity=-80,
            central_gravity=0.01,
            spring_length=220,
            spring_strength=0.035,
            damping=0.65
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
      "edges": {
        "selectionWidth": 3,
        "hoverWidth": 3
      },
      "physics": {
        "stabilization": {
          "enabled": true,
          "iterations": 250,
          "updateInterval": 25
        }
      }
    }
    """)

    return net
