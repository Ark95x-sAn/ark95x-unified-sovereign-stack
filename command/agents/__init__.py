"""
ARK95X Command Center - Agent Registry
Unified agent system with Manus, ZenCode, VibeCoder + all legacy agents.
Full skills, tools, protocols, and systems registry.
Network-95 LLC | Nordskog Properties LLC | 2026
"""
from .manus_agent import ManusAgent, ManusMode, ManusTask, TaskPriority
from .zencode_agent import ZenCodeAgent, ZenMode, CodeQuality
from .vibecoder_agent import VibeCoderAgent, VibeMode, OutputFormat

__all__ = [
    "ManusAgent", "ManusMode", "ManusTask", "TaskPriority",
    "ZenCodeAgent", "ZenMode", "CodeQuality",
    "VibeCoderAgent", "VibeMode", "OutputFormat",
    "AgentRegistry", "CommandCenter",
]


class AgentRegistry:
    """Central registry for all ARK95X agents."""

    AGENTS = {
        "manus": {"class": ManusAgent, "role": "executor", "desc": "Autonomous execution & build"},
        "zencode": {"class": ZenCodeAgent, "role": "architect", "desc": "Deep architecture & code quality"},
        "vibecoder": {"class": VibeCoderAgent, "role": "creator", "desc": "Creative intelligence & rapid prototyping"},
    }

    PROTOCOLS = {
        "mcp": {"name": "Model Context Protocol", "version": "1.0", "spec": "https://modelcontextprotocol.io"},
        "a2a": {"name": "Agent-to-Agent Protocol", "version": "1.0", "spec": "https://google.github.io/A2A"},
        "acp": {"name": "Agent Communication Protocol", "version": "0.2", "spec": "https://agentcommunicationprotocol.dev"},
    }

    SYSTEM_SKILLS = {
        "build": ["code_generation", "repo_management", "docker_deploy", "rapid_prototype", "api_scaffold", "template_factory"],
        "analyze": ["code_review", "pattern_analysis", "dependency_audit", "security_scan", "complexity_analysis", "performance_profile"],
        "create": ["nl_to_code", "ui_generation", "dashboard_builder", "workflow_designer", "creative_solve", "data_visualization"],
        "ops": ["system_audit", "database_ops", "file_operations", "workflow_build", "api_integration"],
        "quality": ["test_suite", "test_generation", "refactor_engine", "documentation", "documentation_gen", "schema_generation"],
    }

    SYSTEM_TOOLS = {
        "ast_parser": "Parse AST for any language",
        "dependency_graph": "Build dependency graphs",
        "metrics_calculator": "Calculate code metrics",
        "schema_validator": "Validate schemas against specs",
        "security_scanner": "Scan for vulnerabilities",
        "performance_profiler": "Profile execution paths",
        "template_engine": "Jinja2/Mustache template engine",
        "ui_kit": "Component library for UI generation",
        "code_transformer": "AST-based code transformation",
        "prompt_optimizer": "Optimize prompts for any LLM",
        "style_engine": "CSS/styling generation engine",
        "api_mocker": "Mock API generation for prototyping",
    }

    @classmethod
    def get_agent(cls, name, **kwargs):
        entry = cls.AGENTS.get(name)
        if not entry:
            raise ValueError(f"Unknown agent: {name}. Available: {list(cls.AGENTS.keys())}")
        return entry["class"](**kwargs)

    @classmethod
    def list_agents(cls):
        return {k: {"role": v["role"], "desc": v["desc"]} for k, v in cls.AGENTS.items()}

    @classmethod
    def list_all_skills(cls):
        return cls.SYSTEM_SKILLS

    @classmethod
    def list_all_tools(cls):
        return cls.SYSTEM_TOOLS

    @classmethod
    def list_protocols(cls):
        return cls.PROTOCOLS

    @classmethod
    def system_manifest(cls):
        return {
            "system": "ARK95X Command Center",
            "version": "3.0.0",
            "owner": "Network-95 LLC",
            "agents": cls.list_agents(),
            "total_skills": sum(len(v) for v in cls.SYSTEM_SKILLS.values()),
            "total_tools": len(cls.SYSTEM_TOOLS),
            "protocols": list(cls.PROTOCOLS.keys()),
            "skill_categories": list(cls.SYSTEM_SKILLS.keys()),
        }


class CommandCenter:
    """ARK95X Command Center - unified orchestration point."""

    def __init__(self):
        self.manus = ManusAgent(ManusMode.AUTONOMOUS)
        self.zencode = ZenCodeAgent(ZenMode.ARCHITECT)
        self.vibecoder = VibeCoderAgent(VibeMode.CREATIVE)
        self.registry = AgentRegistry()

    async def fury_deploy(self, tasks):
        """Full fury mode - all agents in parallel."""
        import asyncio
        manus_tasks = [t for t in tasks if t.get("agent") == "manus"]
        zen_tasks = [t for t in tasks if t.get("agent") == "zencode"]
        vibe_tasks = [t for t in tasks if t.get("agent") == "vibecoder"]
        results = await asyncio.gather(
            self.manus.fury_mode([ManusTask(t["id"], t["action"], t["target"], t.get("params", {})) for t in manus_tasks]) if manus_tasks else asyncio.sleep(0),
            *[self.zencode.analyze(t["target"], t.get("type", "full")) for t in zen_tasks],
            *[self.vibecoder.vibe_create(t["description"]) for t in vibe_tasks],
            return_exceptions=True,
        )
        return {"fury_deploy": "complete", "results_count": len(results)}

    def status(self):
        return {
            "command_center": "ARK95X",
            "version": "3.0.0",
            "agents": {
                "manus": self.manus.status(),
                "zencode": self.zencode.status(),
                "vibecoder": self.vibecoder.status(),
            },
            "manifest": self.registry.system_manifest(),
        }
