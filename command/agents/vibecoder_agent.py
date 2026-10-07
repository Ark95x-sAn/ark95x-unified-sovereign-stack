"""
ARK95X VIBECODER AGENT - Creative Intelligence & Rapid Prototyping Engine
The soul of the system. Rapid prototyping, creative problem solving,
UI/UX generation, natural language to code, and vibe-driven development.
Part of ARK95X Command Center | Network-95 LLC
"""
import asyncio
import logging
from uuid import uuid4
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from . import _blocked, _invoke_handler, _not_implemented, _summarize_outcomes

logger = logging.getLogger("ark95x.vibecoder")


class VibeMode(Enum):
    CREATIVE = "creative"
    RAPID = "rapid"
    FLOW = "flow"
    EXPERIMENTAL = "experimental"
    PRODUCTION = "production"


class OutputFormat(Enum):
    CODE = "code"
    UI = "ui"
    API = "api"
    WORKFLOW = "workflow"
    DOCUMENT = "document"
    DASHBOARD = "dashboard"


@dataclass
class VibeSkill:
    name: str
    category: str
    description: str
    handler: str
    creativity_level: int = 5
    requires: list = field(default_factory=list)


@dataclass
class VibeProject:
    name: str
    description: str
    vibe: str
    output_format: OutputFormat
    components: List[str] = field(default_factory=list)
    status: str = "ideation"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class VibeCoderAgent:
    """Creative intelligence and rapid prototyping engine."""

    SKILLS = {
        "nl_to_code": VibeSkill("nl_to_code", "generation", "Natural language to production code", "_skill_nl_to_code", 8),
        "ui_generation": VibeSkill("ui_generation", "creative", "Generate UI components and layouts", "_skill_ui_gen", 9),
        "rapid_prototype": VibeSkill("rapid_prototype", "build", "Build working prototypes in minutes", "_skill_rapid_proto", 7),
        "api_scaffold": VibeSkill("api_scaffold", "build", "Scaffold complete API from description", "_skill_api_scaffold", 6),
        "dashboard_builder": VibeSkill("dashboard_builder", "creative", "Build monitoring dashboards", "_skill_dashboard", 8),
        "workflow_designer": VibeSkill("workflow_designer", "automation", "Design n8n/automation workflows", "_skill_workflow", 7),
        "creative_solve": VibeSkill("creative_solve", "intelligence", "Creative problem solving with lateral thinking", "_skill_creative_solve", 10),
        "code_remix": VibeSkill("code_remix", "generation", "Remix and improve existing code", "_skill_code_remix", 8),
        "prompt_engineering": VibeSkill("prompt_engineering", "intelligence", "Design optimized prompts for any model", "_skill_prompt_eng", 9),
        "data_visualization": VibeSkill("data_visualization", "creative", "Create data visualizations", "_skill_data_viz", 7),
        "template_factory": VibeSkill("template_factory", "build", "Generate project templates and boilerplate", "_skill_template", 5),
        "integration_weaver": VibeSkill("integration_weaver", "build", "Weave integrations between services", "_skill_integrate", 6),
    }

    PROTOCOLS = {
        "mcp": {"name": "Model Context Protocol", "version": "1.0", "role": "creative_tool"},
        "a2a": {"name": "Agent-to-Agent", "version": "1.0", "role": "creative_partner"},
        "acp": {"name": "Agent Communication Protocol", "version": "0.2", "role": "ideator"},
    }

    TOOLS = {
        "template_engine": {"type": "generation", "desc": "Jinja2/Mustache template engine"},
        "ui_kit": {"type": "creative", "desc": "Component library for UI generation"},
        "code_transformer": {"type": "transformation", "desc": "AST-based code transformation"},
        "prompt_optimizer": {"type": "intelligence", "desc": "Optimize prompts for any LLM"},
        "style_engine": {"type": "creative", "desc": "CSS/styling generation engine"},
        "api_mocker": {"type": "testing", "desc": "Mock API generation for prototyping"},
    }

    def __init__(self, mode=VibeMode.CREATIVE):
        self.mode = mode
        self.agent_id = f"vibecoder-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        self.projects = {}
        self.inspiration_bank = []
        self.metrics = {"prototypes_built": 0, "code_generated_lines": 0,
                        "creative_solutions": 0, "prototypes_reported": 0}
        logger.info(f"VibeCoderAgent initialized | mode={mode.value} | id={self.agent_id}")

    async def vibe_create(self, description, output_format=OutputFormat.CODE):
        if not isinstance(description, str) or not description.strip():
            return _blocked("Description must be a nonempty string.")
        if not isinstance(output_format, OutputFormat):
            return _blocked("Output format must be an OutputFormat value.")
        logger.info(f"VIBE CREATE | {description[:80]} | format={output_format.value}")
        project = VibeProject(
            name=f"vibe-{uuid4().hex}",
            description=description,
            vibe=self.mode.value,
            output_format=output_format,
        )
        self.projects[project.name] = project
        project.status = "running"
        try:
            outcome = await _invoke_handler(self._generate, project)
            project.status = outcome["status"]
            if project.status == "reported":
                self.metrics["prototypes_reported"] += 1
            return {**outcome, "project_id": project.name}
        except asyncio.CancelledError:
            project.status = "cancelled"
            raise

    async def rapid_build(self, specs):
        if not isinstance(specs, (list, tuple)):
            return _blocked("Specs must be a list or tuple of dictionaries.")
        self.mode = VibeMode.RAPID
        logger.info(f"RAPID BUILD | {len(specs)} components")
        results = []
        for spec in specs:
            if not isinstance(spec, dict):
                results.append(_blocked("Each spec must be a dictionary."))
                continue
            r = await self.vibe_create(spec.get("description", ""), spec.get("format", OutputFormat.CODE))
            results.append(r)
        return {**_summarize_outcomes(results), "mode": "rapid", "built": 0}

    async def flow_state(self, problem):
        if not isinstance(problem, str) or not problem.strip():
            return _blocked("Problem must be a nonempty string.")
        self.mode = VibeMode.FLOW
        logger.info(f"FLOW STATE | {problem[:100]}")
        creative = await _invoke_handler(self._skill_creative_solve, problem)
        prototype = await _invoke_handler(self._skill_rapid_proto, problem)
        return {**_summarize_outcomes([creative, prototype]), "mode": "flow",
                "creative_solution": creative, "prototype": prototype}

    async def _generate(self, project):
        handler_map = {
            OutputFormat.CODE: self._skill_nl_to_code,
            OutputFormat.UI: self._skill_ui_gen,
            OutputFormat.API: self._skill_api_scaffold,
            OutputFormat.WORKFLOW: self._skill_workflow,
            OutputFormat.DASHBOARD: self._skill_dashboard,
            OutputFormat.DOCUMENT: self._skill_nl_to_code,
        }
        handler = handler_map.get(project.output_format)
        if handler is None:
            return _blocked("Unknown output format.")
        return await handler(project.description)

    async def _skill_nl_to_code(self, target): return _not_implemented("nl_to_code", target)
    async def _skill_ui_gen(self, target): return _not_implemented("ui_generation", target)
    async def _skill_rapid_proto(self, target): return _not_implemented("rapid_prototype", target)
    async def _skill_api_scaffold(self, target): return _not_implemented("api_scaffold", target)
    async def _skill_dashboard(self, target): return _not_implemented("dashboard_builder", target)
    async def _skill_workflow(self, target): return _not_implemented("workflow_designer", target)
    async def _skill_creative_solve(self, target): return _not_implemented("creative_solve", target)
    async def _skill_code_remix(self, target): return _not_implemented("code_remix", target)
    async def _skill_prompt_eng(self, target): return _not_implemented("prompt_engineering", target)
    async def _skill_data_viz(self, target): return _not_implemented("data_visualization", target)
    async def _skill_template(self, target): return _not_implemented("template_factory", target)
    async def _skill_integrate(self, target): return _not_implemented("integration_weaver", target)

    def status(self):
        return {
            "agent_id": self.agent_id, "mode": self.mode.value,
            "active_projects": sum(project.status == "running" for project in self.projects.values()),
            "projects_recorded": len(self.projects),
            "metrics": self.metrics,
            "skills": list(self.SKILLS.keys()),
            "tools": list(self.TOOLS.keys()),
            "protocols": list(self.PROTOCOLS.keys()),
        }
