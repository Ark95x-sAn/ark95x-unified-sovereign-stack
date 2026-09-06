"""
ARK95X Device Mesh
==================
Maps 9 physical devices to their operational roles and handles context
handoff preparation across the sovereign device fleet. This registry does
not implement a transport or authenticate physical devices.

Each device has:
    - id, name, roles[], status (online/offline/standby)
    - primary_model_access[] — which models this device can reach
    - failover_to — fallback device if this one goes offline
    - sync_bridges[] — how this device syncs with others
"""

from __future__ import annotations

import math
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from loguru import logger
from pydantic import BaseModel, Field, PrivateAttr


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class DeviceStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    STANDBY = "standby"


class SyncProtocol(str, Enum):
    ONEDRIVE = "onedrive"
    ICLOUD = "icloud"
    GITHUB = "github"
    BLUETOOTH = "bluetooth"
    USB = "usb"
    LOCAL_NETWORK = "local_network"
    TAILSCALE = "tailscale"
    AIRDROP = "airdrop"
    NEARBY_SHARE = "nearby_share"
    CLOUD_SYNC = "cloud_sync"


# ---------------------------------------------------------------------------
# Device Definition
# ---------------------------------------------------------------------------


class DeviceNode(BaseModel):
    """A single device in the ARK95X sovereign mesh."""

    id: str
    name: str
    platform: str
    roles: list[str]
    status: DeviceStatus = DeviceStatus.STANDBY
    primary_model_access: list[str] = Field(
        default_factory=list,
        description="Model IDs this device can directly access",
    )
    failover_to: str | None = Field(
        None, description="Device ID to failover to if offline"
    )
    sync_bridges: list[SyncProtocol] = Field(
        default_factory=list,
        description="Synchronization protocols available",
    )
    capabilities: dict[str, Any] = Field(
        default_factory=dict,
        description="Hardware/software capabilities",
    )
    last_seen: str | None = None
    active_context: str | None = Field(
        None, description="Current task/context running on this device"
    )
    _heartbeat_observed_at: float | None = PrivateAttr(default=None)

    def heartbeat(self) -> None:
        """Record a signal observed locally, not authenticated device proof.

        A receiver must call this after observing a heartbeat. Configuration,
        status changes and prepared handoffs must not manufacture this signal.
        The monotonic observation is deliberately absent from serialized data.
        """
        self.last_seen = datetime.now(timezone.utc).isoformat()
        self._heartbeat_observed_at = time.monotonic()
        self.status = DeviceStatus.ONLINE

    def has_recent_heartbeat(self, timeout_seconds: float) -> bool:
        """Check freshness of this process's local heartbeat observation."""
        if self._heartbeat_observed_at is None:
            return False
        age = time.monotonic() - self._heartbeat_observed_at
        return 0 <= age <= timeout_seconds


class ContextHandoff(BaseModel):
    """A prepared transfer request; it is not a delivery receipt."""

    source_device: str
    target_device: str
    context_payload: str
    task_id: str | None = None
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    sync_protocol: SyncProtocol | None = None
    status: str = "pending"


# ---------------------------------------------------------------------------
# Device Fleet Registry
# ---------------------------------------------------------------------------

