"""
ARK95X Self-Learning Loop
==========================
Continuous improvement system that discovers, benchmarks, and tracks AI models:

    - ModelScanner: Monitors HuggingFace trending, RSS feeds, X/Twitter for new releases
    - BenchmarkPipeline: Tests new models against ARK95X task taxonomy
    - ROITracker: Logs every task with time_saved, value_generated, model_used, accuracy_score
    - CompoundingMetrics: Calculates daily improvement rate toward 0.5%/day target
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any
from uuid import uuid4

import httpx
from loguru import logger
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

HUGGINGFACE_API = "https://huggingface.co/api"
DAILY_IMPROVEMENT_TARGET = 0.005  # 0.5% per day

# Task taxonomy categories for benchmarking
TASK_TAXONOMY: list[str] = [
    "code_generation",
    "code_review",
    "research",
    "strategic_planning",
    "creative_writing",
    "data_analysis",
    "summarization",
    "translation",
    "reasoning",
    "integration",
]


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ScanSource(str, Enum):
    HUGGINGFACE = "huggingface"
    RSS = "rss"
    TWITTER = "twitter"
    GITHUB = "github"
    MANUAL = "manual"


class BenchmarkStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class DiscoveredModel(BaseModel):
    """A newly discovered AI model from scanning."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    source: ScanSource
    source_url: str = ""
    description: str = ""
    tags: list[str] = Field(default_factory=list)
    downloads: int = 0
    likes: int = 0
    discovered_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    benchmark_status: BenchmarkStatus = BenchmarkStatus.PENDING
    benchmark_score: float | None = None
    recommended_for: list[str] = Field(
        default_factory=list,
        description="Task taxonomy categories this model suits",
    )


class BenchmarkResult(BaseModel):
    """Result of benchmarking a model against the task taxonomy."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    model_name: str
    task_category: str
    score: float = Field(0.0, ge=0.0, le=1.0)
    latency_ms: float = 0.0
    tokens_per_second: float = 0.0
    error: str | None = None
    tested_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class TaskROIEntry(BaseModel):
    """ROI tracking entry for a single task execution."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    task_description: str
    model_used: str
    time_saved_minutes: float = 0.0
    value_generated_usd: float = 0.0
    accuracy_score: float = Field(0.0, ge=0.0, le=1.0)
    obelisk_function: str = ""
    vertical: str = ""
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class DailyMetrics(BaseModel):
    """Daily compounding metrics summary."""

    date: str
    tasks_completed: int = 0
    total_time_saved_minutes: float = 0.0
    total_value_generated_usd: float = 0.0
    avg_accuracy: float = 0.0
    improvement_rate: float = 0.0
    target_rate: float = DAILY_IMPROVEMENT_TARGET
    on_track: bool = False
    models_used: dict[str, int] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Model Scanner
# ---------------------------------------------------------------------------


