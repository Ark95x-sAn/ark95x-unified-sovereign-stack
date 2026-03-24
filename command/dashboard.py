"""ARK95X Command Base Dashboard - Port 8050
Sovereign Command Center with gate status, council monitoring, and system telemetry.
"""
import os
import time
import asyncio
import httpx
from datetime import datetime, timezone
from dash import Dash, html, dcc, callback, Output, Input, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

# === CONFIG ===
CORE_API = os.getenv("CORE_API_URL", "http://localhost:8000")
FLAMEGATE_URL = os.getenv("FLAMEGATE_URL", "https://localhost:8443")
COMET_ROUTER_URL = os.getenv("COMET_ROUTER_URL", "http://localhost:8100")
GATE_UNLOCKER_URL = os.getenv("GATE_UNLOCKER_URL", "http://localhost:8200")
DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", 8050))

# TLS verification toggle: defaults to True (secure). Set to "false" in
# env only for local dev behind self-signed certs.
VERIFY_TLS = os.getenv("ARK95X_VERIFY_TLS", "true").lower() not in ("false", "0", "no")

# === GATE DEFINITIONS ===
GATES = {
    "gate_core": {"name": "Core API Gate", "port": 8000, "url": f"{CORE_API}/health"},
    "gate_n8n": {"name": "n8n Workflow Gate", "port": 5678, "url": "http://localhost:5678"},
    "gate_qdrant": {"name": "Qdrant Vector Gate", "port": 6333, "url": "http://localhost:6333/health"},
    "gate_searxng": {"name": "SearXNG Intel Gate", "port": 8080, "url": "http://localhost:8080"},
    "gate_grafana": {"name": "Grafana Monitor Gate", "port": 3000, "url": "http://localhost:3000"},
    "gate_flamegate": {"name": "Flamegate TLS Gate", "port": 8443, "url": f"{FLAMEGATE_URL}/health"},
    "gate_comet": {"name": "Comet Router Gate", "port": 8100, "url": f"{COMET_ROUTER_URL}/health"},
    "gate_unlocker": {"name": "Gate Unlocker", "port": 8200, "url": f"{GATE_UNLOCKER_URL}/health"},
    "gate_ollama": {"name": "Ollama LLM Gate", "port": 11434, "url": "http://localhost:11434/api/tags"},
}

# === DASH APP ===
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.CYBORG],
    title="ARK95X Command Base",
    suppress_callback_exceptions=True,
)


def make_gate_card(gate_id, gate_info, status="unknown"):
    color_map = {"healthy": "success", "unhealthy": "danger", "unknown": "secondary", "locked": "warning", "unlocked": "success"}
    color = color_map.get(status, "secondary")
    icon = {"healthy": "\U0001f7e2", "unlocked": "\U0001f513", "unhealthy": "\U0001f534", "locked": "\U0001f512", "unknown": "\u26aa"}.get(status, "\u26aa")
    return dbc.Col(
        dbc.Card([
            dbc.CardBody([
                html.H6(f"{icon} {gate_info['name']}", className="card-title mb-1"),
                html.Small(f":{gate_info['port']} | {status.upper()}", className=f"text-{color}"),
            ])
        ], className=f"border-{color} mb-2", style={"borderWidth": "2px"}),
        width=4,
    )


def build_layout():
    return dbc.Container([
        # Header
        dbc.Row([
            dbc.Col([
                html.H1("\U0001f525 ARK95X COMMAND BASE", className="text-warning mb-0"),
                html.P("Sovereign Stack Control Center | Network-95 LLC", className="text-muted"),
            ], width=8),
            dbc.Col([
                html.Div(id="system-clock", className="text-end text-info h4"),
                html.Div(id="uptime-display", className="text-end text-muted small"),
            ], width=4),
        ], className="my-3"),
        html.Hr(className="border-warning"),
        # Council Status
        dbc.Row([
            dbc.Col([
                html.H4("\u26a1 Council Status", className="text-info"),
                html.Div(id="council-status"),
            ]),
        ], className="mb-3"),
        # Gate Grid
        dbc.Row([
            dbc.Col([
                html.H4("\U0001f6aa Gate Status Grid", className="text-warning"),
                html.Div(id="gate-grid"),
            ]),
        ], className="mb-3"),
        # Gate Unlock Controls
        dbc.Row([
            dbc.Col([
                html.H4("\U0001f513 Gate Unlock Console", className="text-success"),
                dbc.InputGroup([
                    dbc.Select(
                        id="gate-select",
                        options=[{"label": g["name"], "value": gid} for gid, g in GATES.items()],
                        placeholder="Select gate to unlock...",
                    ),
                    dbc.Button("UNLOCK GATE", id="unlock-btn", color="warning", n_clicks=0),
                    dbc.Button("LOCK ALL", id="lock-all-btn", color="danger", n_clicks=0),
                ]),
                html.Div(id="unlock-result", className="mt-2"),
            ]),
        ], className="mb-3"),
        # Telemetry Graph
        dbc.Row([
            dbc.Col([
                html.H4("\U0001f4ca System Telemetry", className="text-info"),
                dcc.Graph(id="telemetry-graph"),
            ]),
        ], className="mb-3"),
        # Audit Log
        dbc.Row([
            dbc.Col([
                html.H4("\U0001f4cb Audit Log", className="text-muted"),
                html.Div(id="audit-log", style={"maxHeight": "300px", "overflowY": "auto", "fontFamily": "monospace", "fontSize": "12px"}),
            ]),
        ], className="mb-3"),
        # Auto-refresh
        dcc.Interval(id="refresh-interval", interval=5000, n_intervals=0),
        dcc.Store(id="gate-states", data={}),
        dcc.Store(id="audit-entries", data=[]),
    ], fluid=True, className="bg-dark text-light p-3")


