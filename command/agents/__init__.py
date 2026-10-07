"""
ARK95X Command Center - Agent Registry
Unified agent system with Manus, ZenCode, VibeCoder + all legacy agents.
Full skills, tools, protocols, and systems registry.
Network-95 LLC | Nordskog Properties LLC | 2026
"""
import asyncio
from collections import Counter
import json
import math


# These helpers precede the agent imports so all three implementations use the
# same outcome contract. They classify reports; they do not validate receipts.
def _json_snapshot(value):
    """Copy plain JSON data within bounded depth, node, and serialized limits."""
    nodes = 0
    text_chars = 0

    def copy(item, depth):
        nonlocal nodes, text_chars
        nodes += 1
        if depth > 32 or nodes > 10000:
            raise ValueError("JSON nesting or item limit exceeded.")
        kind = type(item)
        if item is None or kind in (bool, int):
            return item
        if kind is float:
            if not math.isfinite(item):
                raise ValueError("JSON numbers must be finite.")
            return item
        if kind is str:
            text_chars += len(item)
            if text_chars > 1048576:
                raise ValueError("JSON text limit exceeded.")
            return item
        if kind is list:
            return [copy(child, depth + 1) for child in item]
        if kind is dict:
            result = {}
            for key, child in item.items():
                if type(key) is not str:
                    raise ValueError("JSON object keys must be strings.")
                result[copy(key, depth + 1)] = copy(child, depth + 1)
            return result
        raise ValueError(f"Unsupported JSON type: {kind.__name__}.")

    snapshot = copy(value, 0)
    if len(json.dumps(snapshot, allow_nan=False)) > 1048576:
        raise ValueError("Serialized JSON limit exceeded.")
    return snapshot


def _not_implemented(action, target):
    return {
        "status": "not_implemented", "action": action, "target": target,
        "executed": False, "verified": False,
        "reason": "No executor is implemented for this operation.",
    }


def _blocked(error):
    return {"status": "blocked", "executed": False, "verified": False,
            "error": error, "error_type": "invalid_request"}


def _failed(error, error_type, **details):
    # A handler may have produced effects before failing. Do not claim that it
    # did nothing, and do not retry it automatically.
    return {"status": "failed", "executed": None, "verified": False,
            "error": error, "error_type": error_type, **details}


def _normalize_outcome(result):
    """Retain a handler's output without promoting its claims to verification."""
    try:
        result = _json_snapshot(result)
    except (ValueError, TypeError, OverflowError) as exc:
        return _failed(f"Handler result is not bounded JSON data: {exc}",
                       "invalid_result", result_type=type(result).__name__)
    if not isinstance(result, dict):
        return _failed("Handler result must be a dictionary with a status.",
                       "invalid_result", result=result)
    reported_status = result.get("status")
    successes = {"success", "succeeded", "complete", "completed", "done", "ok", "reported"}
    aliases = {"error": "failed", "failure": "failed"}
    other_states = {"failed", "blocked", "not_implemented", "partial", "cancelled",
                    "pending", "queued", "running"}
    if (not isinstance(reported_status, str)
            or reported_status not in successes | other_states | aliases.keys()):
        return _failed("Handler result has a missing or unsupported status.",
                       "invalid_result", result=result)
    for flag in ("executed", "verified"):
        value = result.get(flag)
        if value is not None and not isinstance(value, bool):
            return _failed(f"Handler result {flag} must be a boolean or null.",
                           "invalid_result", result=result)
    for flag in ("success", "isError"):
        if flag in result and not isinstance(result[flag], bool):
            return _failed(f"Handler result {flag} must be a boolean.",
                           "invalid_result", result=result)
    if reported_status in successes and (result.get("error") or result.get("success") is False
                                        or result.get("isError") is True):
        return _failed("Handler reported success together with an error or failure flag.",
                       "invalid_result", result=result)
    if reported_status == "not_implemented" and result.get("executed") is True:
        return _failed("An unimplemented operation cannot report execution.",
                       "invalid_result", result=result)
    status = "reported" if reported_status in successes else aliases.get(reported_status, reported_status)
    outcome = {
        "status": status,
        "executed": False if result.get("executed") is False else None,
        "verified": False,
        "result": result,
    }
    for key in ("error", "error_type", "reason"):
        if key in result:
            outcome[key] = result[key]
    return outcome


async def _invoke_handler(handler, *args):
    try:
        return _normalize_outcome(await handler(*args))
    except Exception as exc:
        return _failed(str(exc), type(exc).__name__)


