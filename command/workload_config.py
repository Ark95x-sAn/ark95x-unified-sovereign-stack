"""
ARK95X Workload Configuration - Agent Workload Assignment
Each AI agent gets its own dedicated workload pipeline.
Optimized for parallel execution across all 3 agents.
Network-95 LLC | 2026
"""

WORKLOAD_ASSIGNMENTS = {
    "manus": {
        "agent": "ManusAgent",
        "role": "executor",
        "mode": "autonomous",
        "description": "Autonomous execution - builds, deploys, ships",
        "primary_workload": [
            "code_generation",
            "repo_management",
            "docker_deploy",
            "file_operations",
            "database_ops",
        ],
        "secondary_workload": [
            "api_integration",
            "workflow_build",
            "test_suite",
            "system_audit",
            "documentation",
        ],
        "concurrency": 10,
        "max_queue_depth": 100,
        "retry_policy": {"max_retries": 3, "backoff_seconds": 2},
        "priority_boost": ["docker_deploy", "repo_management"],
        "resource_limits": {"cpu_percent": 40, "memory_mb": 2048},
    },
    "zencode": {
        "agent": "ZenCodeAgent",
        "role": "architect",
        "mode": "architect",
        "description": "Deep analysis - architecture, quality, security",
        "primary_workload": [
            "architecture_design",
            "code_review",
            "security_scan",
            "complexity_analysis",
            "refactor_engine",
        ],
        "secondary_workload": [
            "pattern_analysis",
            "dependency_audit",
            "api_design",
            "schema_generation",
            "performance_profile",
            "test_generation",
            "documentation_gen",
        ],
        "concurrency": 5,
        "max_queue_depth": 50,
        "retry_policy": {"max_retries": 2, "backoff_seconds": 5},
        "priority_boost": ["security_scan", "code_review"],
        "resource_limits": {"cpu_percent": 30, "memory_mb": 4096},
    },
    "vibecoder": {
        "agent": "VibeCoderAgent",
        "role": "creator",
        "mode": "creative",
        "description": "Creative intelligence - prototypes, UI, prompts",
        "primary_workload": [
            "nl_to_code",
            "ui_generation",
            "rapid_prototype",
            "creative_solve",
            "prompt_engineering",
        ],
        "secondary_workload": [
            "api_scaffold",
            "dashboard_builder",
            "workflow_designer",
            "code_remix",
            "data_visualization",
            "template_factory",
            "integration_weaver",
        ],
        "concurrency": 8,
        "max_queue_depth": 75,
        "retry_policy": {"max_retries": 2, "backoff_seconds": 1},
        "priority_boost": ["rapid_prototype", "nl_to_code"],
        "resource_limits": {"cpu_percent": 30, "memory_mb": 2048},
    },
}

ROUTING_RULES = {
    "code_generation": "manus",
    "repo_management": "manus",
    "docker_deploy": "manus",
    "api_integration": "manus",
    "database_ops": "manus",
    "system_audit": "manus",
    "workflow_build": "manus",
    "file_operations": "manus",
    "test_suite": "manus",
    "documentation": "manus",
    "architecture_design": "zencode",
    "code_review": "zencode",
    "pattern_analysis": "zencode",
    "dependency_audit": "zencode",
    "api_design": "zencode",
    "schema_generation": "zencode",
    "refactor_engine": "zencode",
    "performance_profile": "zencode",
    "security_scan": "zencode",
    "test_generation": "zencode",
    "documentation_gen": "zencode",
    "complexity_analysis": "zencode",
    "nl_to_code": "vibecoder",
    "ui_generation": "vibecoder",
    "rapid_prototype": "vibecoder",
    "api_scaffold": "vibecoder",
    "dashboard_builder": "vibecoder",
    "workflow_designer": "vibecoder",
    "creative_solve": "vibecoder",
    "code_remix": "vibecoder",
    "prompt_engineering": "vibecoder",
    "data_visualization": "vibecoder",
    "template_factory": "vibecoder",
    "integration_weaver": "vibecoder",
}

FURY_MODE_CONFIG = {
    "enabled": True,
    "max_parallel_agents": 3,
    "max_parallel_tasks_per_agent": 10,
    "timeout_seconds": 300,
    "multiplex_pipelines": True,
    "auto_retry": True,
    "load_balance": "round_robin",
    "health_check_interval": 30,
}

PROTOCOL_CONFIG = {
    "mcp": {"enabled": True, "transport": "stdio", "fallback": "sse"},
    "a2a": {"enabled": True, "transport": "http", "discovery": "agent_cards"},
    "acp": {"enabled": True, "transport": "rest", "mime_types": ["application/json"]},
}


def get_agent_for_skill(skill_name):
    return ROUTING_RULES.get(skill_name)


def get_workload(agent_name):
    return WORKLOAD_ASSIGNMENTS.get(agent_name)


def get_all_workloads():
    return {
        name: {
            "role": w["role"],
            "primary_skills": len(w["primary_workload"]),
            "secondary_skills": len(w["secondary_workload"]),
            "total_skills": len(w["primary_workload"]) + len(w["secondary_workload"]),
            "concurrency": w["concurrency"],
            "resource_limits": w["resource_limits"],
        }
        for name, w in WORKLOAD_ASSIGNMENTS.items()
    }
