"""ARK95X OmniNet Cockpit
FastAPI + WebSocket cockpit on :8080. Replaces the decorative ROI ledger /
leverage meter concept with numbers computed live from real ledger state:
NetX signal -> risk calculator -> passive_income_engine -> command_ledger,
broadcast to connected clients over /ws/cockpit as telemetry_event payloads.

Financial actions (closing a position) are gated by the single control
plane by default: /fills queues the request for human approval instead of
moving money immediately, per control_plane's authority invariants. Set
CONTROL_PLANE_ENABLED=false to fall back to immediate execution.

Ledger persistence: set POSTGRES_URL (e.g. from the data stack's
docker-compose postgres service) to store real ledger state in Postgres
instead of a JSON file. Falls back to LEDGER_PERSIST_PATH when unset.
"""
import os
import logging
from typing import List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel

from netx.signal_engine import Signal
from netx.risk_calculator import RiskCalculator
from passive_income_engine import PassiveIncomeEngine
from ledger.command_ledger import CommandLedger
from control_plane import build_default_control_plane

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ark95x.cockpit")

APP_PORT = int(os.getenv("COCKPIT_PORT", 8080))
STARTING_CAPITAL = float(os.getenv("STARTING_CAPITAL_USD", "10000"))
BREAKEVEN_COST_USD = float(os.getenv("BREAKEVEN_COST_USD", "0"))
LEDGER_PERSIST_PATH = os.getenv("LEDGER_PERSIST_PATH", "data/ledger_state.json")
POSTGRES_URL = os.getenv("POSTGRES_URL", "")
DEFAULT_RISK_PCT = float(os.getenv("DEFAULT_RISK_PCT", "1.0"))
CONTROL_PLANE_ENABLED = os.getenv("CONTROL_PLANE_ENABLED", "true").lower() != "false"


class ConnectionManager:
    """Tracks connected cockpit WebSocket clients and broadcasts telemetry."""

    def __init__(self):
        self.active: List[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)
        logger.info(f"Cockpit client connected ({len(self.active)} total)")

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)
        logger.info(f"Cockpit client disconnected ({len(self.active)} total)")

    async def broadcast(self, payload: dict):
        dead = []
        for ws in self.active:
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


class SignalWebhookPayload(BaseModel):
    symbol: str
    side: str
    entry_price: float
    stop_price: float
    signal_id: Optional[str] = None
    source: Optional[str] = "netx"
    strategy: Optional[str] = "unknown"
    confidence: Optional[float] = None
    take_profit_price: Optional[float] = None
    timeframe: Optional[str] = None


class FillRequest(BaseModel):
    order_id: str
    exit_price: float


manager = ConnectionManager()
engine = PassiveIncomeEngine(
    starting_balance=STARTING_CAPITAL,
    breakeven_cost_usd=BREAKEVEN_COST_USD,
    persist_path=None if POSTGRES_URL else LEDGER_PERSIST_PATH,
    postgres_url=POSTGRES_URL or None,
)
if POSTGRES_URL:
    logger.info("Ledger persistence backend: Postgres")
else:
    logger.info(f"Ledger persistence backend: JSON file ({LEDGER_PERSIST_PATH})")
risk_calculator = RiskCalculator()
control_plane = build_default_control_plane() if CONTROL_PLANE_ENABLED else None
ledger = CommandLedger(
    engine=engine,
    risk_calculator=risk_calculator,
    risk_pct=DEFAULT_RISK_PCT,
    on_telemetry=manager.broadcast,
    control_plane=control_plane,
)

app = FastAPI(title="ARK95X OmniNet Cockpit")


@app.get("/health")
async def health():
    return {"status": "healthy", "starting_capital_usd": STARTING_CAPITAL}


@app.get("/roi")
async def roi():
    """Live ROI ledger + leverage meter snapshot -- no decorative values."""
    event = ledger.build_telemetry_event(event_type="roi_update")
    return event.to_dict()


@app.post("/netx/webhook")
async def netx_webhook(payload: SignalWebhookPayload):
    """NetX / n8n signal ingestion. Fires the full signal -> risk -> telemetry chain."""
    try:
        signal = Signal.from_webhook_payload(payload.model_dump(exclude_none=True))
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=422, detail=str(e))
    order = await ledger.handle_signal(signal)
    return order.to_dict()


@app.post("/fills")
async def report_fill(fill: FillRequest):
    """Reports a closed position. With the control plane enabled (default),
    this is a FINANCIAL action -- it queues for human approval and does not
    move money until POST /approve/{request_id} is called. Disabled, it
    records the real realized P&L immediately, as before."""
    try:
        result = await ledger.request_close_order(fill.order_id, fill.exit_price)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return result


@app.get("/pending")
async def pending_actions():
    """Actions queued for human approval -- the control plane's authority
    gate made visible."""
    if control_plane is None:
        return {"control_plane_enabled": False, "pending": []}
    pending = [r for r in control_plane.action_queue if not r["executed"]]
    return {"control_plane_enabled": True, "pending": pending}


@app.post("/approve/{request_id}")
async def approve_action(request_id: str):
    """A human approves a queued financial action; only now does the real
    ledger entry get recorded and reported back through the control plane."""
    if control_plane is None:
        raise HTTPException(status_code=409, detail="control plane is disabled -- nothing to approve")
    try:
        entry = await ledger.approve_pending_action(request_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return entry.to_dict()


@app.get("/control-plane")
async def control_plane_snapshot():
    """The authority/reporting state itself -- who's registered, what they
    can do, and what's queued. ARK-STATE.json stays authoritative; this is
    a read-only view."""
    if control_plane is None:
        return {"control_plane_enabled": False}
    return {"control_plane_enabled": True, **control_plane.snapshot()}


@app.websocket("/ws/cockpit")
async def cockpit_ws(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send current state immediately so new clients never see stale/decorative data.
        snapshot_event = ledger.build_telemetry_event(event_type="roi_update")
        await websocket.send_json(snapshot_event.to_dict())
        while True:
            await websocket.receive_text()  # keep-alive / ignore inbound
    except WebSocketDisconnect:
        manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=APP_PORT)
