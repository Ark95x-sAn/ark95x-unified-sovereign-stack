"""ARK95X single control plane.

ARK-STATE.json remains the only authoritative state of truth. This package
coordinates specialist agents; it does not introduce a competing brain.
"""

from .control_plane import (
    APPROVAL_REQUIRED_ACTION_CLASSES,
    AUTHORITATIVE_STATE_PATH,
    CONTROL_PLANE_ID,
    DEFAULT_AGENT_SPECS,
    AgentRecord,
    ControlPlane,
    build_default_control_plane,
)

__all__ = [
    "APPROVAL_REQUIRED_ACTION_CLASSES",
    "AUTHORITATIVE_STATE_PATH",
    "CONTROL_PLANE_ID",
    "DEFAULT_AGENT_SPECS",
    "AgentRecord",
    "ControlPlane",
    "build_default_control_plane",
]
