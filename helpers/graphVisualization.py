def save_graph_png(compiled_graph, filename="qg_graph.png"):
    try:
        png_bytes = compiled_graph.get_graph().draw_mermaid_png()
        with open(filename, "wb") as f:
            f.write(png_bytes)
        print(f"Graph saved to {filename}")
    except Exception as e:
        print(f"Failed to save graph: {e}")