class ModelScanner:
    """Scans external sources for new AI model releases."""

    def __init__(self) -> None:
        self._discovered: list[DiscoveredModel] = []
        self._rss_feeds: list[str] = [
            "https://huggingface.co/blog/feed.xml",
        ]
        logger.info("ModelScanner initialized")

    async def scan_huggingface_trending(self, limit: int = 20) -> list[DiscoveredModel]:
        """Fetch trending models from HuggingFace."""
        models: list[DiscoveredModel] = []
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    f"{HUGGINGFACE_API}/models",
                    params={
                        "sort": "trending",
                        "limit": limit,
                        "direction": -1,
                    },
                )
                resp.raise_for_status()
                data = resp.json()

                for item in data:
                    model = DiscoveredModel(
                        name=item.get("id", "unknown"),
                        source=ScanSource.HUGGINGFACE,
                        source_url=f"https://huggingface.co/{item.get('id', '')}",
                        description=item.get("description", "")[:500],
                        tags=item.get("tags", [])[:10],
                        downloads=item.get("downloads", 0),
                        likes=item.get("likes", 0),
                    )
                    models.append(model)
                    self._discovered.append(model)

                logger.info(f"HuggingFace scan: found {len(models)} trending models")
        except Exception as e:
            logger.error(f"HuggingFace scan failed: {e}")

        return models

    async def scan_rss_feeds(self) -> list[DiscoveredModel]:
        """Scan RSS feeds for new model announcements."""
        models: list[DiscoveredModel] = []
        for feed_url in self._rss_feeds:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(feed_url)
                    resp.raise_for_status()
                    # Simple extraction — production would use feedparser
                    content = resp.text
                    if "model" in content.lower() or "release" in content.lower():
                        model = DiscoveredModel(
                            name=f"rss_discovery_{len(self._discovered)}",
                            source=ScanSource.RSS,
                            source_url=feed_url,
                            description="Discovered via RSS feed monitoring",
                        )
                        models.append(model)
                        self._discovered.append(model)
            except Exception as e:
                logger.warning(f"RSS scan failed for {feed_url}: {e}")

        logger.info(f"RSS scan: found {len(models)} potential discoveries")
        return models

    async def scan_twitter_signals(self) -> list[DiscoveredModel]:
        """Scan X/Twitter for new model release signals.

        Requires TWITTER_BEARER_TOKEN. Searches for model release announcements
        from key accounts.
        """
        bearer = os.getenv("TWITTER_BEARER_TOKEN")
        if not bearer:
            logger.debug("Twitter scan skipped — no bearer token")
            return []

        models: list[DiscoveredModel] = []
        try:
            query = "(new model OR model release OR open source LLM) -is:retweet"
            headers = {"Authorization": f"Bearer {bearer}"}
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    "https://api.twitter.com/2/tweets/search/recent",
                    headers=headers,
                    params={"query": query, "max_results": 10},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    for tweet in data.get("data", []):
                        model = DiscoveredModel(
                            name=f"twitter_{tweet.get('id', '')}",
                            source=ScanSource.TWITTER,
                            source_url=f"https://twitter.com/i/status/{tweet.get('id', '')}",
                            description=tweet.get("text", "")[:500],
                        )
                        models.append(model)
                        self._discovered.append(model)
        except Exception as e:
            logger.warning(f"Twitter scan failed: {e}")

        logger.info(f"Twitter scan: found {len(models)} signals")
        return models

    async def run_full_scan(self) -> list[DiscoveredModel]:
        """Run all scanners and return combined results."""
        results: list[DiscoveredModel] = []
        hf = await self.scan_huggingface_trending()
        rss = await self.scan_rss_feeds()
        twitter = await self.scan_twitter_signals()
        results.extend(hf)
        results.extend(rss)
        results.extend(twitter)
        logger.info(f"Full scan complete: {len(results)} models discovered")
        return results

    def get_discovered(self) -> list[DiscoveredModel]:
        return list(self._discovered)


# ---------------------------------------------------------------------------
# Benchmark Pipeline
# ---------------------------------------------------------------------------


