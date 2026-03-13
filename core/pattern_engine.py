"""
ARK95X Pattern Prediction Engine
=================================
Knowledge graph schema for the Pattern Prediction Engine, supporting:
    - ChartNode (cosmic, human design, akashic, numerology, gene keys, natal, etc.)
    - PatternEdge (cycle, trigger, alignment, conflict)
    - PredictionResult with confidence scores
    - Storage in Neo4j (graph), pgvector (semantic), Qdrant (embedding similarity)
    - Timing advisor that maps chart data to decision windows
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from loguru import logger
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ChartType(str, Enum):
    COSMIC_CHART = "cosmic_chart"
    HUMAN_DESIGN = "human_design"
    AKASHIC = "akashic"
    NUMEROLOGY = "numerology"
    GENE_KEYS = "gene_keys"
    NATAL = "natal"
    PROGRESSED = "progressed"
    SOLAR_RETURN = "solar_return"
    LUNAR_RETURN = "lunar_return"
    TRANSIT = "transit"
    COMPOSITE = "composite"
    SYNASTRY = "synastry"
    HORARY = "horary"
    ELECTIONAL = "electional"


class EdgeType(str, Enum):
    CYCLE = "cycle"
    TRIGGER = "trigger"
    ALIGNMENT = "alignment"
    CONFLICT = "conflict"


class TimingSignal(str, Enum):
    GREEN = "green"        # Optimal window — proceed
    YELLOW = "yellow"      # Caution — review conditions
    RED = "red"            # Avoid — high friction expected
    NEUTRAL = "neutral"    # No strong signal


class StorageBackend(str, Enum):
    NEO4J = "neo4j"
    PGVECTOR = "pgvector"
    QDRANT = "qdrant"


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")
PGVECTOR_URL = os.getenv("POSTGRES_URL", "postgresql://ark95x:password@localhost:5432/sovereign")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")


# ---------------------------------------------------------------------------
# Graph Schema Models
# ---------------------------------------------------------------------------


class ChartNode(BaseModel):
    """A node in the pattern knowledge graph representing a chart or data point."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    chart_type: ChartType
    label: str = Field(..., description="Human-readable label for this chart node")
    subject: str = Field("", description="Entity this chart belongs to")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    data: dict[str, Any] = Field(
        default_factory=dict,
        description="Chart-specific data (positions, numbers, keys, etc.)",
    )
    embedding: list[float] | None = Field(
        None, description="Vector embedding for semantic search"
    )
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_neo4j_props(self) -> dict[str, Any]:
        """Convert to Neo4j-compatible property dict (no nested objects)."""
        return {
            "id": self.id,
            "chart_type": self.chart_type.value,
            "label": self.label,
            "subject": self.subject,
            "timestamp": self.timestamp,
        }


class PatternEdge(BaseModel):
    """An edge connecting two ChartNodes representing a detected pattern."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    edge_type: EdgeType
    source_id: str = Field(..., description="Source ChartNode ID")
    target_id: str = Field(..., description="Target ChartNode ID")
    weight: float = Field(1.0, ge=0.0, le=1.0, description="Relationship strength")
    description: str = ""
    detected_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_neo4j_props(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "edge_type": self.edge_type.value,
            "weight": self.weight,
            "description": self.description,
            "detected_at": self.detected_at,
        }


class PredictionResult(BaseModel):
    """Result of a pattern-based prediction with confidence scores."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    prediction: str = Field(..., description="The prediction text")
    confidence: float = Field(..., ge=0.0, le=1.0)
    source_patterns: list[str] = Field(
        default_factory=list,
        description="IDs of PatternEdges that contributed",
    )
    source_charts: list[str] = Field(
        default_factory=list,
        description="IDs of ChartNodes that contributed",
    )
    timing_signal: TimingSignal = TimingSignal.NEUTRAL
    decision_window: DecisionWindow | None = None
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class DecisionWindow(BaseModel):
    """A time window recommended for action based on pattern analysis."""

    start: str = Field(..., description="ISO datetime for window start")
    end: str = Field(..., description="ISO datetime for window end")
    signal: TimingSignal
    reason: str = ""
    contributing_factors: list[str] = Field(default_factory=list)
    confidence: float = Field(0.5, ge=0.0, le=1.0)


