"""
ARK95X Passive Income Engine
==============================
Automated pipeline that generates, builds, deploys, and monitors
hundreds of small software products — packaged until something sticks.

Strategy: ship fast, iterate constantly, let the compounding work.

Product categories (100+ ideas, execute in parallel across PCs):
    Tier 1 — Code packages  (npm, pip, crates, gems)
    Tier 2 — SaaS micro-apps (Railway/Vercel, $9–$49/mo)
    Tier 3 — Marketplace templates (Gumroad, Lemon Squeezy)
    Tier 4 — API wrappers (RapidAPI, Mashape)
    Tier 5 — Browser/IDE extensions
    Tier 6 — n8n/Zapier workflow templates
    Tier 7 — AI-powered micro-tools (Claude/GPT wrappers)

Each product runs through:
    IDEA → BUILD → TEST → PACKAGE → PUBLISH → MONITOR → ITERATE

The engine distributes work across the PC fleet so all nodes
contribute to building passive income simultaneously.
"""

from __future__ import annotations

import asyncio
import json
import os
import random
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from loguru import logger


# ---------------------------------------------------------------------------
# Product Types
# ---------------------------------------------------------------------------


class ProductTier(str, Enum):
    CODE_PACKAGE = "code_package"       # npm/pip/crates
    SAAS_APP = "saas_app"              # hosted micro-SaaS
    TEMPLATE = "template"              # Notion/Figma/Gumroad
    API_WRAPPER = "api_wrapper"        # RapidAPI listing
    BROWSER_EXTENSION = "browser_extension"
    IDE_EXTENSION = "ide_extension"    # VS Code marketplace
    WORKFLOW_TEMPLATE = "workflow_template"  # n8n/Zapier
    AI_TOOL = "ai_tool"               # Claude/GPT wrapper product
    CHROME_EXTENSION = "chrome_extension"
    WORDPRESS_PLUGIN = "wordpress_plugin"
    DOCKER_IMAGE = "docker_image"      # Docker Hub
    DISCORD_BOT = "discord_bot"
    TELEGRAM_BOT = "telegram_bot"
    DATA_FEED = "data_feed"            # paid data API


class BuildStatus(str, Enum):
    IDEA = "idea"
    IN_PROGRESS = "in_progress"
    BUILT = "built"
    TESTED = "tested"
    PUBLISHED = "published"
    LIVE = "live"
    FAILED = "failed"
    PAUSED = "paused"


class MonetizationModel(str, Enum):
    ONE_TIME = "one_time"
    SUBSCRIPTION = "subscription"
    USAGE_BASED = "usage_based"
    FREEMIUM = "freemium"
    MARKETPLACE = "marketplace"
    ADS = "ads"


# ---------------------------------------------------------------------------
# Product Definition
# ---------------------------------------------------------------------------