class BenchmarkPipeline:
    """Tests discovered models against the ARK95X task taxonomy."""

    def __init__(self) -> None:
        self._results: list[BenchmarkResult] = []
        logger.info("BenchmarkPipeline initialized")

    async def benchmark_model(
        self,
        model_name: str,
        endpoint: str,
        task_category: str,
        test_prompt: str = "",
    ) -> BenchmarkResult:
        """Benchmark a single model on a single task category."""
        if not test_prompt:
            test_prompt = self._generate_test_prompt(task_category)

        start = time.time()
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Try OpenAI-compatible API format
                resp = await client.post(
                    f"{endpoint}/chat/completions",
                    json={
                        "model": model_name,
                        "messages": [{"role": "user", "content": test_prompt}],
                        "max_tokens": 512,
                    },
                    headers={"Content-Type": "application/json"},
                )
                latency = (time.time() - start) * 1000

                if resp.status_code == 200:
                    data = resp.json()
                    response_text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    tokens = data.get("usage", {}).get("completion_tokens", 0)
                    tps = tokens / max(latency / 1000, 0.01)
                    score = self._evaluate_response(response_text, task_category)
                else:
                    score = 0.0
                    tps = 0.0

                result = BenchmarkResult(
                    model_name=model_name,
                    task_category=task_category,
                    score=score,
                    latency_ms=round(latency, 1),
                    tokens_per_second=round(tps, 1),
                )
        except Exception as e:
            latency = (time.time() - start) * 1000
            result = BenchmarkResult(
                model_name=model_name,
                task_category=task_category,
                score=0.0,
                latency_ms=round(latency, 1),
                error=str(e)[:300],
            )

        self._results.append(result)
        return result

    async def run_full_benchmark(
        self,
        model_name: str,
        endpoint: str,
    ) -> list[BenchmarkResult]:
        """Benchmark a model across all task categories."""
        results = []
        for category in TASK_TAXONOMY:
            result = await self.benchmark_model(model_name, endpoint, category)
            results.append(result)
        return results

    def _generate_test_prompt(self, category: str) -> str:
        """Generate a test prompt for a task category."""
        prompts: dict[str, str] = {
            "code_generation": "Write a Python function that implements binary search on a sorted list.",
            "code_review": "Review this code for bugs: `def add(a, b): return a - b`",
            "research": "What are the key differences between transformer and mamba architectures?",
            "strategic_planning": "Outline a 90-day go-to-market strategy for a B2B SaaS product.",
            "creative_writing": "Write a haiku about artificial intelligence.",
            "data_analysis": "Explain how you would approach analyzing customer churn data.",
            "summarization": "Summarize the concept of attention mechanisms in neural networks in 2 sentences.",
            "translation": "Translate 'The future of AI is collaborative' to French and Spanish.",
            "reasoning": "If all roses are flowers and some flowers fade quickly, can we conclude that some roses fade quickly?",
            "integration": "Describe how to connect a FastAPI backend to a PostgreSQL database with async support.",
        }
        return prompts.get(category, f"Complete a {category} task to the best of your ability.")

    def _evaluate_response(self, response: str, category: str) -> float:
        """Simple heuristic scoring of a model response."""
        if not response:
            return 0.0

        score = 0.3  # Base score for any non-empty response
        word_count = len(response.split())

        # Length-based scoring
        if word_count >= 20:
            score += 0.2
        if word_count >= 50:
            score += 0.1

        # Category-specific quality signals
        if category == "code_generation" and ("def " in response or "function" in response):
            score += 0.2
        elif category == "code_review" and ("bug" in response.lower() or "issue" in response.lower()):
            score += 0.2
        elif category == "reasoning" and ("therefore" in response.lower() or "conclude" in response.lower()):
            score += 0.2
        else:
            score += 0.1  # Generic quality boost

        return min(1.0, round(score, 3))

    def get_results(self, model_name: str | None = None) -> list[BenchmarkResult]:
        if model_name:
            return [r for r in self._results if r.model_name == model_name]
        return list(self._results)

    def leaderboard(self) -> list[dict[str, Any]]:
        """Generate a model leaderboard sorted by average score."""
        scores: dict[str, list[float]] = {}
        for r in self._results:
            if r.model_name not in scores:
                scores[r.model_name] = []
            scores[r.model_name].append(r.score)

        board = []
        for model_name, model_scores in scores.items():
            avg = sum(model_scores) / len(model_scores) if model_scores else 0
            board.append({
                "model": model_name,
                "avg_score": round(avg, 3),
                "tests": len(model_scores),
            })

        return sorted(board, key=lambda x: x["avg_score"], reverse=True)


# ---------------------------------------------------------------------------
# ROI Tracker
# ---------------------------------------------------------------------------