# Fix forward reference
PredictionResult.model_rebuild()


# ---------------------------------------------------------------------------
# Storage Adapters
# ---------------------------------------------------------------------------


class Neo4jAdapter:
    """Adapter for Neo4j graph database operations."""

    def __init__(self, uri: str = NEO4J_URI, user: str = NEO4J_USER,
                 password: str = NEO4J_PASSWORD) -> None:
        self.uri = uri
        self.user = user
        self.password = password
        self._driver: Any = None

    def connect(self) -> None:
        """Establish Neo4j connection."""
        try:
            from neo4j import GraphDatabase
            self._driver = GraphDatabase.driver(
                self.uri, auth=(self.user, self.password)
            )
            logger.info(f"Neo4j connected at {self.uri}")
        except ImportError:
            logger.warning("neo4j driver not installed — graph queries unavailable")
        except Exception as e:
            logger.error(f"Neo4j connection failed: {e}")

    def close(self) -> None:
        if self._driver:
            self._driver.close()

    def create_node(self, node: ChartNode) -> str:
        """Create a ChartNode in Neo4j."""
        if not self._driver:
            logger.warning("Neo4j not connected, skipping node creation")
            return node.id

        query = """
        CREATE (n:ChartNode {id: $id, chart_type: $chart_type,
                label: $label, subject: $subject, timestamp: $timestamp})
        RETURN n.id
        """
        with self._driver.session() as session:
            result = session.run(query, **node.to_neo4j_props())
            return result.single()[0]

    def create_edge(self, edge: PatternEdge) -> str:
        """Create a PatternEdge between two ChartNodes."""
        if not self._driver:
            logger.warning("Neo4j not connected, skipping edge creation")
            return edge.id

        query = """
        MATCH (a:ChartNode {id: $source_id}), (b:ChartNode {id: $target_id})
        CREATE (a)-[r:PATTERN {id: $id, edge_type: $edge_type,
                weight: $weight, description: $description,
                detected_at: $detected_at}]->(b)
        RETURN r.id
        """
        params = {
            "source_id": edge.source_id,
            "target_id": edge.target_id,
            **edge.to_neo4j_props(),
        }
        with self._driver.session() as session:
            result = session.run(query, **params)
            return result.single()[0]

    def find_patterns(self, node_id: str, depth: int = 2) -> list[dict[str, Any]]:
        """Find patterns connected to a node within N hops."""
        if not self._driver:
            return []

        query = """
        MATCH path = (n:ChartNode {id: $node_id})-[*1..$depth]-(m:ChartNode)
        RETURN path LIMIT 50
        """
        with self._driver.session() as session:
            result = session.run(query, node_id=node_id, depth=depth)
            return [record.data() for record in result]


