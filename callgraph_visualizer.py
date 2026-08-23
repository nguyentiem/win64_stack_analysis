#!/usr/bin/env python3
"""Visualize JSON exported by callgraph_gui.py in an interactive browser view.

Examples:
    python callgraph_visualizer.py test.json
    python callgraph_visualizer.py test.json -o call_graph.html --open

The generated HTML supports mouse-wheel zoom, pan, dragging nodes, search by
function name, and clicking a node to inspect its source file and neighbours.
It deliberately identifies a node by both function name and definition file,
so two static functions with the same name are not merged.
"""

import argparse
import html
import json
import sys
import webbrowser
from collections import Counter
from pathlib import Path


VIS_NETWORK_CDN = "https://unpkg.com/vis-network@9.1.9/dist/vis-network.min.js"


def node_id(function: dict) -> str:
    """Return a stable ID which does not merge duplicate static functions."""
    return json.dumps([function.get("name") or "<unknown>", function.get("file") or ""],
                      ensure_ascii=False, separators=(",", ","))


def load_graph(path: Path) -> tuple[list[dict], list[dict]]:
    with path.open(encoding="utf-8") as source:
        raw_edges = json.load(source)
    if not isinstance(raw_edges, list):
        raise ValueError("JSON must be an array of edges exported by callgraph_gui.py")

    nodes: dict[str, dict] = {}
    edges: dict[tuple[str, str, str], dict] = {}
    colors = {"direct": "#3b82f6", "indirect": "#f59e0b", "manual": "#a855f7"}
    for index, item in enumerate(raw_edges, start=1):
        if not isinstance(item, dict) or not isinstance(item.get("caller"), dict) or not isinstance(item.get("callee"), dict):
            raise ValueError(f"Invalid edge at array item {index}")
        caller, callee = item["caller"], item["callee"]
        caller_id, callee_id = node_id(caller), node_id(callee)
        for func, func_id in ((caller, caller_id), (callee, callee_id)):
            name, file = func.get("name") or "<unknown>", func.get("file") or "(unknown source file)"
            nodes.setdefault(func_id, {
                "id": func_id,
                "label": name,
                "title": f"<b>{html.escape(name)}</b><br>{html.escape(file)}",
                "file": file,
                "shape": "dot",
            })
        edge_type = item.get("type", "direct")
        key = (caller_id, callee_id, edge_type)
        edges.setdefault(key, {
            "from": caller_id, "to": callee_id, "type": edge_type,
            "label": edge_type, "arrows": "to",
            "color": {"color": colors.get(edge_type, "#64748b")},
        })
    return list(nodes.values()), list(edges.values())