def _summarize_outcomes(results):
    counts = dict(Counter(result["status"] for result in results))
    if not results:
        status = "empty"
    elif all(result["status"] == "reported" for result in results):
        status = "reported"
    elif any(result["status"] in {"reported", "partial"} for result in results):
        status = "partial"
    elif any(result["status"] in {"failed", "cancelled"} for result in results):
        status = "failed"
    else:
        status = "blocked"
    return {
        "status": status,
        "executed": False if all(result["executed"] is False for result in results) else None,
        "verified": False,
        "results_count": len(results), "counts": counts, "results": results,
    }


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
        """Dispatch validated requests once and retain one outcome per input.

        Successful handler returns are reports, not verified completion. A
        cancelled parent call still propagates cancellation to its children.
        """
        if not isinstance(tasks, (list, tuple)):
            summary = _summarize_outcomes([])
            summary.update(_blocked("tasks must be a list or tuple of requests."))
            return {**summary, "fury_deploy": "blocked", "requested_count": None,
                    "dispatched_count": 0}

        records = []
        ready = []
        for index, task in enumerate(tasks):
            try:
                snapshot = _json_snapshot(task)
            except (ValueError, TypeError, OverflowError) as exc:
                records.append({"index": index, "task_id": None, "agent": None,
                                "input": None, "input_type": type(task).__name__,
                                **_blocked(f"Request is not bounded JSON data: {exc}")})
                continue
            record = {"index": index, "task_id": snapshot.get("id") if isinstance(snapshot, dict) else None,
                      "agent": snapshot.get("agent") if isinstance(snapshot, dict) else None,
                      "input": snapshot}
            error = self._validate_request(snapshot)
            if error:
                record.update(_blocked(error))
            else:
                # Keep a separate worker copy: a handler cannot rewrite the
                # caller's request or the retained input record through params.
                ready.append((index, _json_snapshot(snapshot)))
            records.append(record)

        # Duplicate explicit identifiers are ambiguous within one worker's
        # active-task table. Reject every occurrence before any dispatch starts.
        identities = Counter((task["agent"], task["id"]) for _, task in ready if "id" in task)
        dispatch = []
        for index, task in ready:
            if "id" in task and identities[(task["agent"], task["id"])] > 1:
                records[index].update(_blocked("Duplicate task id for this agent in the batch."))
            else:
                dispatch.append((index, task))

        returned = await asyncio.gather(
            *(self._dispatch_request(task) for _, task in dispatch), return_exceptions=True)
        for (index, task), result in zip(dispatch, returned):
            if isinstance(result, BaseException):
                outcome = _failed(str(result) or type(result).__name__, type(result).__name__)
            else:
                outcome = _normalize_outcome(result)
                snapshot = outcome.get("result")
                if (isinstance(snapshot, dict) and "task_id" in snapshot and "id" in task
                        and snapshot["task_id"] != task["id"]):
                    outcome = _failed("Handler result task_id does not match the request.",
                                      "invalid_result", result=snapshot)
            records[index].update(outcome)

        summary = _summarize_outcomes(records)
        return {**summary, "fury_deploy": summary["status"],
                "requested_count": len(tasks), "dispatched_count": len(dispatch)}

    @staticmethod
    def _validate_request(task):
        if not isinstance(task, dict):
            return "Each task must be a dictionary."
        agent = task.get("agent")
        if not isinstance(agent, str) or agent not in {"manus", "zencode", "vibecoder"}:
            return "Unknown or missing agent; expected manus, zencode, or vibecoder."
        if "id" in task and (not isinstance(task["id"], str) or not task["id"].strip()):
            return "Task id must be a nonempty string."
        required = {"manus": ("id", "action", "target"),
                    "zencode": ("target",), "vibecoder": ("description",)}[agent]
        for key in required:
            if not isinstance(task.get(key), str) or not task[key].strip():
                return f"{agent} requires a nonempty {key} string."
        if "params" in task and not isinstance(task["params"], dict):
            return "Task params must be a dictionary."
        if agent == "manus" and task["action"] not in ManusAgent.SKILLS:
            return f"Unknown Manus skill: {task['action']}"
        if agent == "zencode":
            analysis_type = task.get("type", "full")
            if (not isinstance(analysis_type, str)
                    or analysis_type not in {*ZenCodeAgent.SKILLS, "full"}):
                return "Unknown ZenCode analysis type."
        return None

    async def _dispatch_request(self, task):
        if task["agent"] == "manus":
            return await self.manus.execute(ManusTask(
                task["id"], task["action"], task["target"], task.get("params", {})))
        if task["agent"] == "zencode":
            return await self.zencode.analyze(task["target"], task.get("type", "full"))
        return await self.vibecoder.vibe_create(task["description"])

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