class PgVectorAdapter:
    """Adapter for pgvector semantic search operations."""

    def __init__(self, connection_url: str = PGVECTOR_URL) -> None:
        self.connection_url = connection_url
        self._pool: Any = None

    async def connect(self) -> None:
        """Establish async connection pool."""
        try:
            import asyncpg
            self._pool = await asyncpg.create_pool(self.connection_url)
            # Ensure the vector extension and table exist
            async with self._pool.acquire() as conn:
                await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS pattern_embeddings (
                        id TEXT PRIMARY KEY,
                        chart_type TEXT NOT NULL,
                        label TEXT NOT NULL,
                        subject TEXT DEFAULT '',
                        embedding vector(1536),
                        metadata JSONB DEFAULT '{}',
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    )
                """)
            logger.info("pgvector adapter connected and schema ensured")
        except ImportError:
            logger.warning("asyncpg not installed — pgvector unavailable")
        except Exception as e:
            logger.error(f"pgvector connection failed: {e}")

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()

    async def store_embedding(self, node: ChartNode) -> None:
        """Store a ChartNode's embedding in pgvector."""
        if not self._pool or not node.embedding:
            return

        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO pattern_embeddings (id, chart_type, label, subject, embedding, metadata)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (id) DO UPDATE SET embedding = $5, metadata = $6
                """,
                node.id, node.chart_type.value, node.label,
                node.subject, str(node.embedding), str(node.metadata),
            )

    async def semantic_search(
        self, query_embedding: list[float], limit: int = 10
    ) -> list[dict[str, Any]]:
        """Find the nearest chart nodes by embedding similarity."""
        if not self._pool:
            return []

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, chart_type, label, subject,
                       embedding <-> $1::vector AS distance
                FROM pattern_embeddings
                ORDER BY distance
                LIMIT $2
                """,
                str(query_embedding), limit,
            )
            return [dict(row) for row in rows]


class QdrantAdapter:
    """Adapter for Qdrant vector similarity search."""

    def __init__(self, url: str = QDRANT_URL) -> None:
        self.url = url
        self._client: Any = None
        self.collection_name = "ark95x_patterns"

    def connect(self) -> None:
        """Connect to Qdrant."""
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams

            self._client = QdrantClient(url=self.url)
            # Ensure collection exists
            collections = self._client.get_collections().collections
            names = [c.name for c in collections]
            if self.collection_name not in names:
                self._client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
                )
            logger.info(f"Qdrant connected at {self.url}")
        except ImportError:
            logger.warning("qdrant-client not installed — Qdrant unavailable")
        except Exception as e:
            logger.error(f"Qdrant connection failed: {e}")

    def upsert_node(self, node: ChartNode) -> None:
        """Upsert a ChartNode into Qdrant."""
        if not self._client or not node.embedding:
            return

        from qdrant_client.models import PointStruct

        point = PointStruct(
            id=node.id,
            vector=node.embedding,
            payload={
                "chart_type": node.chart_type.value,
                "label": node.label,
                "subject": node.subject,
                "timestamp": node.timestamp,
            },
        )
        self._client.upsert(
            collection_name=self.collection_name, points=[point]
        )

    def search_similar(
        self, query_vector: list[float], limit: int = 10
    ) -> list[dict[str, Any]]:
        """Search for similar patterns by vector."""
        if not self._client:
            return []

        results = self._client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit,
        )
        return [
            {"id": r.id, "score": r.score, "payload": r.payload}
            for r in results
        ]


# ---------------------------------------------------------------------------
# Timing Advisor
# ---------------------------------------------------------------------------


class TimingAdvisor:
    """Maps chart data to decision windows using pattern analysis."""

    def __init__(self) -> None:
        self._windows: list[DecisionWindow] = []

    def evaluate_window(
        self,
        charts: list[ChartNode],
        edges: list[PatternEdge],
    ) -> DecisionWindow:
        """Evaluate current patterns to determine optimal decision timing.

        Scoring:
            - Alignment edges increase confidence and push toward GREEN
            - Conflict edges decrease confidence and push toward RED
            - Cycle edges provide context but are neutral
            - Trigger edges indicate urgency
        """
        alignment_count = sum(1 for e in edges if e.edge_type == EdgeType.ALIGNMENT)
        conflict_count = sum(1 for e in edges if e.edge_type == EdgeType.CONFLICT)
        trigger_count = sum(1 for e in edges if e.edge_type == EdgeType.TRIGGER)

        total = max(len(edges), 1)
        alignment_ratio = alignment_count / total
        conflict_ratio = conflict_count / total

        # Determine signal
        if alignment_ratio > 0.6 and conflict_ratio < 0.2:
            signal = TimingSignal.GREEN
        elif conflict_ratio > 0.5:
            signal = TimingSignal.RED
        elif alignment_ratio > 0.3:
            signal = TimingSignal.YELLOW
        else:
            signal = TimingSignal.NEUTRAL

        confidence = round(
            min(1.0, (alignment_ratio * 0.7 + (1 - conflict_ratio) * 0.3)), 3
        )

        factors = []
        if alignment_count:
            factors.append(f"{alignment_count} alignment(s) detected")
        if conflict_count:
            factors.append(f"{conflict_count} conflict(s) detected")
        if trigger_count:
            factors.append(f"{trigger_count} trigger(s) active")

        now = datetime.now(timezone.utc).isoformat()
        window = DecisionWindow(
            start=now,
            end=now,  # Would be calculated from actual chart data in production
            signal=signal,
            reason=f"Pattern analysis: {alignment_count}A/{conflict_count}C/{trigger_count}T",
            contributing_factors=factors,
            confidence=confidence,
        )
        self._windows.append(window)
        return window


