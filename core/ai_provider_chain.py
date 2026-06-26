"""
ARK95X AI Provider Chain Router
=================================
Dimensional linking of AI provider families.

Each chain is a provider family tree:
    ChatGPT → Codex → GitHub Actions
    Gemini  → Google Search → Google Drive/Docs
    Copilot → Microsoft Graph → Azure/Office 365
    Claude  → Anthropic → Computer Use
    Alexa   → Smart Home → IoT devices

Intent is classified, routed to the best chain, then drilled
down to the right model within that chain for execution.

"Dimensionally linked like generations of families" — every
provider family has a HEAD (reasoning), BODY (execution),
and MEMORY (storage/retrieval).
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import httpx
from loguru import logger


# ---------------------------------------------------------------------------
# Provider Families
# ---------------------------------------------------------------------------


class ProviderFamily(str, Enum):
    OPENAI = "openai"         # ChatGPT → Codex → DALL-E → Whisper
    GOOGLE = "google"         # Gemini → Search → Drive → Docs → Gmail
    MICROSOFT = "microsoft"   # Copilot → Graph → Azure → Office → Teams
    ANTHROPIC = "anthropic"   # Claude → Computer Use → Artifacts
    AMAZON = "amazon"         # Alexa → AWS → IoT → Rekognition
    META = "meta"             # Llama → Instagram → Messenger
    XAI = "xai"              # Grok → X/Twitter → Real-time data
    LOCAL = "local"           # Ollama → local models → private compute


class ChainRole(str, Enum):
    HEAD = "head"           # Reasoning / planning
    BODY = "body"           # Execution / code / action
    MEMORY = "memory"       # Storage / retrieval / search
    SENSE = "sense"         # Input: vision, audio, search
    VOICE = "voice"         # Output: speech, notifications


# ---------------------------------------------------------------------------
# Chain Definitions
# ---------------------------------------------------------------------------


@dataclass
class ChainNode:
    """One model/service in a provider chain."""
    node_id: str
    name: str
    role: ChainRole
    family: ProviderFamily
    endpoint: str
    api_key_env: str
    model_id: str
    capabilities: list[str] = field(default_factory=list)
    cost_tier: str = "medium"   # low / medium / high
    latency_tier: str = "medium"  # fast / medium / slow
    offline_capable: bool = False


@dataclass
class ProviderChain:
    """A full provider family chain: HEAD → BODY → MEMORY."""
    family: ProviderFamily
    name: str
    description: str
    head: ChainNode
    body: ChainNode
    memory: ChainNode
    sense: ChainNode | None = None
    voice: ChainNode | None = None
    best_for: list[str] = field(default_factory=list)
    smart_home_capable: bool = False


# ---------------------------------------------------------------------------
# The Five Primary Chains
# ---------------------------------------------------------------------------


OPENAI_CHAIN = ProviderChain(
    family=ProviderFamily.OPENAI,
    name="OpenAI Chain",
    description="ChatGPT reasoning → Codex code execution → Embeddings memory",
    best_for=["code", "analysis", "general_reasoning", "creative", "plugins"],
    head=ChainNode(
        node_id="chatgpt_pro",
        name="ChatGPT (GPT-5 / o3)",
        role=ChainRole.HEAD,
        family=ProviderFamily.OPENAI,
        endpoint="https://api.openai.com/v1",
        api_key_env="OPENAI_API_KEY",
        model_id="gpt-4o",
        capabilities=["reasoning", "planning", "long_context", "vision"],
        cost_tier="high",
        latency_tier="medium",
    ),
    body=ChainNode(
        node_id="codex",
        name="Codex (OpenAI Code)",
        role=ChainRole.BODY,
        family=ProviderFamily.OPENAI,
        endpoint="https://api.openai.com/v1",
        api_key_env="OPENAI_API_KEY",
        model_id="gpt-4o",
        capabilities=["code_generation", "refactor", "tests", "github_pr"],
        cost_tier="medium",
        latency_tier="fast",
    ),
    memory=ChainNode(
        node_id="openai_embeddings",
        name="OpenAI Embeddings",
        role=ChainRole.MEMORY,
        family=ProviderFamily.OPENAI,
        endpoint="https://api.openai.com/v1",
        api_key_env="OPENAI_API_KEY",
        model_id="text-embedding-3-large",
        capabilities=["semantic_search", "vector_store", "retrieval"],
        cost_tier="low",
        latency_tier="fast",
    ),
)

GOOGLE_CHAIN = ProviderChain(
    family=ProviderFamily.GOOGLE,
    name="Google Chain",
    description="Gemini reasoning → Google Search → Google Drive/Docs storage",
    best_for=["research", "web_search", "documents", "email", "maps"],
    smart_home_capable=True,
    head=ChainNode(
        node_id="gemini_pro",
        name="Gemini Pro",
        role=ChainRole.HEAD,
        family=ProviderFamily.GOOGLE,
        endpoint="https://generativelanguage.googleapis.com/v1beta",
        api_key_env="GEMINI_API_KEY",
        model_id="gemini-1.5-pro",
        capabilities=["reasoning", "vision", "long_context", "grounding"],
        cost_tier="medium",
        latency_tier="medium",
    ),
    body=ChainNode(
        node_id="google_search",
        name="Google Search + SerpAPI",
        role=ChainRole.BODY,
        family=ProviderFamily.GOOGLE,
        endpoint="https://serpapi.com/search",
        api_key_env="SERP_API_KEY",
        model_id="search",
        capabilities=["web_search", "news", "images", "shopping"],
        cost_tier="low",
        latency_tier="fast",
    ),
    memory=ChainNode(
        node_id="google_drive",
        name="Google Drive + Docs",
        role=ChainRole.MEMORY,
        family=ProviderFamily.GOOGLE,
        endpoint="https://www.googleapis.com/drive/v3",
        api_key_env="GOOGLE_API_KEY",
        model_id="drive_v3",
        capabilities=["file_storage", "docs", "sheets", "slides", "retrieval"],
        cost_tier="low",
        latency_tier="medium",
    ),
    voice=ChainNode(
        node_id="google_home",
        name="Google Home / Smart Hub",
        role=ChainRole.VOICE,
        family=ProviderFamily.GOOGLE,
        endpoint="https://homegraph.googleapis.com",
        api_key_env="GOOGLE_HOME_API_KEY",
        model_id="home_graph",
        capabilities=["smart_home", "device_control", "routines", "notifications"],
        cost_tier="low",
        latency_tier="fast",
        offline_capable=True,
    ),
)

MICROSOFT_CHAIN = ProviderChain(
    family=ProviderFamily.MICROSOFT,
    name="Microsoft Chain",
    description="Copilot planning → Microsoft Graph execution → SharePoint memory",
    best_for=["office", "teams", "azure", "enterprise", "productivity"],
    head=ChainNode(
        node_id="copilot",
        name="Microsoft Copilot",
        role=ChainRole.HEAD,
        family=ProviderFamily.MICROSOFT,
        endpoint="https://api.cognitive.microsoft.com",
        api_key_env="AZURE_OPENAI_KEY",
        model_id="gpt-4o",
        capabilities=["reasoning", "office_integration", "teams", "enterprise"],
        cost_tier="high",
        latency_tier="medium",
    ),
    body=ChainNode(
        node_id="microsoft_graph",
        name="Microsoft Graph API",
        role=ChainRole.BODY,
        family=ProviderFamily.MICROSOFT,
        endpoint="https://graph.microsoft.com/v1.0",
        api_key_env="MICROSOFT_GRAPH_TOKEN",
        model_id="graph_v1",
        capabilities=["email", "calendar", "files", "teams_messages", "users"],
        cost_tier="low",
        latency_tier="fast",
    ),
    memory=ChainNode(
        node_id="sharepoint",
        name="SharePoint + OneDrive",
        role=ChainRole.MEMORY,
        family=ProviderFamily.MICROSOFT,
        endpoint="https://graph.microsoft.com/v1.0/drive",
        api_key_env="MICROSOFT_GRAPH_TOKEN",
        model_id="onedrive_v1",
        capabilities=["file_storage", "versioning", "search", "collaboration"],
        cost_tier="low",
        latency_tier="medium",
    ),
)

ANTHROPIC_CHAIN = ProviderChain(
    family=ProviderFamily.ANTHROPIC,
    name="Anthropic Chain",
    description="Claude reasoning → Computer Use execution → Artifact memory",
    best_for=["safety_critical", "code_review", "legal", "analysis", "desktop_control"],
    head=ChainNode(
        node_id="claude_pro",
        name="Claude (Sonnet / Opus)",
        role=ChainRole.HEAD,
        family=ProviderFamily.ANTHROPIC,
        endpoint="https://api.anthropic.com/v1",
        api_key_env="ANTHROPIC_API_KEY",
        model_id="claude-sonnet-4-6",
        capabilities=["reasoning", "code", "safety", "long_context", "analysis"],
        cost_tier="medium",
        latency_tier="medium",
    ),
    body=ChainNode(
        node_id="claude_computer_use",
        name="Claude Computer Use",
        role=ChainRole.BODY,
        family=ProviderFamily.ANTHROPIC,
        endpoint="https://api.anthropic.com/v1",
        api_key_env="ANTHROPIC_API_KEY",
        model_id="claude-sonnet-4-6",
        capabilities=["desktop_control", "browser", "screenshot", "mouse", "keyboard"],
        cost_tier="high",
        latency_tier="slow",
    ),
    memory=ChainNode(
        node_id="claude_artifacts",
        name="Claude Artifacts + Context",
        role=ChainRole.MEMORY,
        family=ProviderFamily.ANTHROPIC,
        endpoint="https://api.anthropic.com/v1",
        api_key_env="ANTHROPIC_API_KEY",
        model_id="claude-sonnet-4-6",
        capabilities=["artifacts", "long_context", "project_memory"],
        cost_tier="medium",
        latency_tier="medium",
    ),
)

AMAZON_CHAIN = ProviderChain(
    family=ProviderFamily.AMAZON,
    name="Amazon / Alexa Chain",
    description="Alexa voice → AWS Lambda execution → DynamoDB memory",
    best_for=["smart_home", "voice_commands", "iot", "aws_services"],
    smart_home_capable=True,
    head=ChainNode(
        node_id="alexa",
        name="Alexa Voice AI",
        role=ChainRole.HEAD,
        family=ProviderFamily.AMAZON,
        endpoint="https://api.amazonalexa.com",
        api_key_env="ALEXA_API_KEY",
        model_id="alexa_llm",
        capabilities=["voice", "smart_home", "routines", "skills"],
        cost_tier="low",
        latency_tier="fast",
    ),
    body=ChainNode(
        node_id="aws_lambda",
        name="AWS Lambda + IoT",
        role=ChainRole.BODY,
        family=ProviderFamily.AMAZON,
        endpoint="https://lambda.amazonaws.com",
        api_key_env="AWS_SECRET_ACCESS_KEY",
        model_id="lambda",
        capabilities=["serverless", "iot", "automation", "events"],
        cost_tier="low",
        latency_tier="fast",
    ),
    memory=ChainNode(
        node_id="dynamodb",
        name="AWS DynamoDB",
        role=ChainRole.MEMORY,
        family=ProviderFamily.AMAZON,
        endpoint="https://dynamodb.amazonaws.com",
        api_key_env="AWS_SECRET_ACCESS_KEY",
        model_id="dynamodb",
        capabilities=["key_value_store", "fast_retrieval", "scaling"],
        cost_tier="low",
        latency_tier="fast",
    ),
    voice=ChainNode(
        node_id="alexa_smart_home",
        name="Alexa Smart Home Hub",
        role=ChainRole.VOICE,
        family=ProviderFamily.AMAZON,
        endpoint="https://api.amazonalexa.com/v3/events",
        api_key_env="ALEXA_API_KEY",
        model_id="alexa_home",
        capabilities=["lights", "thermostat", "locks", "cameras", "routines"],
        cost_tier="low",
        latency_tier="fast",
        offline_capable=True,
    ),
)

LOCAL_CHAIN = ProviderChain(
    family=ProviderFamily.LOCAL,
    name="Local Ollama Chain",
    description="Ollama local LLM → local tools → local vector DB",
    best_for=["private_data", "offline", "low_cost", "fast_iteration"],
    head=ChainNode(
        node_id="ollama_head",
        name="Ollama (Llama3 / DeepSeek / Mistral)",
        role=ChainRole.HEAD,
        family=ProviderFamily.LOCAL,
        endpoint="http://localhost:11434",
        api_key_env="",
        model_id="llama3",
        capabilities=["reasoning", "code", "offline", "private"],
        cost_tier="low",
        latency_tier="fast",
        offline_capable=True,
    ),
    body=ChainNode(
        node_id="ollama_codellama",
        name="Ollama (CodeLlama / DeepSeek-Coder)",
        role=ChainRole.BODY,
        family=ProviderFamily.LOCAL,
        endpoint="http://localhost:11434",
        api_key_env="",
        model_id="deepseek-coder-v2",
        capabilities=["code_generation", "offline", "private"],
        cost_tier="low",
        latency_tier="fast",
        offline_capable=True,
    ),
    memory=ChainNode(
        node_id="qdrant_local",
        name="Qdrant (Local Vector DB)",
        role=ChainRole.MEMORY,
        family=ProviderFamily.LOCAL,
        endpoint="http://localhost:6333",
        api_key_env="",
        model_id="qdrant",
        capabilities=["vector_search", "embedding_store", "offline", "private"],
        cost_tier="low",
        latency_tier="fast",
        offline_capable=True,
    ),
)


ALL_CHAINS: dict[ProviderFamily, ProviderChain] = {
    ProviderFamily.OPENAI: OPENAI_CHAIN,
    ProviderFamily.GOOGLE: GOOGLE_CHAIN,
    ProviderFamily.MICROSOFT: MICROSOFT_CHAIN,
    ProviderFamily.ANTHROPIC: ANTHROPIC_CHAIN,
    ProviderFamily.AMAZON: AMAZON_CHAIN,
    ProviderFamily.LOCAL: LOCAL_CHAIN,
}


# ---------------------------------------------------------------------------
# Intent → Chain Classifier
# ---------------------------------------------------------------------------


INTENT_TO_FAMILY: list[tuple[list[str], ProviderFamily]] = [
    (["code", "build", "deploy", "github", "git", "test", "debug", "codex"], ProviderFamily.OPENAI),
    (["search", "research", "find", "google", "news", "web", "browse", "gemini"], ProviderFamily.GOOGLE),
    (["smart home", "alexa", "lights", "thermostat", "iot", "device", "turn on", "turn off"], ProviderFamily.AMAZON),
    (["office", "teams", "email", "outlook", "sharepoint", "excel", "copilot", "microsoft"], ProviderFamily.MICROSOFT),
    (["safe", "review", "audit", "legal", "security", "private", "claude", "anthropic"], ProviderFamily.ANTHROPIC),
    (["private", "offline", "local", "ollama", "llama", "no cloud", "on-device"], ProviderFamily.LOCAL),
]

SMART_HOME_KEYWORDS = [
    "alexa", "google home", "smart hub", "lights", "thermostat",
    "lock", "camera", "plug", "switch", "routine", "automaton",
    "turn on", "turn off", "dim", "temperature", "scene",
]


def classify_intent_to_chain(intent: str) -> ProviderFamily:
    text = intent.lower()
    scores: dict[ProviderFamily, int] = {}
    for keywords, family in INTENT_TO_FAMILY:
        score = sum(1 for kw in keywords if kw in text)
        if score:
            scores[family] = score
    if not scores:
        return ProviderFamily.OPENAI  # default
    return max(scores, key=lambda f: scores[f])


def is_smart_home_intent(intent: str) -> bool:
    text = intent.lower()
    return any(kw in text for kw in SMART_HOME_KEYWORDS)


# ---------------------------------------------------------------------------
# Chain Router
# ---------------------------------------------------------------------------


class AIProviderChainRouter:
    """
    Routes any intent through the dimensional chain of AI providers.

    Flow:
        1. Classify intent → best provider family
        2. Select chain role: HEAD for reasoning, BODY for execution, MEMORY for retrieval
        3. Execute against the chain node
        4. Fall through to LOCAL chain if cloud providers unavailable
    """

    def __init__(self) -> None:
        self.chains = ALL_CHAINS
        self._call_log: list[dict[str, Any]] = []

    def select_chain(self, intent: str) -> ProviderChain:
        family = classify_intent_to_chain(intent)
        chain = self.chains[family]
        api_key_env = chain.head.api_key_env
        if api_key_env and not os.getenv(api_key_env):
            logger.warning(
                f"[CHAIN] {family.value} chain selected but {api_key_env} not set — falling back to LOCAL"
            )
            return self.chains[ProviderFamily.LOCAL]
        return chain

    async def execute(
        self,
        intent: str,
        role: ChainRole = ChainRole.HEAD,
        context: str = "",
        override_family: ProviderFamily | None = None,
    ) -> dict[str, Any]:
        chain = (
            self.chains[override_family]
            if override_family
            else self.select_chain(intent)
        )

        node = {
            ChainRole.HEAD: chain.head,
            ChainRole.BODY: chain.body,
            ChainRole.MEMORY: chain.memory,
            ChainRole.SENSE: chain.sense or chain.head,
            ChainRole.VOICE: chain.voice or chain.head,
        }[role]

        start = time.time()
        result = await self._call_node(node, intent, context)
        elapsed = round(time.time() - start, 3)

        record = {
            "chain": chain.family.value,
            "node": node.node_id,
            "role": role.value,
            "intent_preview": intent[:100],
            "elapsed_seconds": elapsed,
            "status": "ok" if "error" not in result else "error",
        }
        self._call_log.append(record)
        logger.info(f"[CHAIN] {chain.family.value}:{role.value}:{node.node_id} → {elapsed}s")

        return {
            "chain": chain.family.value,
            "node_id": node.node_id,
            "model": node.model_id,
            "role": role.value,
            "elapsed_seconds": elapsed,
            **result,
        }

    async def execute_full_chain(
        self,
        intent: str,
        context: str = "",
        override_family: ProviderFamily | None = None,
    ) -> dict[str, Any]:
        """
        Run through the full chain: HEAD reasons, BODY executes, MEMORY stores.
        Returns all three results.
        """
        head_result = await self.execute(intent, ChainRole.HEAD, context, override_family)
        body_result = await self.execute(
            head_result.get("response", intent), ChainRole.BODY, context, override_family
        )
        memory_result = await self.execute(
            f"Store: {intent} → {body_result.get('response', '')[:500]}",
            ChainRole.MEMORY, context, override_family,
        )
        return {
            "head": head_result,
            "body": body_result,
            "memory": memory_result,
            "chain": head_result.get("chain"),
        }

    async def smart_home_dispatch(
        self,
        command: str,
    ) -> dict[str, Any]:
        """Route voice/text command to the smart home chain."""
        if not is_smart_home_intent(command):
            return {"status": "not_smart_home", "command": command}

        # Try Google Home first, then Alexa
        for family in (ProviderFamily.GOOGLE, ProviderFamily.AMAZON):
            chain = self.chains[family]
            if chain.smart_home_capable and chain.voice:
                result = await self._call_node(chain.voice, command, "")
                return {
                    "provider": family.value,
                    "hub": chain.voice.name,
                    "command": command,
                    **result,
                }
        return {"status": "no_smart_home_provider", "command": command}

    async def _call_node(
        self,
        node: ChainNode,
        prompt: str,
        context: str,
    ) -> dict[str, Any]:
        api_key = os.getenv(node.api_key_env) if node.api_key_env else None

        if node.family == ProviderFamily.LOCAL:
            return await self._call_ollama(node, prompt, context)

        if not api_key:
            return {
                "response": f"[{node.node_id}] API key {node.api_key_env} not configured.",
                "status": "unconfigured",
            }

        if node.family == ProviderFamily.ANTHROPIC:
            return await self._call_anthropic(node, api_key, prompt, context)

        if node.family in (ProviderFamily.OPENAI, ProviderFamily.MICROSOFT):
            return await self._call_openai_compat(node, api_key, prompt, context)

        if node.family == ProviderFamily.GOOGLE:
            return await self._call_gemini(node, api_key, prompt, context)

        if node.family == ProviderFamily.AMAZON:
            return {"response": f"[{node.name}] command dispatched: {prompt}", "status": "dispatched"}

        return {"response": f"[{node.node_id}] No handler for family {node.family.value}", "status": "unhandled"}

    async def _call_openai_compat(
        self, node: ChainNode, api_key: str, prompt: str, context: str
    ) -> dict[str, Any]:
        messages = []
        if context:
            messages.append({"role": "system", "content": context})
        messages.append({"role": "user", "content": prompt})
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    f"{node.endpoint}/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={"model": node.model_id, "messages": messages, "max_tokens": 2048},
                )
                data = resp.json()
                text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                return {"response": text, "status": "ok"}
        except Exception as e:
            return {"response": "", "error": str(e), "status": "error"}

    async def _call_anthropic(
        self, node: ChainNode, api_key: str, prompt: str, context: str
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "model": node.model_id,
            "max_tokens": 2048,
            "messages": [{"role": "user", "content": prompt}],
        }
        if context:
            body["system"] = context
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    f"{node.endpoint}/messages",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                    },
                    json=body,
                )
                data = resp.json()
                text = data.get("content", [{}])[0].get("text", "")
                return {"response": text, "status": "ok"}
        except Exception as e:
            return {"response": "", "error": str(e), "status": "error"}

    async def _call_gemini(
        self, node: ChainNode, api_key: str, prompt: str, context: str
    ) -> dict[str, Any]:
        full_prompt = f"{context}\n\n{prompt}" if context else prompt
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                url = (
                    f"{node.endpoint}/models/{node.model_id}"
                    f":generateContent?key={api_key}"
                )
                resp = await client.post(
                    url,
                    json={"contents": [{"parts": [{"text": full_prompt}]}]},
                )
                data = resp.json()
                text = (
                    data.get("candidates", [{}])[0]
                    .get("content", {})
                    .get("parts", [{}])[0]
                    .get("text", "")
                )
                return {"response": text, "status": "ok"}
        except Exception as e:
            return {"response": "", "error": str(e), "status": "error"}

    async def _call_ollama(
        self, node: ChainNode, prompt: str, context: str
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"model": node.model_id, "prompt": prompt, "stream": False}
        if context:
            payload["system"] = context
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(f"{node.endpoint}/api/generate", json=payload)
                return {"response": resp.json().get("response", ""), "status": "ok"}
        except Exception as e:
            return {"response": "", "error": str(e), "status": "error"}

    def chain_map(self) -> dict[str, Any]:
        """Return the full dimensional chain map for inspection."""
        return {
            family.value: {
                "name": chain.name,
                "description": chain.description,
                "best_for": chain.best_for,
                "smart_home": chain.smart_home_capable,
                "nodes": {
                    "head": {"id": chain.head.node_id, "model": chain.head.model_id},
                    "body": {"id": chain.body.node_id, "model": chain.body.model_id},
                    "memory": {"id": chain.memory.node_id, "model": chain.memory.model_id},
                    "voice": {"id": chain.voice.node_id} if chain.voice else None,
                },
            }
            for family, chain in self.chains.items()
        }


# Singleton
chain_router = AIProviderChainRouter()


# ---------------------------------------------------------------------------
# Quick simulation for troubleshooting
# ---------------------------------------------------------------------------


def simulate_chain_routing(intent: str) -> dict[str, Any]:
    """Dry-run routing without making API calls — for diagnostics."""
    family = classify_intent_to_chain(intent)
    chain = ALL_CHAINS[family]
    is_sh = is_smart_home_intent(intent)
    return {
        "intent": intent,
        "selected_family": family.value,
        "chain_name": chain.name,
        "head": chain.head.node_id,
        "body": chain.body.node_id,
        "memory": chain.memory.node_id,
        "voice": chain.voice.node_id if chain.voice else None,
        "smart_home_trigger": is_sh,
        "best_for": chain.best_for,
        "api_key_required": chain.head.api_key_env,
        "api_key_set": bool(os.getenv(chain.head.api_key_env)) if chain.head.api_key_env else True,
        "offline_fallback": chain.head.offline_capable,
    }


if __name__ == "__main__":
    import json
    test_intents = [
        "Build me a Python package and push it to PyPI",
        "Search Google for the latest AI news",
        "Turn on the living room lights",
        "Review this code for security issues",
        "Send a Teams message to the team",
        "Run this locally with no internet",
    ]
    print("=== CHAIN ROUTING SIMULATION ===\n")
    for intent in test_intents:
        result = simulate_chain_routing(intent)
        print(f"Intent: {intent}")
        print(f"  → {result['selected_family']} chain: {result['head']} → {result['body']} → {result['memory']}")
        if result["smart_home_trigger"]:
            print(f"  → Smart Home: {result['voice']}")
        print()
