def render_network(G, physics_on=True):
    net = Network(
        height="760px",
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

            size = 16 + (degree / max_degree) * 24

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
                    "border": "#222222",
                    "highlight": {
                        "background": color,
                        "border": "#000000"
                    }
                },
                size=size,
                shape="dot",
                borderWidth=2,
                mass=3,
                font={
                    "size": 14,
                    "color": "#111111",
                    "strokeWidth": 4,
                    "strokeColor": "#ffffff"
                }
            )

        else:
            size = 13 + (degree / max_degree) * 22
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
                mass=2,
                font={
                    "size": 11,
                    "color": "#111111",
                    "strokeWidth": 4,
                    "strokeColor": "#ffffff"
                }
            )

    # Add edges
    for u, v, data in G.edges(data=True):
        weight = safe_float(data.get("weight", 1))

        # Keep relation lines readable, not too thick
        width = 0.8 + min(weight, 50) / 14

        net.add_edge(
            u,
            v,
            title=f"Shareholding: {weight:.2f}%",
            width=width,
            color={
                "color": "rgba(70,70,70,0.28)",
                "highlight": "rgba(0,0,0,0.85)",
                "hover": "rgba(0,0,0,0.85)"
            },
            smooth={
                "enabled": True,
                "type": "dynamic",
                "roundness": 0.35
            }
        )

    if physics_on:
        net.force_atlas_2based(
            gravity=-180,
            central_gravity=0.004,
            spring_length=310,
            spring_strength=0.022,
            damping=0.78
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
          "size": 7,
          "x": 2,
          "y": 2
        }
      },
      "edges": {
        "selectionWidth": 4,
        "hoverWidth": 4,
        "smooth": {
          "enabled": true,
          "type": "dynamic",
          "roundness": 0.35
        }
      },
      "physics": {
        "enabled": true,
        "stabilization": {
          "enabled": true,
          "iterations": 500,
          "updateInterval": 25,
          "fit": true
        },
        "minVelocity": 0.75
      }
    }
    """)

    return net
