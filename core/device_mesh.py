"""
ARK95X Device Mesh
==================
Maps 9 physical devices to their operational roles and handles context
handoff logic across the sovereign device fleet.

Each device has:
    - id, name, roles[], status (online/offline/standby)
    - primary_model_access[] — which models this device can reach
    - failover_to — fallback device if this one goes offline
    - sync_bridges[] — how this device syncs with others
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from loguru import logger
from pydantic import BaseModel, Field


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

    def heartbeat(self) -> None:
        """Update last seen timestamp."""
        self.last_seen = datetime.now(timezone.utc).isoformat()
        if self.status == DeviceStatus.OFFLINE:
            self.status = DeviceStatus.ONLINE


class ContextHandoff(BaseModel):
    """Represents a context transfer between two devices."""

    source_device: str
    target_device: str
    context_payload: str
    task_id: str | None = None
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    sync_protocol: SyncProtocol = SyncProtocol.CLOUD_SYNC
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
        status=DeviceStatus.ONLINE,
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
        status=DeviceStatus.ONLINE,
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
    """Manages the sovereign device fleet and context handoffs."""

    def __init__(self) -> None:
        self.devices = DEVICE_FLEET.copy()
        self.handoff_log: list[ContextHandoff] = []
        logger.info(f"DeviceMesh initialized with {len(self.devices)} devices")

    def get_device(self, device_id: str) -> DeviceNode | None:
        return self.devices.get(device_id)

    def list_devices(self) -> list[DeviceNode]:
        return list(self.devices.values())

    def list_online(self) -> list[DeviceNode]:
        return [d for d in self.devices.values() if d.status == DeviceStatus.ONLINE]

    def list_by_role(self, role: str) -> list[DeviceNode]:
        return [d for d in self.devices.values() if role in d.roles]

    def set_status(self, device_id: str, status: DeviceStatus) -> DeviceNode | None:
        device = self.devices.get(device_id)
        if device:
            device.status = status
            if status == DeviceStatus.ONLINE:
                device.heartbeat()
            logger.info(f"Device {device_id} status → {status.value}")
        return device

    def get_failover_chain(self, device_id: str, max_depth: int = 5) -> list[str]:
        """Get the failover chain for a device (avoids cycles)."""
        chain: list[str] = []
        visited: set[str] = set()
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
        """Transfer context from one device to another."""
        source = self.devices.get(source_id)
        target = self.devices.get(target_id)

        if not source:
            raise ValueError(f"Source device not found: {source_id}")
        if not target:
            raise ValueError(f"Target device not found: {target_id}")

        # Find common sync protocol
        common_protocols = set(source.sync_bridges) & set(target.sync_bridges)
        protocol = (
            list(common_protocols)[0] if common_protocols else SyncProtocol.CLOUD_SYNC
        )

        handoff = ContextHandoff(
            source_device=source_id,
            target_device=target_id,
            context_payload=context,
            task_id=task_id,
            sync_protocol=protocol,
            status="completed",
        )

        # Update device contexts
        source.active_context = None
        target.active_context = context
        target.heartbeat()

        self.handoff_log.append(handoff)
        logger.info(
            f"Context handoff: {source_id} → {target_id} via {protocol.value}"
        )

        return handoff

    def auto_failover(self, device_id: str) -> DeviceNode | None:
        """Automatically failover to the next available device."""
        device = self.devices.get(device_id)
        if not device or not device.failover_to:
            return None

        failover_chain = self.get_failover_chain(device_id)
        for target_id in failover_chain:
            target = self.devices.get(target_id)
            if target and target.status != DeviceStatus.OFFLINE:
                if device.active_context:
                    self.handoff_context(
                        device_id, target_id, device.active_context
                    )
                logger.info(f"Auto-failover: {device_id} → {target_id}")
                return target

        logger.warning(f"No available failover target for {device_id}")
        return None

    def find_best_device_for_model(self, model_id: str) -> DeviceNode | None:
        """Find the best online device that can access a given model."""
        candidates = [
            d for d in self.devices.values()
            if d.status == DeviceStatus.ONLINE
            and model_id in d.primary_model_access
        ]
        if not candidates:
            # Try standby devices
            candidates = [
                d for d in self.devices.values()
                if d.status == DeviceStatus.STANDBY
                and model_id in d.primary_model_access
            ]
        return candidates[0] if candidates else None

    def mesh_status(self) -> dict[str, Any]:
        """Return full mesh status summary."""
        devices = self.list_devices()
        return {
            "total_devices": len(devices),
            "online": sum(1 for d in devices if d.status == DeviceStatus.ONLINE),
            "offline": sum(1 for d in devices if d.status == DeviceStatus.OFFLINE),
            "standby": sum(1 for d in devices if d.status == DeviceStatus.STANDBY),
            "total_handoffs": len(self.handoff_log),
            "devices": {
                d.id: {
                    "name": d.name,
                    "status": d.status.value,
                    "roles": d.roles,
                    "model_count": len(d.primary_model_access),
                    "failover_to": d.failover_to,
                }
                for d in devices
            },
        }


# Singleton mesh instance
mesh = DeviceMesh()
