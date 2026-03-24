"""
ARK95X Command Center API - FastAPI Server
Unified API for all agents, protocols, skills, tools, and systems.
Fury mode, multiplex, and full command center orchestration.
Network-95 LLC | 2026
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import uvicorn
from datetime import datetime

from .agents import CommandCenter, AgentRegistry
from .protocol_router import create_default_router, ProtocolMessage, ProtocolType, MessagePriority

app = FastAPI(
    title="ARK95X Command Center",
    description="Sovereign AI Command Center - Manus + ZenCode + VibeCoder",
    version="3.0.0",
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

center = CommandCenter()
router = create_default_router()


class TaskRequest(BaseModel):
    agent: str
    action: str
    target: str
    params: Dict[str, Any] = {}


class FuryRequest(BaseModel):
    tasks: List[Dict[str, Any]]


class RouteRequest(BaseModel):
    protocol: str
    sender: str
    recipient: str
    action: str
    payload: Dict[str, Any] = {}


@app.get("/")
async def root():
    return {
        "system": "ARK95X Command Center",
        "version": "3.0.0",
        "status": "operational",
        "owner": "Network-95 LLC",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "uptime": datetime.utcnow().isoformat()}


@app.get("/status")
async def status():
    return center.status()


@app.get("/manifest")
async def manifest():
    return AgentRegistry.system_manifest()


@app.get("/agents")
async def list_agents():
    return AgentRegistry.list_agents()


@app.get("/agents/{agent_id}/status")
async def agent_status(agent_id: str):
    agent_map = {"manus": center.manus, "zencode": center.zencode, "vibecoder": center.vibecoder}
    agent = agent_map.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
    return agent.status()


@app.get("/skills")
async def list_skills():
    return AgentRegistry.list_all_skills()


@app.get("/tools")
async def list_tools():
    return AgentRegistry.list_all_tools()


@app.get("/protocols")
async def list_protocols():
    return AgentRegistry.list_protocols()


@app.get("/router/status")
async def router_status():
    return router.status()


@app.get("/router/discover")
async def discover_agents(skill: Optional[str] = None):
    return router.discover_agents(skill)


@app.post("/router/route")
async def route_message(req: RouteRequest):
    msg = ProtocolMessage(
        protocol=ProtocolType(req.protocol),
        sender=req.sender,
        recipient=req.recipient,
        action=req.action,
        payload=req.payload,
    )
    return await router.route(msg)


@app.post("/fury")
async def fury_deploy(req: FuryRequest):
    return await center.fury_deploy(req.tasks)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
