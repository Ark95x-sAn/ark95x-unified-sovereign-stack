"""
ARK95X Sovereign Council — Multi-Model Consensus Engine
========================================================
Network-95 LLC | Comet Executive Assistant
Queries 3+ AI models, merges responses via weighted voting.
Task #33 from NETWORK95_100_TASKS.md
"""

import asyncio
import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx


class ModelProvider(str, Enum):
    OLLAMA_LLAMA3 = "ollama:llama3"
    OLLAMA_MISTRAL = "ollama:mistral"
    OLLAMA_DEEPSEEK = "ollama:deepseek-coder-v2"
    GROQ_LLAMA3 = "groq:llama3-70b"
    OPENAI_GPT4 = "openai:gpt-4o"
    PERPLEXITY = "perplexity:sonar-pro"
    KIMI_K25 = "kimi:k2.5"


@dataclass
class CouncilVote:
    model: str
    response: str
    confidence: float  # 0.0 - 1.0
    latency_ms: float
    tokens_used: int
    cost_usd: float


@dataclass
class CouncilVerdict:
    query: str
    votes: List[CouncilVote]
    consensus: str
    agreement_score: float
    total_latency_ms: float
    total_cost_usd: float
    timestamp: str
    session_id: str


class SovereignCouncil:
    """
    Multi-model consensus engine.
    Dispatches queries to N models in parallel,
    collects responses, and merges via weighted voting.
    """

    PROVIDER_CONFIG = {
        ModelProvider.OLLAMA_LLAMA3: {
            "url": "http://localhost:11434/api/generate",
            "cost_per_1k": 0.0,
            "weight": 1.0,
            "timeout": 30,
        },
        ModelProvider.OLLAMA_MISTRAL: {
            "url": "http://localhost:11434/api/generate",
            "cost_per_1k": 0.0,
            "weight": 1.2,  # Financial structurer bonus
            "timeout": 30,
        },
        ModelProvider.OLLAMA_DEEPSEEK: {
            "url": "http://localhost:11434/api/generate",
            "cost_per_1k": 0.0,
            "weight": 1.3,  # Code specialist bonus
            "timeout": 30,
        },
        ModelProvider.GROQ_LLAMA3: {
            "url": "https://api.groq.com/openai/v1/chat/completions",
            "cost_per_1k": 0.00059,
            "weight": 1.1,
            "timeout": 10,
        },
        ModelProvider.OPENAI_GPT4: {
            "url": "https://api.openai.com/v1/chat/completions",
            "cost_per_1k": 0.005,
            "weight": 1.5,  # Highest reasoning weight
            "timeout": 30,
        },
        ModelProvider.PERPLEXITY: {
            "url": "https://api.perplexity.ai/chat/completions",
            "cost_per_1k": 0.003,
            "weight": 1.4,  # Web-grounded bonus
            "timeout": 20,
        },
        ModelProvider.KIMI_K25: {
            "url": "https://api.moonshot.cn/v1/chat/completions",
            "cost_per_1k": 0.002,
            "weight": 1.2,
            "timeout": 25,
        },
    }

    def __init__(
        self,
        models: Optional[List[ModelProvider]] = None,
        api_keys: Optional[Dict[str, str]] = None,
    ):
        self.models = models or [
            ModelProvider.OLLAMA_LLAMA3,
            ModelProvider.OLLAMA_MISTRAL,
            ModelProvider.OLLAMA_DEEPSEEK,
        ]
        self.api_keys = api_keys or {}
        self.history: List[CouncilVerdict] = []

    async def _query_ollama(
        self, model: ModelProvider, prompt: str
    ) -> CouncilVote:
        model_name = model.value.split(":")[1]
        config = self.PROVIDER_CONFIG[model]
        start = time.monotonic()
        async with httpx.AsyncClient(timeout=config["timeout"]) as client:
            resp = await client.post(
                config["url"],
                json={"model": model_name, "prompt": prompt, "stream": False},
            )
            data = resp.json()
        latency = (time.monotonic() - start) * 1000
        text = data.get("response", "")
        tokens = data.get("eval_count", len(text.split()))
        return CouncilVote(
            model=model.value,
            response=text,
            confidence=config["weight"],
            latency_ms=round(latency, 1),
            tokens_used=tokens,
            cost_usd=0.0,
        )

    async def _query_cloud(
        self, model: ModelProvider, prompt: str
    ) -> CouncilVote:
        config = self.PROVIDER_CONFIG[model]
        provider = model.value.split(":")[0]
        api_key = self.api_keys.get(provider, "")
        start = time.monotonic()
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": model.value.split(":")[1],
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 2048,
        }
        async with httpx.AsyncClient(timeout=config["timeout"]) as client:
            resp = await client.post(
                config["url"], json=body, headers=headers
            )
            data = resp.json()
        latency = (time.monotonic() - start) * 1000
        text = data.get("choices", [{}])[0].get("message", {}).get(
            "content", ""
        )
        tokens = data.get("usage", {}).get("total_tokens", len(text.split()))
        cost = (tokens / 1000) * config["cost_per_1k"]
        return CouncilVote(
            model=model.value,
            response=text,
            confidence=config["weight"],
            latency_ms=round(latency, 1),
            tokens_used=tokens,
            cost_usd=round(cost, 6),
        )

    async def _query_model(
        self, model: ModelProvider, prompt: str
    ) -> CouncilVote:
        try:
            if model.value.startswith("ollama:"):
                return await self._query_ollama(model, prompt)
            else:
                return await self._query_cloud(model, prompt)
        except Exception as e:
            return CouncilVote(
                model=model.value,
                response=f"[ERROR] {str(e)}",
                confidence=0.0,
                latency_ms=0.0,
                tokens_used=0,
                cost_usd=0.0,
            )

    def _compute_consensus(self, votes: List[CouncilVote]) -> tuple:
        """Weighted merge — highest confidence * longest response wins."""
        valid = [v for v in votes if not v.response.startswith("[ERROR]")]
        if not valid:
            return "NO CONSENSUS — all models failed", 0.0
        scored = []
        for v in valid:
            score = v.confidence * min(len(v.response) / 500, 2.0)
            scored.append((score, v))
        scored.sort(key=lambda x: x[0], reverse=True)
        best = scored[0][1]
        # Agreement score: how many models roughly agree
        agreement = sum(
            1
            for v in valid
            if self._similarity(v.response, best.response) > 0.3
        )
        agreement_pct = agreement / len(valid) if valid else 0
        return best.response, round(agreement_pct, 2)

    @staticmethod
    def _similarity(a: str, b: str) -> float:
        """Quick token overlap similarity."""
        tokens_a = set(a.lower().split())
        tokens_b = set(b.lower().split())
        if not tokens_a or not tokens_b:
            return 0.0
        overlap = tokens_a & tokens_b
        return len(overlap) / max(len(tokens_a), len(tokens_b))

    async def convene(self, query: str) -> CouncilVerdict:
        """Main entry — convene the council on a query."""
        session_id = hashlib.md5(
            f"{query}{time.time()}".encode()
        ).hexdigest()[:12]
        tasks = [self._query_model(m, query) for m in self.models]
        votes = await asyncio.gather(*tasks)
        consensus, agreement = self._compute_consensus(list(votes))
        verdict = CouncilVerdict(
            query=query,
            votes=list(votes),
            consensus=consensus,
            agreement_score=agreement,
            total_latency_ms=round(
                max(v.latency_ms for v in votes), 1
            ),
            total_cost_usd=round(sum(v.cost_usd for v in votes), 6),
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            session_id=session_id,
        )
        self.history.append(verdict)
        return verdict

    def to_dict(self, verdict: CouncilVerdict) -> Dict[str, Any]:
        return {
            "session_id": verdict.session_id,
            "query": verdict.query,
            "consensus": verdict.consensus[:500],
            "agreement_score": verdict.agreement_score,
            "total_latency_ms": verdict.total_latency_ms,
            "total_cost_usd": verdict.total_cost_usd,
            "votes": [
                {
                    "model": v.model,
                    "confidence": v.confidence,
                    "latency_ms": v.latency_ms,
                    "tokens": v.tokens_used,
                    "cost": v.cost_usd,
                    "response_preview": v.response[:200],
                }
                for v in verdict.votes
            ],
            "timestamp": verdict.timestamp,
        }


# --- FastAPI Integration (add to comet_router.py) ---
# from core.council import SovereignCouncil, ModelProvider
#
# council = SovereignCouncil(
#     models=[
#         ModelProvider.OLLAMA_LLAMA3,
#         ModelProvider.OLLAMA_MISTRAL,
#         ModelProvider.GROQ_LLAMA3,
#     ],
#     api_keys={"groq": os.getenv("GROQ_API_KEY")},
# )
#
# @app.post("/council")
# async def council_vote(request: TaskRequest):
#     verdict = await council.convene(request.content)
#     return council.to_dict(verdict)


if __name__ == "__main__":
    async def demo():
        c = SovereignCouncil()
        v = await c.convene(
            "What is the optimal automation strategy for a "
            "5-property real estate portfolio with a bar & grill?"
        )
        print(json.dumps(c.to_dict(v), indent=2))

    asyncio.run(demo())