def make_html(nodes: list[dict], edges: list[dict], title: str) -> str:
    payload = json.dumps({"nodes": nodes, "edges": edges}, ensure_ascii=False).replace("</", "<\\/")
    page_title = html.escape(title)
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{page_title}</title><script src="{VIS_NETWORK_CDN}"></script>
<style>
* {{ box-sizing: border-box; }} body {{ margin: 0; font: 14px Segoe UI,Arial,sans-serif; color:#172033; }}
#toolbar {{ display:flex; gap:8px; align-items:center; padding:10px 14px; border-bottom:1px solid #d8dee9; background:#f8fafc; }}
#search {{ width:min(430px,55vw); padding:7px 9px; border:1px solid #94a3b8; border-radius:5px; }} button {{ padding:7px 10px; cursor:pointer; }}
#status {{ color:#475569; }} #graph {{ height:calc(100vh - 53px); width:100%; }}
#info {{ position:absolute; right:16px; top:66px; width:min(390px,45vw); padding:12px; background:#ffffffed; border:1px solid #cbd5e1; border-radius:7px; box-shadow:0 2px 9px #0002; display:none; overflow-wrap:anywhere; }}
.legend {{ margin-left:auto; color:#475569; white-space:nowrap; }} .direct{{color:#2563eb}} .indirect{{color:#b45309}} .manual{{color:#7e22ce}}
</style></head><body>
<div id="toolbar"><input id="search" placeholder="Find function name, e.g. at_parser_ (Enter to focus)" autofocus><button id="find">Find</button><button id="reset">Reset view</button><span id="status"></span><span class="legend"><span class="direct">● direct</span> <span class="indirect">● indirect</span> <span class="manual">● manual</span></span></div>
<div id="graph"></div><aside id="info"></aside>
<script>
const data = {payload};
const nodes = new vis.DataSet(data.nodes), edges = new vis.DataSet(data.edges);
const network = new vis.Network(document.getElementById('graph'), {{nodes, edges}}, {{
  interaction: {{
    hover:true, navigationButtons:false, keyboard:false, multiselect:true,
    zoomView:true, dragView:true, dragNodes:true,
    zoomSpeed:0.25
  }},
  nodes: {{size:13, font:{{size:14, face:'Segoe UI'}}, color:{{background:'#dbeafe', border:'#2563eb'}}, borderWidth:1.5}},
  edges: {{smooth:{{type:'dynamic'}}, width:1.4, font:{{size:11, align:'middle'}}, arrows:{{to:{{enabled:true, scaleFactor:.65}}}}}},
  physics: {{stabilization:{{iterations:180}}, barnesHut:{{gravitationalConstant:-9000, springLength:125, springConstant:.035}}}}
}});
const normal = {{background:'#dbeafe', border:'#2563eb'}}, match = {{background:'#fef08a', border:'#ca8a04'}}, dim = {{background:'#e2e8f0', border:'#cbd5e1'}};
const status = document.getElementById('status'), info = document.getElementById('info');
// Only the initial force-layout is useful.  Disable physics afterwards so a
// mouse move/hover can never make the graph appear to zoom or drift by itself.
network.once('stabilizationIterationsDone', () => network.setOptions({{physics: {{enabled:false}}}}));
function restoreEdges() {{
  edges.update(edges.get().map(e => ({{id:e.id, hidden:false, width:1.4,
    color:{{color: e.type==='direct' ? '#3b82f6' : e.type==='indirect' ? '#f59e0b' : e.type==='manual' ? '#a855f7' : '#64748b'}}}})));
}}
function clearFocus() {{
  nodes.update(nodes.get().map(n => ({{id:n.id, color:normal}})));
  restoreEdges();
  network.unselectAll();
}}
function focusNode(id) {{
  const outgoingEdges = edges.get({{filter:e => e.from === id}});
  const callees = new Set(outgoingEdges.map(e => e.to));
  nodes.update(nodes.get().map(n => ({{id:n.id,
    color: n.id===id ? {{background:'#fb7185', border:'#be123c'}} :
           callees.has(n.id) ? {{background:'#fef08a', border:'#ca8a04'}} : dim,
    font: {{color: (n.id===id || callees.has(n.id)) ? '#172033' : '#94a3b8'}}}})));
  const selectedEdges = new Set(outgoingEdges.map(e => e.id));
  edges.update(edges.get().map(e => ({{id:e.id, width:selectedEdges.has(e.id) ? 3.5 : 0.7,
    color: selectedEdges.has(e.id)
      ? {{color: e.type==='direct' ? '#2563eb' : e.type==='indirect' ? '#d97706' : '#7e22ce', opacity:1}}
      : {{color:'#cbd5e1', opacity:0.12}}}})));
  status.textContent = `Focused: ${{nodes.get(id).label}} (${{callees.size}} direct callee(s))`;
}}
function search() {{
  const query = document.getElementById('search').value.trim().toLocaleLowerCase();
  const found = nodes.get().filter(n => !query || n.label.toLocaleLowerCase().includes(query));
  restoreEdges();
  nodes.update(nodes.get().map(n => ({{id:n.id, color: query ? (found.some(x=>x.id===n.id) ? match : dim) : normal,
    font:{{color: query && !found.some(x=>x.id===n.id) ? '#94a3b8' : '#172033'}}}})));
  status.textContent = query ? `${{found.length}} match(es)` : `${{nodes.length}} nodes, ${{edges.length}} edges`;
  if (found.length) network.focus(found[0].id, {{scale:1.35, animation:{{duration:450}}}});
}}
function reset() {{ document.getElementById('search').value=''; clearFocus(); status.textContent = `${{nodes.length}} nodes, ${{edges.length}} edges`; network.fit({{animation:{{duration:0}}}}); info.style.display='none'; }}
document.getElementById('find').onclick=search; document.getElementById('reset').onclick=reset;
document.getElementById('search').addEventListener('keydown', e => {{ if(e.key==='Enter') search(); }});
network.on('click', p => {{
  if (!p.nodes.length) {{ clearFocus(); status.textContent = `${{nodes.length}} nodes, ${{edges.length}} edges`; info.style.display='none'; return; }}
  const n=nodes.get(p.nodes[0]), incoming=network.getConnectedNodes(n.id,'from').length, outgoing=network.getConnectedNodes(n.id,'to').length;
  focusNode(n.id);
  info.innerHTML=`<b>${{escapeHtml(n.label)}}</b><br><br><b>File:</b> ${{escapeHtml(n.file)}}<br><b>Calls:</b> ${{outgoing}} &nbsp; <b>Called by:</b> ${{incoming}}`;
  info.style.display='block';
}});
function escapeHtml(s) {{ const e=document.createElement('span'); e.textContent=s; return e.innerHTML; }}
reset();
</script></body></html>'''


def main() -> int:
    parser = argparse.ArgumentParser(description="Create an interactive call graph HTML page.")
    parser.add_argument("input", type=Path, help="JSON exported by callgraph_gui.py")
    parser.add_argument("-o", "--output", type=Path, help="output HTML path (default: beside input)")
    parser.add_argument("--open", action="store_true", help="open the generated page in the default browser")
    args = parser.parse_args()
    output = args.output or args.input.with_name(args.input.stem + "_call_graph.html")
    try:
        nodes, edges = load_graph(args.input)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    output.write_text(make_html(nodes, edges, f"Call graph — {args.input.name}"), encoding="utf-8")
    print(f"Created {output} ({len(nodes)} nodes, {len(edges)} edges)")
    print("Mouse wheel: zoom. Hold left mouse on blank space: pan. Hold left mouse on a node: move node.")
    if args.open:
        webbrowser.open(output.resolve().as_uri())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