DEVICE_FLEET: dict[str, DeviceNode] = {
    "pc_win11": DeviceNode(
        id="pc_win11",
        name="PC Win11 Pro",
        platform="windows_11_pro",
        roles=["primary_command", "docker_host", "ollama_gpu", "development"],
        status=DeviceStatus.STANDBY,
        primary_model_access=[
            "claude_pro", "chatgpt_pro", "codex", "grok_xai",
            "perplexity_comet", "ollama_llama3", "ollama_deepseek",
            "ollama_codellama", "ollama_mistral", "ollama_phi",
            "gpt4all", "copilot", "crewai", "n8n", "searxng",
            "prometheus_grafana", "docker_conductor",
        ],
        failover_to="surface_pro",
        sync_bridges=[
            SyncProtocol.ONEDRIVE, SyncProtocol.GITHUB,
            SyncProtocol.LOCAL_NETWORK, SyncProtocol.TAILSCALE,
        ],
        capabilities={
            "gpu": "nvidia_rtx",
            "ram_gb": 32,
            "docker": True,
            "ollama": True,
            "wsl2": True,
            "vscode": True,
        },
    ),
    "surface_pro": DeviceNode(
        id="surface_pro",
        name="Surface Pro",
        platform="windows_11",
        roles=["mobile_command", "field_ops", "client_meetings"],
        status=DeviceStatus.STANDBY,
        primary_model_access=[
            "claude_pro", "chatgpt_pro", "grok_xai",
            "perplexity_comet", "copilot",
        ],
        failover_to="pc_win11",
        sync_bridges=[
            SyncProtocol.ONEDRIVE, SyncProtocol.GITHUB,
            SyncProtocol.TAILSCALE, SyncProtocol.BLUETOOTH,
        ],
        capabilities={
            "gpu": "integrated",
            "ram_gb": 16,
            "touch_screen": True,
            "pen_support": True,
            "portable": True,
        },
    ),
    "ms_tablet": DeviceNode(
        id="ms_tablet",
        name="Microsoft Tablet",
        platform="windows_11",
        roles=["monitoring", "dashboards", "secondary_display"],
        status=DeviceStatus.STANDBY,
        primary_model_access=[
            "chatgpt_pro", "claude_pro", "prometheus_grafana",
        ],
        failover_to="surface_pro",
        sync_bridges=[
            SyncProtocol.ONEDRIVE, SyncProtocol.LOCAL_NETWORK,
            SyncProtocol.BLUETOOTH,
        ],
        capabilities={
            "touch_screen": True,
            "portable": True,
            "display_mode": "dashboard",
        },
    ),
    "iphone_12": DeviceNode(
        id="iphone_12",
        name="iPhone 12",
        platform="ios",
        roles=["communication", "2fa", "notifications", "quick_capture"],
        status=DeviceStatus.STANDBY,
        primary_model_access=[
            "chatgpt_pro", "claude_pro", "perplexity_comet",
        ],
        failover_to="samsung_s20",
        sync_bridges=[
            SyncProtocol.ICLOUD, SyncProtocol.AIRDROP,
            SyncProtocol.BLUETOOTH,
        ],
        capabilities={
            "camera": True,
            "biometric": "face_id",
            "cellular": True,
            "nfc": True,
        },
    ),
    "samsung_s20": DeviceNode(
        id="samsung_s20",
        name="Samsung S20",
        platform="android",
        roles=["android_ops", "backup_comms", "testing"],
        status=DeviceStatus.STANDBY,
        primary_model_access=[
            "chatgpt_pro", "claude_pro", "perplexity_comet",
        ],
        failover_to="iphone_12",
        sync_bridges=[
            SyncProtocol.NEARBY_SHARE, SyncProtocol.BLUETOOTH,
            SyncProtocol.CLOUD_SYNC,
        ],
        capabilities={
            "camera": True,
            "biometric": "fingerprint",
            "cellular": True,
            "dex_mode": True,
        },
    ),
    "ipad_1": DeviceNode(
        id="ipad_1",
        name="iPad 1",
        platform="ipados",
        roles=["content_creation", "design", "reading", "annotation"],
        status=DeviceStatus.STANDBY,
        primary_model_access=[
            "chatgpt_pro", "claude_pro", "perplexity_comet",
        ],
        failover_to="ipad_2",
        sync_bridges=[
            SyncProtocol.ICLOUD, SyncProtocol.AIRDROP,
            SyncProtocol.BLUETOOTH,
        ],
        capabilities={
            "apple_pencil": True,
            "touch_screen": True,
            "split_view": True,
            "procreate": True,
        },
    ),
    "ipad_2": DeviceNode(
        id="ipad_2",
        name="iPad 2",
        platform="ipados",
        roles=["pos_terminal", "square_shell", "restaurant_ops"],
        status=DeviceStatus.STANDBY,
        primary_model_access=[
            "chatgpt_pro", "claude_pro",
        ],
        failover_to="ipad_1",
        sync_bridges=[
            SyncProtocol.ICLOUD, SyncProtocol.AIRDROP,
            SyncProtocol.LOCAL_NETWORK,
        ],
        capabilities={
            "touch_screen": True,
            "square_pos": True,
            "kiosk_mode": True,
            "receipt_printer": True,
        },
    ),
    "xbox_series_x": DeviceNode(
        id="xbox_series_x",
        name="Xbox Series X",
        platform="xbox_os",
        roles=["recovery", "inspiration", "strategic_gaming"],
        status=DeviceStatus.STANDBY,
        primary_model_access=[],
        failover_to=None,
        sync_bridges=[
            SyncProtocol.LOCAL_NETWORK, SyncProtocol.CLOUD_SYNC,
        ],
        capabilities={
            "gpu": "rdna2_custom",
            "media_playback": True,
            "game_pass": True,
            "streaming": True,
        },
    ),
    "quest_3": DeviceNode(
        id="quest_3",
        name="Quest 3",
        platform="meta_quest_os",
        roles=["vr_workspace", "immersive_viz", "spatial_computing"],
        status=DeviceStatus.STANDBY,
        primary_model_access=[],
        failover_to=None,
        sync_bridges=[
            SyncProtocol.LOCAL_NETWORK, SyncProtocol.USB,
            SyncProtocol.BLUETOOTH,
        ],
        capabilities={
            "vr": True,
            "mixed_reality": True,
            "hand_tracking": True,
            "passthrough": True,
            "spatial_audio": True,
        },
    ),
}