class ROITracker:
    """Tracks ROI for every task execution."""

    def __init__(self) -> None:
        self._entries: list[TaskROIEntry] = []
        logger.info("ROITracker initialized")

    def log_task(
        self,
        task_description: str,
        model_used: str,
        time_saved_minutes: float = 0.0,
        value_generated_usd: float = 0.0,
        accuracy_score: float = 0.0,
        obelisk_function: str = "",
        vertical: str = "",
    ) -> TaskROIEntry:
        """Log a completed task with its ROI metrics."""
        entry = TaskROIEntry(
            task_description=task_description,
            model_used=model_used,
            time_saved_minutes=time_saved_minutes,
            value_generated_usd=value_generated_usd,
            accuracy_score=accuracy_score,
            obelisk_function=obelisk_function,
            vertical=vertical,
        )
        self._entries.append(entry)
        logger.debug(
            f"ROI logged: {model_used} | {time_saved_minutes}min saved | "
            f"${value_generated_usd} value | {accuracy_score:.0%} accuracy"
        )
        return entry

    def get_entries(
        self, model: str | None = None, vertical: str | None = None
    ) -> list[TaskROIEntry]:
        entries = self._entries
        if model:
            entries = [e for e in entries if e.model_used == model]
        if vertical:
            entries = [e for e in entries if e.vertical == vertical]
        return entries

    def total_time_saved(self) -> float:
        return sum(e.time_saved_minutes for e in self._entries)

    def total_value_generated(self) -> float:
        return sum(e.value_generated_usd for e in self._entries)

    def avg_accuracy(self) -> float:
        if not self._entries:
            return 0.0
        return sum(e.accuracy_score for e in self._entries) / len(self._entries)

    def model_usage_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for e in self._entries:
            counts[e.model_used] = counts.get(e.model_used, 0) + 1
        return counts

    def summary(self) -> dict[str, Any]:
        return {
            "total_tasks": len(self._entries),
            "total_time_saved_minutes": round(self.total_time_saved(), 1),
            "total_value_generated_usd": round(self.total_value_generated(), 2),
            "avg_accuracy": round(self.avg_accuracy(), 3),
            "model_usage": self.model_usage_counts(),
        }


# ---------------------------------------------------------------------------
# Compounding Metrics
# ---------------------------------------------------------------------------


class CompoundingMetrics:
    """Calculates daily improvement rates toward the 0.5%/day target."""

    def __init__(self, roi_tracker: ROITracker) -> None:
        self.roi = roi_tracker
        self._daily_snapshots: list[DailyMetrics] = []
        logger.info("CompoundingMetrics initialized (target: 0.5%/day)")

    def snapshot_day(self, date: str | None = None) -> DailyMetrics:
        """Generate a daily metrics snapshot."""
        target_date = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # Filter entries for this date
        day_entries = [
            e for e in self.roi.get_entries()
            if e.timestamp.startswith(target_date)
        ]

        tasks = len(day_entries)
        time_saved = sum(e.time_saved_minutes for e in day_entries)
        value = sum(e.value_generated_usd for e in day_entries)
        accuracy = (
            sum(e.accuracy_score for e in day_entries) / tasks if tasks else 0.0
        )

        # Calculate improvement rate vs previous day
        improvement_rate = 0.0
        if len(self._daily_snapshots) >= 1:
            prev = self._daily_snapshots[-1]
            if prev.avg_accuracy > 0:
                improvement_rate = (accuracy - prev.avg_accuracy) / prev.avg_accuracy

        model_usage: dict[str, int] = {}
        for e in day_entries:
            model_usage[e.model_used] = model_usage.get(e.model_used, 0) + 1

        metrics = DailyMetrics(
            date=target_date,
            tasks_completed=tasks,
            total_time_saved_minutes=round(time_saved, 1),
            total_value_generated_usd=round(value, 2),
            avg_accuracy=round(accuracy, 3),
            improvement_rate=round(improvement_rate, 4),
            on_track=improvement_rate >= DAILY_IMPROVEMENT_TARGET,
            models_used=model_usage,
        )

        self._daily_snapshots.append(metrics)
        return metrics

    def compound_growth_projection(self, days: int = 30) -> dict[str, Any]:
        """Project compounding growth at the target rate."""
        current_accuracy = self.roi.avg_accuracy() or 0.5
        projections: list[dict[str, float]] = []

        value = current_accuracy
        for day in range(1, days + 1):
            value *= (1 + DAILY_IMPROVEMENT_TARGET)
            projections.append({
                "day": day,
                "projected_accuracy": round(min(value, 1.0), 4),
            })

        return {
            "starting_accuracy": round(current_accuracy, 3),
            "daily_target": DAILY_IMPROVEMENT_TARGET,
            "projection_days": days,
            "final_projected_accuracy": projections[-1]["projected_accuracy"] if projections else current_accuracy,
            "projections": projections,
        }

    def streak(self) -> int:
        """Count consecutive days meeting the improvement target."""
        count = 0
        for snapshot in reversed(self._daily_snapshots):
            if snapshot.on_track:
                count += 1
            else:
                break
        return count

    def get_snapshots(self) -> list[DailyMetrics]:
        return list(self._daily_snapshots)

    def summary(self) -> dict[str, Any]:
        return {
            "total_days_tracked": len(self._daily_snapshots),
            "current_streak": self.streak(),
            "target_rate": DAILY_IMPROVEMENT_TARGET,
            "roi_summary": self.roi.summary(),
            "growth_projection": self.compound_growth_projection(30),
        }