# ---------------------------------------------------------------------------
# Pattern Engine (Orchestrator)
# ---------------------------------------------------------------------------


class PatternEngine:
    """Orchestrates pattern storage, search, and prediction across all backends."""

    def __init__(self) -> None:
        self.neo4j = Neo4jAdapter()
        self.pgvector = PgVectorAdapter()
        self.qdrant = QdrantAdapter()
        self.timing = TimingAdvisor()
        self._nodes: dict[str, ChartNode] = {}
        self._edges: dict[str, PatternEdge] = {}
        logger.info("PatternEngine initialized")

    def connect_all(self) -> None:
        """Connect to all storage backends (best-effort)."""
        self.neo4j.connect()
        self.qdrant.connect()
        # pgvector requires async — call connect in an async context

    def add_node(self, node: ChartNode) -> str:
        """Add a chart node to all backends."""
        self._nodes[node.id] = node
        self.neo4j.create_node(node)
        self.qdrant.upsert_node(node)
        logger.debug(f"Node added: {node.id} ({node.chart_type.value})")
        return node.id

    def add_edge(self, edge: PatternEdge) -> str:
        """Add a pattern edge to all backends."""
        self._edges[edge.id] = edge
        self.neo4j.create_edge(edge)
        logger.debug(
            f"Edge added: {edge.source_id} --[{edge.edge_type.value}]--> {edge.target_id}"
        )
        return edge.id

    def predict(
        self,
        chart_ids: list[str],
        query: str = "",
    ) -> PredictionResult:
        """Generate a prediction based on the specified charts and their patterns."""
        charts = [self._nodes[cid] for cid in chart_ids if cid in self._nodes]
        related_edges = [
            e for e in self._edges.values()
            if e.source_id in chart_ids or e.target_id in chart_ids
        ]

        window = self.timing.evaluate_window(charts, related_edges)

        confidence = window.confidence
        edge_ids = [e.id for e in related_edges]
        prediction_text = (
            f"Based on {len(charts)} chart(s) and {len(related_edges)} pattern(s): "
            f"Timing signal is {window.signal.value} "
            f"(confidence {confidence:.1%}). "
            f"{window.reason}"
        )

        return PredictionResult(
            prediction=prediction_text,
            confidence=confidence,
            source_patterns=edge_ids,
            source_charts=chart_ids,
            timing_signal=window.signal,
            decision_window=window,
        )

    def search_similar(self, query_vector: list[float], limit: int = 10) -> list[dict]:
        """Search for similar patterns using Qdrant."""
        return self.qdrant.search_similar(query_vector, limit)

    def graph_stats(self) -> dict[str, Any]:
        """Return current graph statistics."""
        return {
            "total_nodes": len(self._nodes),
            "total_edges": len(self._edges),
            "chart_types": list({n.chart_type.value for n in self._nodes.values()}),
            "edge_types": list({e.edge_type.value for e in self._edges.values()}),
            "backends": {
                "neo4j": self.neo4j._driver is not None,
                "pgvector": self.pgvector._pool is not None,
                "qdrant": self.qdrant._client is not None,
            },
        }