# ---------------------------------------------------------------------------
# Device Mesh Manager
# ---------------------------------------------------------------------------


class DeviceMesh:
    """Tracks local observations and prepares, but cannot deliver, handoffs."""

    def __init__(self, heartbeat_timeout_seconds: float = 60.0) -> None:
        if not math.isfinite(heartbeat_timeout_seconds) or heartbeat_timeout_seconds <= 0:
            raise ValueError("heartbeat_timeout_seconds must be finite and positive")
        self.heartbeat_timeout_seconds = heartbeat_timeout_seconds
        self.devices = {
            device_id: device.model_copy(deep=True)
            for device_id, device in DEVICE_FLEET.items()
        }
        self.handoff_log: list[ContextHandoff] = []
        logger.info(f"DeviceMesh initialized with {len(self.devices)} devices")

    def get_device(self, device_id: str) -> DeviceNode | None:
        return self.devices.get(device_id)

    def list_devices(self) -> list[DeviceNode]:
        return list(self.devices.values())

    def list_online(self) -> list[DeviceNode]:
        """Return ONLINE nodes with fresh local, unauthenticated observations."""
        return [d for d in self.devices.values() if self._is_routable(d)]

    def _is_routable(self, device: DeviceNode) -> bool:
        return (
            device.status == DeviceStatus.ONLINE
            and device.has_recent_heartbeat(self.heartbeat_timeout_seconds)
        )

    def record_heartbeat(self, device_id: str) -> DeviceNode | None:
        """Record a received signal locally; this does not verify device identity."""
        device = self.devices.get(device_id)
        if device:
            device.heartbeat()
        return device

    def list_by_role(self, role: str) -> list[DeviceNode]:
        return [d for d in self.devices.values() if role in d.roles]

    def set_status(self, device_id: str, status: DeviceStatus) -> DeviceNode | None:
        """Set recorded state without manufacturing a heartbeat or reachability."""
        device = self.devices.get(device_id)
        if device:
            device.status = status
            if status != DeviceStatus.ONLINE:
                device._heartbeat_observed_at = None
            logger.info(f"Device {device_id} status → {status.value}")
        return device

    def get_failover_chain(self, device_id: str, max_depth: int = 5) -> list[str]:
        """Get the failover chain for a device (avoids cycles)."""
        chain: list[str] = []
        visited: set[str] = {device_id}
        current = device_id

        for _ in range(max_depth):
            device = self.devices.get(current)
            if not device or not device.failover_to:
                break
            if device.failover_to in visited:
                break
            chain.append(device.failover_to)
            visited.add(device.failover_to)
            current = device.failover_to

        return chain

    def handoff_context(
        self,
        source_id: str,
        target_id: str,
        context: str,
        task_id: str | None = None,
    ) -> ContextHandoff:
        """Prepare a context handoff without modifying either device's state.

        No transport is implemented. This method cannot report completion,
        prove target reachability, or release source context. A future delivery
        implementation must obtain a real transport receipt before doing so.
        """
        source = self.devices.get(source_id)
        target = self.devices.get(target_id)

        if not source:
            raise ValueError(f"Source device not found: {source_id}")
        if not target:
            raise ValueError(f"Target device not found: {target_id}")

        # A common declared bridge is a proposal, not a working transport.
        protocol = next(
            (bridge for bridge in source.sync_bridges if bridge in target.sync_bridges),
            None,
        )

        handoff = ContextHandoff(
            source_device=source_id,
            target_device=target_id,
            context_payload=context,
            task_id=task_id,
            sync_protocol=protocol,
            status="transport_not_implemented",
        )

        self.handoff_log.append(handoff)
        logger.info(
            f"Context handoff prepared: {source_id} → {target_id}; "
            f"bridge={protocol.value if protocol else 'none'}; transport not implemented"
        )

        return handoff

    def auto_failover(self, device_id: str) -> DeviceNode | None:
        """Prepare a failover request; return None because no transfer occurred."""
        device = self.devices.get(device_id)
        if not device or not device.failover_to or not device.active_context:
            return None

        failover_chain = self.get_failover_chain(device_id)
        for target_id in failover_chain:
            target = self.devices.get(target_id)
            if target and self._is_routable(target):
                self.handoff_context(device_id, target_id, device.active_context)
                logger.info(
                    f"Failover prepared: {device_id} → {target_id}; no migration occurred"
                )
                return None

        logger.warning(f"No available failover target for {device_id}")
        return None

    def find_best_device_for_model(self, model_id: str) -> DeviceNode | None:
        """Find a fresh observed ONLINE device with declared model access.

        The registry does not verify that the model is installed or accessible.
        """
        candidates = [
            d for d in self.devices.values()
            if self._is_routable(d)
            and model_id in d.primary_model_access
        ]
        return candidates[0] if candidates else None

    def mesh_status(self) -> dict[str, Any]:
        """Return full mesh status summary."""
        devices = self.list_devices()
        online_ids = {device.id for device in self.list_online()}
        offline_count = sum(1 for d in devices if d.status == DeviceStatus.OFFLINE)
        return {
            "total_devices": len(devices),
            "online": len(online_ids),
            "offline": offline_count,
            "standby": len(devices) - len(online_ids) - offline_count,
            "heartbeat_evidence": "local_observation_only_not_authenticated",
            "transport_implemented": False,
            "total_handoffs": len(self.handoff_log),
            "devices": {
                d.id: {
                    "name": d.name,
                    "status": (
                        DeviceStatus.STANDBY.value
                        if d.status == DeviceStatus.ONLINE and d.id not in online_ids
                        else d.status.value
                    ),
                    "recorded_status": d.status.value,
                    "last_seen": d.last_seen,
                    "roles": d.roles,
                    "model_count": len(d.primary_model_access),
                    "failover_to": d.failover_to,
                }
                for d in devices
            },
        }


# Singleton mesh instance
mesh = DeviceMesh()
