"""ARK95X Multi-Agent Council
Planner, Research, Analysis, and Synthesis agents for sovereign decision-making.
Uses CrewAI for orchestration with Ollama local models.
"""
import os
import time
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from loguru import logger
from typing import Optional

# === CONFIG ===
COUNCIL_PORT = int(os.getenv("COUNCIL_PORT", 8300))
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
COUNCIL_MODEL = os.getenv("COUNCIL_MODEL", "llama3")

# === MODELS ===
class CouncilRequest(BaseModel):
    query: str
    context: str = ""
    require_consensus: bool = True
    gate_id: str = ""  # If gate unlock vote needed

class AgentVote(BaseModel):
    agent: str
    vote: str  # "approve", "deny", "abstain"
    reasoning: str
    confidence: float

class CouncilResponse(BaseModel):
    decision: str  # "approved", "denied", "split"
    votes: list
    consensus_score: float
    reasoning: str
    elapsed: float
    timestamp: str

# === COUNCIL AGENTS ===
AGENTS = {
    "planner": {
        "role": "Strategic Planner",
        "goal": "Evaluate operational feasibility, resource allocation, and strategic alignment",
        "system": "You are the ARK95X Strategic Planner. Evaluate requests for operational feasibility. Consider resource constraints, timing, and alignment with Network-95 LLC objectives. Vote APPROVE, DENY, or ABSTAIN with clear reasoning. Keep response under 100 words.",
    },
    "research": {
        "role": "Research Analyst",
        "goal": "Verify claims, check data sources, and assess information quality",
        "system": "You are the ARK95X Research Analyst. Verify factual claims and data quality in requests. Check for completeness and accuracy. Vote APPROVE, DENY, or ABSTAIN with clear reasoning. Keep response under 100 words.",
    },
    "analysis": {
        "role": "Risk Analyst",
        "goal": "Identify risks, vulnerabilities, and potential negative outcomes",
        "system": "You are the ARK95X Risk Analyst. Identify security risks, operational vulnerabilities, and potential negative outcomes. Vote APPROVE, DENY, or ABSTAIN with clear reasoning. Keep response under 100 words.",
    },
    "synthesis": {
        "role": "Integration Synthesizer",
        "goal": "Ensure system coherence and synthesize multi-agent perspectives",
        "system": "You are the ARK95X Integration Synthesizer. Ensure the request is coherent with existing systems and synthesize perspectives from other council members. Vote APPROVE, DENY, or ABSTAIN with clear reasoning. Keep response under 100 words.",
    },
}

# === APP ===
app = FastAPI(
    title="ARK95X Multi-Agent Council",
    description="Sovereign council for multi-agent decision-making and gate validation",
    version="1.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# === AGENT CALL ===
async def call_agent(agent_id: str, query: str, context: str = "") -> AgentVote:
    import httpx
    agent = AGENTS[agent_id]
    prompt = f"COUNCIL VOTE REQUEST:\n{query}"
    if context:
        prompt += f"\n\nCONTEXT:\n{context}"
    prompt += "\n\nRespond with: VOTE: [APPROVE/DENY/ABSTAIN]\nREASONING: [your reasoning]\nCONFIDENCE: [0.0-1.0]"

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(
                f"{OLLAMA_HOST}/api/generate",
                json={"model": COUNCIL_MODEL, "prompt": prompt, "system": agent["system"], "stream": False},
            )
            text = r.json().get("response", "")

        vote = "abstain"
        if "APPROVE" in text.upper():
            vote = "approve"
        elif "DENY" in text.upper():
            vote = "deny"

        confidence = 0.5
        if "CONFIDENCE:" in text.upper():
            try:
                conf_str = text.upper().split("CONFIDENCE:")[1].strip().split()[0]
                confidence = float(conf_str.replace(",", ""))
                confidence = max(0.0, min(1.0, confidence))
            except (ValueError, IndexError):
                pass

        return AgentVote(agent=agent_id, vote=vote, reasoning=text[:300], confidence=confidence)

    except Exception as e:
        logger.error(f"[COUNCIL] Agent {agent_id} failed: {e}")
        return AgentVote(agent=agent_id, vote="abstain", reasoning=f"Agent error: {str(e)[:100]}", confidence=0.0)

# === ENDPOINTS ===
@app.get("/health")
async def health():
    return {
        "service": "council",
        "status": "operational",
        "port": COUNCIL_PORT,
        "agents": list(AGENTS.keys()),
        "model": COUNCIL_MODEL,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

@app.post("/vote", response_model=CouncilResponse)
async def council_vote(req: CouncilRequest):
    import asyncio
    start = time.time()

    tasks = [call_agent(aid, req.query, req.context) for aid in AGENTS]
    votes = await asyncio.gather(*tasks)

    approve_count = sum(1 for v in votes if v.vote == "approve")
    deny_count = sum(1 for v in votes if v.vote == "deny")
    total_voting = sum(1 for v in votes if v.vote != "abstain")

    if total_voting == 0:
        decision = "split"
        consensus_score = 0.0
    elif approve_count > deny_count:
        decision = "approved"
        consensus_score = approve_count / max(total_voting, 1)
    elif deny_count > approve_count:
        decision = "denied"
        consensus_score = deny_count / max(total_voting, 1)
    else:
        decision = "split"
        consensus_score = 0.5

    avg_confidence = sum(v.confidence for v in votes) / len(votes) if votes else 0

    reasoning = f"Council decision: {decision.upper()}. {approve_count} approve, {deny_count} deny, {len(votes) - total_voting} abstain. Avg confidence: {avg_confidence:.2f}"

    elapsed = round(time.time() - start, 2)

    return CouncilResponse(
        decision=decision,
        votes=[v.dict() for v in votes],
        consensus_score=round(consensus_score, 2),
        reasoning=reasoning,
        elapsed=elapsed,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

@app.post("/gate-vote")
async def gate_vote(gate_id: str, actor: str = "command_base"):
    import httpx
    query = f"Should gate '{gate_id}' be unlocked? Actor requesting: {actor}. Evaluate security implications."
    req = CouncilRequest(query=query, gate_id=gate_id, require_consensus=True)
    result = await council_vote(req)

    if result.decision == "approved":
        try:
            gate_unlocker_url = os.getenv("GATE_UNLOCKER_URL", "http://localhost:8200")
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.post(
                    f"{gate_unlocker_url}/unlock",
                    json={"gate_id": gate_id, "actor": f"council_{actor}", "council_override": True},
                )
                unlock_result = r.json()
        except Exception as e:
            unlock_result = {"error": str(e)}
    else:
        unlock_result = {"status": "denied_by_council"}

    return {"council_decision": result.dict(), "gate_action": unlock_result}

@app.get("/agents")
async def list_agents():
    return {"agents": {k: {"role": v["role"], "goal": v["goal"]} for k, v in AGENTS.items()}}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("council:app", host="0.0.0.0", port=COUNCIL_PORT, reload=True)