app.layout = build_layout()


# === CALLBACKS ===
@callback(
    Output("system-clock", "children"),
    Input("refresh-interval", "n_intervals"),
)
def update_clock(_):
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


@callback(
    Output("gate-grid", "children"),
    Output("gate-states", "data"),
    Input("refresh-interval", "n_intervals"),
)
def update_gates(_):
    states = {}
    cards = []
    for gid, ginfo in GATES.items():
        try:
            r = httpx.get(ginfo["url"], timeout=3.0, verify=VERIFY_TLS)
            status = "healthy" if r.status_code < 400 else "unhealthy"
        except Exception:
            status = "unhealthy"
        states[gid] = status
        cards.append(make_gate_card(gid, ginfo, status))
    rows = [dbc.Row(cards[i:i + 3]) for i in range(0, len(cards), 3)]
    return rows, states


@callback(
    Output("council-status", "children"),
    Input("gate-states", "data"),
)
def update_council(states):
    healthy = sum(1 for s in states.values() if s == "healthy")
    total = len(states)
    pct = (healthy / total * 100) if total > 0 else 0
    color = "success" if pct > 80 else "warning" if pct > 50 else "danger"
    return dbc.Progress(
        value=pct,
        label=f"Council Readiness: {healthy}/{total} gates ({pct:.0f}%)",
        color=color,
        className="mb-2",
        style={"height": "30px"},
    )


@callback(
    Output("unlock-result", "children"),
    Output("audit-entries", "data"),
    Input("unlock-btn", "n_clicks"),
    State("gate-select", "value"),
    State("audit-entries", "data"),
    prevent_initial_call=True,
)
def unlock_gate(n, gate_id, audit):
    if not gate_id:
        return dbc.Alert("Select a gate first", color="warning"), audit
    ts = datetime.now(timezone.utc).isoformat()
    try:
        r = httpx.post(
            f"{GATE_UNLOCKER_URL}/unlock",
            json={"gate_id": gate_id, "actor": "command_base", "timestamp": ts},
            timeout=10.0,
            verify=VERIFY_TLS,
        )
        result = r.json()
        entry = f"[{ts}] UNLOCK {gate_id} -> {result.get('status', 'unknown')}"
        audit.insert(0, entry)
        return dbc.Alert(f"Gate {gate_id}: {result.get('status', 'done')}", color="success"), audit
    except Exception as e:
        entry = f"[{ts}] UNLOCK {gate_id} -> FAILED: {e}"
        audit.insert(0, entry)
        return dbc.Alert(f"Unlock failed: {e}", color="danger"), audit


@callback(
    Output("audit-log", "children"),
    Input("audit-entries", "data"),
)
def update_audit(entries):
    return [html.Div(e, className="text-muted") for e in (entries or [])]


@callback(
    Output("telemetry-graph", "figure"),
    Input("refresh-interval", "n_intervals"),
    State("gate-states", "data"),
)
def update_telemetry(_, states):
    names = [GATES[gid]["name"] for gid in states] if states else []
    values = [1 if s == "healthy" else 0 for s in states.values()] if states else []
    colors = ["#00ff88" if v == 1 else "#ff4444" for v in values]
    fig = go.Figure(go.Bar(x=names, y=values, marker_color=colors, text=["UP" if v else "DOWN" for v in values], textposition="auto"))
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        title="Gate Health Status",
        yaxis=dict(tickvals=[0, 1], ticktext=["DOWN", "UP"]),
        height=300,
        margin=dict(t=40, b=40, l=40, r=40),
    )
    return fig


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=DASHBOARD_PORT, debug=True)