# ---------------------------------------------------------------------------
# Self-Learning Orchestrator
# ---------------------------------------------------------------------------


class SelfLearningLoop:
    """Orchestrates the complete self-learning pipeline."""

    def __init__(self) -> None:
        self.scanner = ModelScanner()
        self.benchmark = BenchmarkPipeline()
        self.roi = ROITracker()
        self.metrics = CompoundingMetrics(self.roi)
        logger.info("SelfLearningLoop initialized — all subsystems active")

    async def daily_cycle(self) -> dict[str, Any]:
        """Run the daily self-learning cycle.

        1. Scan for new models
        2. Benchmark promising candidates
        3. Snapshot daily metrics
        4. Return summary
        """
        logger.info("Starting daily self-learning cycle")

        # 1. Scan
        discovered = await self.scanner.run_full_scan()
        logger.info(f"Scan phase: {len(discovered)} models found")

        # 2. Benchmark top candidates (by downloads/likes)
        top_candidates = sorted(
            discovered,
            key=lambda m: m.downloads + m.likes,
            reverse=True,
        )[:5]

        benchmarked = []
        for candidate in top_candidates:
            if candidate.source == ScanSource.HUGGINGFACE:
                # Only benchmark models we can actually reach
                results = await self.benchmark.run_full_benchmark(
                    candidate.name,
                    f"http://localhost:11434",  # Try via Ollama
                )
                avg_score = (
                    sum(r.score for r in results) / len(results) if results else 0
                )
                candidate.benchmark_score = round(avg_score, 3)
                candidate.benchmark_status = BenchmarkStatus.COMPLETED
                benchmarked.append(candidate.name)

        # 3. Daily snapshot
        daily = self.metrics.snapshot_day()

        summary = {
            "cycle_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "models_discovered": len(discovered),
            "models_benchmarked": len(benchmarked),
            "daily_metrics": daily.model_dump(),
            "leaderboard": self.benchmark.leaderboard()[:10],
            "roi": self.roi.summary(),
            "streak": self.metrics.streak(),
        }

        logger.info(
            f"Daily cycle complete: {len(discovered)} discovered, "
            f"{len(benchmarked)} benchmarked, streak={self.metrics.streak()}"
        )
        return summary

    def status(self) -> dict[str, Any]:
        return {
            "scanner": {
                "discovered_total": len(self.scanner.get_discovered()),
            },
            "benchmark": {
                "results_total": len(self.benchmark.get_results()),
                "leaderboard": self.benchmark.leaderboard()[:5],
            },
            "roi": self.roi.summary(),
            "metrics": self.metrics.summary(),
        }


# Singleton
learning = SelfLearningLoop()