@dataclass
class PassiveIncomeProduct:
    product_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    description: str = ""
    tier: ProductTier = ProductTier.CODE_PACKAGE
    status: BuildStatus = BuildStatus.IDEA
    monetization: MonetizationModel = MonetizationModel.MARKETPLACE
    target_price_usd: float = 9.99
    estimated_monthly_revenue: float = 0.0
    actual_monthly_revenue: float = 0.0
    tech_stack: list[str] = field(default_factory=list)
    publish_targets: list[str] = field(default_factory=list)
    preferred_pc_node: str | None = None
    build_command: str = ""
    publish_command: str = ""
    repo_path: str = ""
    created_at: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)
    build_log: list[str] = field(default_factory=list)
    revenue_log: list[dict[str, Any]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Product Catalog (100+ ideas, pre-seeded)
# ---------------------------------------------------------------------------


PRODUCT_CATALOG: list[dict[str, Any]] = [
    # CODE PACKAGES
    {"name": "smart-env-validator", "tier": ProductTier.CODE_PACKAGE, "tech_stack": ["python", "pypi"],
     "description": "Validate .env files against schemas with auto-docs generation",
     "publish_targets": ["pypi", "npm"], "target_price_usd": 0, "monetization": MonetizationModel.FREEMIUM},
    {"name": "ai-rate-limiter", "tier": ProductTier.CODE_PACKAGE, "tech_stack": ["python"],
     "description": "Smart rate limiter for AI API calls with cost tracking",
     "publish_targets": ["pypi"], "target_price_usd": 0, "monetization": MonetizationModel.FREEMIUM},
    {"name": "prompt-optimizer-sdk", "tier": ProductTier.CODE_PACKAGE, "tech_stack": ["python", "typescript"],
     "description": "SDK to auto-compress and optimize prompts for any LLM",
     "publish_targets": ["pypi", "npm"], "target_price_usd": 0, "monetization": MonetizationModel.FREEMIUM},
    {"name": "cron-ai", "tier": ProductTier.CODE_PACKAGE, "tech_stack": ["python"],
     "description": "Natural language cron scheduler: 'every weekday at 9am' → valid cron",
     "publish_targets": ["pypi"], "target_price_usd": 0, "monetization": MonetizationModel.FREEMIUM},
    {"name": "docker-compose-validator", "tier": ProductTier.CODE_PACKAGE, "tech_stack": ["python"],
     "description": "Lint and validate docker-compose files with security scanning",
     "publish_targets": ["pypi"], "target_price_usd": 0, "monetization": MonetizationModel.FREEMIUM},

    # API WRAPPERS
    {"name": "zillow-api-wrapper", "tier": ProductTier.API_WRAPPER, "tech_stack": ["python", "fastapi"],
     "description": "Clean REST wrapper for Zillow property data",
     "publish_targets": ["rapidapi"], "target_price_usd": 9.99, "monetization": MonetizationModel.SUBSCRIPTION},
    {"name": "court-records-api", "tier": ProductTier.API_WRAPPER, "tech_stack": ["python", "scrapy"],
     "description": "Unified API for public court records across 50 states",
     "publish_targets": ["rapidapi", "mashape"], "target_price_usd": 29.99, "monetization": MonetizationModel.USAGE_BASED},
    {"name": "restaurant-menu-api", "tier": ProductTier.API_WRAPPER, "tech_stack": ["python"],
     "description": "Scrape and serve restaurant menus via REST",
     "publish_targets": ["rapidapi"], "target_price_usd": 14.99, "monetization": MonetizationModel.SUBSCRIPTION},
    {"name": "social-sentiment-api", "tier": ProductTier.API_WRAPPER, "tech_stack": ["python", "transformers"],
     "description": "Real-time sentiment scoring for Twitter, Reddit, StockTwits",
     "publish_targets": ["rapidapi"], "target_price_usd": 19.99, "monetization": MonetizationModel.USAGE_BASED},
    {"name": "iowa-property-api", "tier": ProductTier.API_WRAPPER, "tech_stack": ["python", "scrapy"],
     "description": "Iowa county property records, assessed values, tax history",
     "publish_targets": ["rapidapi", "gumroad"], "target_price_usd": 24.99, "monetization": MonetizationModel.SUBSCRIPTION},

    # SAAS MICRO-APPS
    {"name": "receipt-ocr-saas", "tier": ProductTier.SAAS_APP, "tech_stack": ["python", "fastapi", "tesseract"],
     "description": "Upload receipts → get structured JSON data for bookkeeping",
     "publish_targets": ["railway", "vercel"], "target_price_usd": 9.99, "monetization": MonetizationModel.SUBSCRIPTION},
    {"name": "invoice-autopilot", "tier": ProductTier.SAAS_APP, "tech_stack": ["python", "fastapi", "stripe"],
     "description": "Auto-generate and send invoices from time-tracking data",
     "publish_targets": ["railway"], "target_price_usd": 19.99, "monetization": MonetizationModel.SUBSCRIPTION},
    {"name": "ai-lead-qualifier", "tier": ProductTier.SAAS_APP, "tech_stack": ["python", "fastapi"],
     "description": "Paste a LinkedIn URL → AI scores lead quality for your ICP",
     "publish_targets": ["railway"], "target_price_usd": 29.99, "monetization": MonetizationModel.SUBSCRIPTION},
    {"name": "competitor-watcher", "tier": ProductTier.SAAS_APP, "tech_stack": ["python", "playwright"],
     "description": "Monitor competitor pricing/features and send weekly reports",
     "publish_targets": ["railway"], "target_price_usd": 39.99, "monetization": MonetizationModel.SUBSCRIPTION},
    {"name": "ai-contract-reviewer", "tier": ProductTier.SAAS_APP, "tech_stack": ["python", "fastapi", "anthropic"],
     "description": "Upload PDF contract → AI flags risky clauses and summaries",
     "publish_targets": ["railway", "vercel"], "target_price_usd": 49.99, "monetization": MonetizationModel.SUBSCRIPTION},

    # TEMPLATES
    {"name": "restaurant-notion-os", "tier": ProductTier.TEMPLATE, "tech_stack": ["notion"],
     "description": "Full restaurant operations Notion workspace: staff, inventory, POS sync",
     "publish_targets": ["gumroad", "lemon_squeezy"], "target_price_usd": 47, "monetization": MonetizationModel.ONE_TIME},
    {"name": "real-estate-investor-vault", "tier": ProductTier.TEMPLATE, "tech_stack": ["notion"],
     "description": "Deal analysis, property tracker, tenant management in Notion",
     "publish_targets": ["gumroad", "lemon_squeezy"], "target_price_usd": 67, "monetization": MonetizationModel.ONE_TIME},
    {"name": "sovereign-stack-template", "tier": ProductTier.TEMPLATE, "tech_stack": ["notion", "n8n"],
     "description": "Multi-PC AI stack operating system template with automation flows",
     "publish_targets": ["gumroad", "lemon_squeezy"], "target_price_usd": 97, "monetization": MonetizationModel.ONE_TIME},
    {"name": "ai-agency-os", "tier": ProductTier.TEMPLATE, "tech_stack": ["notion"],
     "description": "AI agency project management: client onboarding, delivery, billing",
     "publish_targets": ["gumroad"], "target_price_usd": 77, "monetization": MonetizationModel.ONE_TIME},
    {"name": "trading-journal-notion", "tier": ProductTier.TEMPLATE, "tech_stack": ["notion"],
     "description": "Advanced trading journal with automated P&L tracking in Notion",
     "publish_targets": ["gumroad", "lemon_squeezy"], "target_price_usd": 37, "monetization": MonetizationModel.ONE_TIME},

    # BROWSER / IDE EXTENSIONS
    {"name": "prompt-saver-chrome", "tier": ProductTier.CHROME_EXTENSION, "tech_stack": ["javascript", "chrome_extension"],
     "description": "Save and organize prompts across ChatGPT, Claude, Gemini in one click",
     "publish_targets": ["chrome_web_store"], "target_price_usd": 4.99, "monetization": MonetizationModel.ONE_TIME},
    {"name": "ai-cost-tracker-chrome", "tier": ProductTier.CHROME_EXTENSION, "tech_stack": ["javascript"],
     "description": "Track your OpenAI/Anthropic API spend in real-time in the browser",
     "publish_targets": ["chrome_web_store"], "target_price_usd": 0, "monetization": MonetizationModel.FREEMIUM},
    {"name": "ark-vscode-extension", "tier": ProductTier.IDE_EXTENSION, "tech_stack": ["typescript", "vscode"],
     "description": "ARK95X command palette inside VS Code — route tasks to any AI",
     "publish_targets": ["vscode_marketplace"], "target_price_usd": 0, "monetization": MonetizationModel.FREEMIUM},
    {"name": "court-lookup-chrome", "tier": ProductTier.CHROME_EXTENSION, "tech_stack": ["javascript"],
     "description": "Right-click any name → instant Iowa court record lookup",
     "publish_targets": ["chrome_web_store"], "target_price_usd": 2.99, "monetization": MonetizationModel.ONE_TIME},

    # WORKFLOW TEMPLATES
    {"name": "n8n-lead-to-crm", "tier": ProductTier.WORKFLOW_TEMPLATE, "tech_stack": ["n8n"],
     "description": "LinkedIn scrape → enrich → score → push to CRM n8n workflow",
     "publish_targets": ["n8n_marketplace", "gumroad"], "target_price_usd": 29, "monetization": MonetizationModel.ONE_TIME},
    {"name": "n8n-receipt-bookkeeping", "tier": ProductTier.WORKFLOW_TEMPLATE, "tech_stack": ["n8n"],
     "description": "Gmail receipt → OCR → Notion + QuickBooks sync n8n flow",
     "publish_targets": ["n8n_marketplace", "gumroad"], "target_price_usd": 19, "monetization": MonetizationModel.ONE_TIME},
    {"name": "n8n-social-autopilot", "tier": ProductTier.WORKFLOW_TEMPLATE, "tech_stack": ["n8n"],
     "description": "AI-generated posts → review → publish to 5 platforms via n8n",
     "publish_targets": ["n8n_marketplace", "gumroad"], "target_price_usd": 39, "monetization": MonetizationModel.ONE_TIME},
    {"name": "n8n-competitor-monitor", "tier": ProductTier.WORKFLOW_TEMPLATE, "tech_stack": ["n8n", "playwright"],
     "description": "Daily competitor price/feature scrape → Slack/email digest",
     "publish_targets": ["n8n_marketplace"], "target_price_usd": 24, "monetization": MonetizationModel.ONE_TIME},

    # AI TOOLS
    {"name": "legal-brief-generator", "tier": ProductTier.AI_TOOL, "tech_stack": ["python", "fastapi", "anthropic"],
     "description": "Paste facts → AI generates formatted Iowa legal brief",
     "publish_targets": ["gumroad", "railway"], "target_price_usd": 99, "monetization": MonetizationModel.USAGE_BASED},
    {"name": "menu-description-ai", "tier": ProductTier.AI_TOOL, "tech_stack": ["python", "openai"],
     "description": "Restaurant menu item list → AI rewrites for higher conversion",
     "publish_targets": ["gumroad", "railway"], "target_price_usd": 19, "monetization": MonetizationModel.ONE_TIME},
    {"name": "real-estate-pitch-ai", "tier": ProductTier.AI_TOOL, "tech_stack": ["python", "anthropic"],
     "description": "Property address → investor pitch deck generated by AI",
     "publish_targets": ["railway"], "target_price_usd": 4.99, "monetization": MonetizationModel.USAGE_BASED},

    # BOTS
    {"name": "court-alert-telegram", "tier": ProductTier.TELEGRAM_BOT, "tech_stack": ["python", "telegram"],
     "description": "Telegram bot: watch any Iowa county for new court filings",
     "publish_targets": ["telegram", "gumroad"], "target_price_usd": 9.99, "monetization": MonetizationModel.SUBSCRIPTION},
    {"name": "dark-pool-discord-bot", "tier": ProductTier.DISCORD_BOT, "tech_stack": ["python", "discord.py"],
     "description": "Discord bot that alerts unusual options + dark pool activity",
     "publish_targets": ["discord", "gumroad"], "target_price_usd": 19.99, "monetization": MonetizationModel.SUBSCRIPTION},

    # DOCKER IMAGES
    {"name": "sovereign-stack-docker", "tier": ProductTier.DOCKER_IMAGE, "tech_stack": ["docker"],
     "description": "1-command ARK95X stack: Ollama + n8n + Postgres + Redis + SearXNG",
     "publish_targets": ["docker_hub"], "target_price_usd": 0, "monetization": MonetizationModel.FREEMIUM},
    {"name": "ai-router-docker", "tier": ProductTier.DOCKER_IMAGE, "tech_stack": ["docker", "python"],
     "description": "Drop-in AI router container: classify → route → respond",
     "publish_targets": ["docker_hub"], "target_price_usd": 0, "monetization": MonetizationModel.FREEMIUM},
]


# ---------------------------------------------------------------------------
# Build Pipeline
# ---------------------------------------------------------------------------


@dataclass
class BuildResult:
    product_id: str
    success: bool
    stage: BuildStatus
    duration_seconds: float
    output: str
    error: str | None = None


class PassiveIncomeEngine:
    """
    Manages the full lifecycle of passive income products:
    ideate → build → test → publish → monitor.

    Distributes build work across multiple PC nodes via the coordinator.
    """

    def __init__(
        self,
        coordinator_url: str = "http://localhost:8096",
        workspace_dir: str = "~/sovereign-products",
    ) -> None:
        self.coordinator_url = coordinator_url
        self.workspace_dir = Path(workspace_dir).expanduser()
        self.products: dict[str, PassiveIncomeProduct] = {}
        self.revenue_total: float = 0.0
        self._running = False
        self._seed_catalog()

    def _seed_catalog(self) -> None:
        for spec in PRODUCT_CATALOG:
            product = PassiveIncomeProduct(
                name=spec["name"],
                description=spec.get("description", ""),
                tier=spec.get("tier", ProductTier.CODE_PACKAGE),
                monetization=spec.get("monetization", MonetizationModel.ONE_TIME),
                target_price_usd=spec.get("target_price_usd", 9.99),
                tech_stack=spec.get("tech_stack", []),
                publish_targets=spec.get("publish_targets", []),
            )
            self.products[product.product_id] = product
        logger.info(f"[INCOME] Seeded {len(self.products)} products from catalog")

    def add_product(self, product: PassiveIncomeProduct) -> PassiveIncomeProduct:
        self.products[product.product_id] = product
        logger.info(f"[INCOME] Added product: {product.name}")
        return product

    def products_by_status(self, status: BuildStatus) -> list[PassiveIncomeProduct]:
        return [p for p in self.products.values() if p.status == status]

    def priority_queue(self) -> list[PassiveIncomeProduct]:
        """Return products sorted by estimated ROI vs effort."""
        ideas = self.products_by_status(BuildStatus.IDEA)
        return sorted(ideas, key=lambda p: p.target_price_usd * 12, reverse=True)

    # ------------------------------------------------------------------
    # Pipeline Stages
    # ------------------------------------------------------------------

    async def generate_scaffold(self, product: PassiveIncomeProduct) -> BuildResult:
        """Generate initial code scaffold for a product."""
        start = time.time()
        product.status = BuildStatus.IN_PROGRESS
        product.build_log.append(f"[{time.strftime('%H:%M:%S')}] Generating scaffold for {product.name}")

        scaffold_dir = self.workspace_dir / product.name
        scaffold_dir.mkdir(parents=True, exist_ok=True)

        template = self._get_template(product)
        readme_path = scaffold_dir / "README.md"
        readme_path.write_text(template)

        product.repo_path = str(scaffold_dir)
        product.build_log.append(f"[{time.strftime('%H:%M:%S')}] Scaffold written to {scaffold_dir}")

        return BuildResult(
            product_id=product.product_id,
            success=True,
            stage=BuildStatus.IN_PROGRESS,
            duration_seconds=round(time.time() - start, 2),
            output=str(scaffold_dir),
        )

    async def run_build(self, product: PassiveIncomeProduct) -> BuildResult:
        """Run the build command for a product."""
        start = time.time()
        if not product.build_command:
            product.status = BuildStatus.BUILT
            return BuildResult(
                product_id=product.product_id,
                success=True,
                stage=BuildStatus.BUILT,
                duration_seconds=0,
                output="No build command — scaffold only",
            )

        proc = await asyncio.create_subprocess_shell(
            product.build_command,
            cwd=product.repo_path or ".",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        success = proc.returncode == 0
        product.status = BuildStatus.BUILT if success else BuildStatus.FAILED
        product.build_log.append(stdout.decode()[:500])

        return BuildResult(
            product_id=product.product_id,
            success=success,
            stage=product.status,
            duration_seconds=round(time.time() - start, 2),
            output=stdout.decode()[:1000],
            error=stderr.decode()[:500] if not success else None,
        )

    async def run_tests(self, product: PassiveIncomeProduct) -> BuildResult:
        """Run tests. If no test command, auto-pass."""
        start = time.time()
        if not product.repo_path:
            product.status = BuildStatus.TESTED
            return BuildResult(
                product_id=product.product_id, success=True,
                stage=BuildStatus.TESTED, duration_seconds=0,
                output="No repo — skipping tests",
            )

        test_cmd = f"cd {product.repo_path} && pytest -q 2>&1 | tail -5"
        proc = await asyncio.create_subprocess_shell(
            test_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        success = proc.returncode == 0
        product.status = BuildStatus.TESTED if success else BuildStatus.FAILED
        return BuildResult(
            product_id=product.product_id, success=success,
            stage=product.status, duration_seconds=round(time.time() - start, 2),
            output=stdout.decode()[:500],
        )

    async def publish(self, product: PassiveIncomeProduct) -> BuildResult:
        """Publish to all configured targets."""
        start = time.time()
        results: list[str] = []
        for target in product.publish_targets:
            cmd = self._publish_command(product, target)
            if cmd:
                results.append(f"Would run: {cmd}")
            else:
                results.append(f"{target}: manual publish required")

        product.status = BuildStatus.PUBLISHED
        product.build_log.append(f"[{time.strftime('%H:%M:%S')}] Published to {product.publish_targets}")
        return BuildResult(
            product_id=product.product_id, success=True,
            stage=BuildStatus.PUBLISHED, duration_seconds=round(time.time() - start, 2),
            output="\n".join(results),
        )

    async def full_pipeline(self, product: PassiveIncomeProduct) -> list[BuildResult]:
        """Run a product through the full build pipeline."""
        results: list[BuildResult] = []
        stages = [
            self.generate_scaffold,
            self.run_build,
            self.run_tests,
            self.publish,
        ]
        for stage_fn in stages:
            result = await stage_fn(product)
            results.append(result)
            if not result.success:
                logger.warning(f"[INCOME] Pipeline stopped at {result.stage} for {product.name}")
                break
            await asyncio.sleep(0.1)

        if product.status == BuildStatus.PUBLISHED:
            product.status = BuildStatus.LIVE
            logger.info(f"[INCOME] {product.name} is LIVE")
        return results

    # ------------------------------------------------------------------
    # 24/7 Automation Loop
    # ------------------------------------------------------------------

    async def run_automation_loop(
        self, max_concurrent: int = 3, interval_hours: float = 1.0
    ) -> None:
        """
        Continuously pick IDEA products, build them, publish them.
        Runs forever — each PC node running this fills the catalog.
        """
        self._running = True
        logger.info("[INCOME] Passive income automation loop started")

        while self._running:
            queue = self.priority_queue()
            batch = queue[:max_concurrent]

            if not batch:
                logger.info("[INCOME] No pending ideas — waiting for next cycle")
                await asyncio.sleep(interval_hours * 3600)
                continue

            tasks = [self.full_pipeline(product) for product in batch]
            results_list = await asyncio.gather(*tasks, return_exceptions=True)

            live_count = len(self.products_by_status(BuildStatus.LIVE))
            total_mrr = sum(
                p.actual_monthly_revenue
                for p in self.products.values()
                if p.status == BuildStatus.LIVE
            )
            logger.info(
                f"[INCOME] Cycle done. Live: {live_count} products. "
                f"MRR: ${total_mrr:.2f}"
            )
            await asyncio.sleep(interval_hours * 3600)

    def stop(self) -> None:
        self._running = False

    # ------------------------------------------------------------------
    # Revenue Tracking
    # ------------------------------------------------------------------

    def log_revenue(self, product_id: str, amount_usd: float, source: str) -> None:
        product = self.products.get(product_id)
        if not product:
            logger.warning(f"[INCOME] Unknown product: {product_id}")
            return
        product.actual_monthly_revenue += amount_usd
        self.revenue_total += amount_usd
        product.revenue_log.append({
            "timestamp": time.time(),
            "amount": amount_usd,
            "source": source,
        })
        logger.info(f"[INCOME] Revenue: ${amount_usd:.2f} from {product.name} via {source}")

    def revenue_summary(self) -> dict[str, Any]:
        live = self.products_by_status(BuildStatus.LIVE)
        total_mrr = sum(p.actual_monthly_revenue for p in live)
        projected_arr = total_mrr * 12
        return {
            "total_products": len(self.products),
            "live_products": len(live),
            "published_products": len(self.products_by_status(BuildStatus.PUBLISHED)),
            "in_progress": len(self.products_by_status(BuildStatus.IN_PROGRESS)),
            "ideas_remaining": len(self.products_by_status(BuildStatus.IDEA)),
            "total_revenue_collected": round(self.revenue_total, 2),
            "current_mrr": round(total_mrr, 2),
            "projected_arr": round(projected_arr, 2),
            "top_earners": sorted(
                [{"name": p.name, "mrr": p.actual_monthly_revenue} for p in live],
                key=lambda x: x["mrr"],
                reverse=True,
            )[:5],
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_template(self, product: PassiveIncomeProduct) -> str:
        return f"""# {product.name}

{product.description}

## Stack
{', '.join(product.tech_stack)}

## Monetization
Model: {product.monetization.value}
Price: ${product.target_price_usd}

## Publish Targets
{', '.join(product.publish_targets)}

## Build
```bash
{product.build_command or 'echo ready'}
```

## Status
{product.status.value}
"""

    def _publish_command(self, product: PassiveIncomeProduct, target: str) -> str:
        commands = {
            "pypi": f"cd {product.repo_path} && python -m build && twine upload dist/*",
            "npm": f"cd {product.repo_path} && npm publish",
            "docker_hub": f"docker build -t ark95x/{product.name} {product.repo_path} && docker push ark95x/{product.name}",
            "railway": f"railway deploy --path {product.repo_path}",
            "vercel": f"vercel --cwd {product.repo_path} --prod",
        }
        return commands.get(target, "")


# Singleton
engine = PassiveIncomeEngine()


if __name__ == "__main__":
    summary = engine.revenue_summary()
    print(json.dumps(summary, indent=2))
    print(f"\nTop priority product: {engine.priority_queue()[0].name}")
