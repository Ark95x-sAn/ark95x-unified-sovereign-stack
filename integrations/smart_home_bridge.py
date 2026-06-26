"""
ARK95X Smart Home Bridge
=========================
Unified interface to Alexa, Google Home, SmartThings, and local MQTT.

Voice or text commands flow in, get parsed into device actions,
and fan out to whichever hubs are configured.

Architecture:
    SmartHomeBridge
        ├── AlexaBridge  (Alexa Skills API + Alexa Gadgets)
        ├── GoogleHomeBridge (Google Home Graph + Assistant)
        ├── SmartThingsBridge (Samsung SmartThings REST API)
        └── MQTTBridge  (local Mosquitto — offline capable)

All bridges implement the same SmartHomeCommand interface so the
coordinator can send commands without knowing which hub runs what.
"""

from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import httpx
from loguru import logger


# ---------------------------------------------------------------------------
# Domain Types
# ---------------------------------------------------------------------------


class DeviceType(str, Enum):
    LIGHT = "light"
    SWITCH = "switch"
    THERMOSTAT = "thermostat"
    LOCK = "lock"
    CAMERA = "camera"
    SENSOR = "sensor"
    SPEAKER = "speaker"
    TV = "tv"
    PLUG = "plug"
    FAN = "fan"
    BLIND = "blind"
    GARAGE = "garage"
    ALARM = "alarm"
    ROUTER = "router"


class CommandType(str, Enum):
    TURN_ON = "turn_on"
    TURN_OFF = "turn_off"
    SET_BRIGHTNESS = "set_brightness"
    SET_COLOR = "set_color"
    SET_TEMPERATURE = "set_temperature"
    LOCK = "lock"
    UNLOCK = "unlock"
    GET_STATE = "get_state"
    LIST_DEVICES = "list_devices"
    RUN_ROUTINE = "run_routine"
    SPEAK = "speak"


@dataclass
class SmartHomeCommand:
    command: CommandType
    device_name: str | None = None
    device_id: str | None = None
    device_type: DeviceType | None = None
    value: Any = None
    room: str | None = None
    routine_name: str | None = None
    text: str | None = None


@dataclass
class SmartHomeResult:
    success: bool
    hub: str
    device_name: str | None = None
    state: dict[str, Any] = field(default_factory=dict)
    message: str = ""
    error: str | None = None


# ---------------------------------------------------------------------------
# Natural Language Parser
# ---------------------------------------------------------------------------


NL_PATTERNS: list[tuple[list[str], CommandType]] = [
    (["turn on", "switch on", "power on", "lights on", "activate"], CommandType.TURN_ON),
    (["turn off", "switch off", "power off", "lights off", "deactivate"], CommandType.TURN_OFF),
    (["dim", "brightness", "set brightness", "brighten"], CommandType.SET_BRIGHTNESS),
    (["color", "hue", "set color", "change color"], CommandType.SET_COLOR),
    (["temperature", "thermostat", "heat", "cool", "degrees"], CommandType.SET_TEMPERATURE),
    (["lock", "secure", "close the lock"], CommandType.LOCK),
    (["unlock", "open the lock", "let me in"], CommandType.UNLOCK),
    (["what is", "status of", "is the", "check"], CommandType.GET_STATE),
    (["list devices", "what devices", "show devices"], CommandType.LIST_DEVICES),
    (["run routine", "activate routine", "good morning", "good night", "movie mode"], CommandType.RUN_ROUTINE),
    (["say", "announce", "tell", "speak"], CommandType.SPEAK),
]

ROOM_KEYWORDS = [
    "living room", "bedroom", "kitchen", "bathroom", "garage",
    "office", "basement", "hallway", "porch", "backyard",
    "master", "guest", "dining", "laundry",
]


def parse_nl_command(text: str) -> SmartHomeCommand:
    """Parse a natural language string into a SmartHomeCommand."""
    lower = text.lower()

    command = CommandType.GET_STATE  # default
    for triggers, cmd in NL_PATTERNS:
        if any(t in lower for t in triggers):
            command = cmd
            break

    room = next((r for r in ROOM_KEYWORDS if r in lower), None)

    value: Any = None
    if command == CommandType.SET_BRIGHTNESS:
        import re
        m = re.search(r"(\d+)\s*%?", lower)
        if m:
            value = int(m.group(1))
    elif command == CommandType.SET_TEMPERATURE:
        import re
        m = re.search(r"(\d+)\s*(?:degrees|°|f|c)?", lower)
        if m:
            value = int(m.group(1))

    return SmartHomeCommand(
        command=command,
        device_name=text,
        room=room,
        value=value,
        text=text if command == CommandType.SPEAK else None,
    )


# ---------------------------------------------------------------------------
# Hub Base
# ---------------------------------------------------------------------------


class SmartHomeHub:
    name: str = "base"

    async def execute(self, cmd: SmartHomeCommand) -> SmartHomeResult:
        raise NotImplementedError

    async def list_devices(self) -> list[dict[str, Any]]:
        raise NotImplementedError

    def is_configured(self) -> bool:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Alexa Bridge
# ---------------------------------------------------------------------------


class AlexaBridge(SmartHomeHub):
    name = "alexa"

    def __init__(self) -> None:
        self.client_id = os.getenv("ALEXA_CLIENT_ID", "")
        self.client_secret = os.getenv("ALEXA_CLIENT_SECRET", "")
        self.refresh_token = os.getenv("ALEXA_REFRESH_TOKEN", "")
        self._access_token: str | None = None

    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret and self.refresh_token)

    async def _get_token(self) -> str | None:
        if self._access_token:
            return self._access_token
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    "https://api.amazon.com/auth/o2/token",
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": self.refresh_token,
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                    },
                )
                data = resp.json()
                self._access_token = data.get("access_token")
                return self._access_token
        except Exception as e:
            logger.error(f"[ALEXA] Token error: {e}")
            return None

    async def execute(self, cmd: SmartHomeCommand) -> SmartHomeResult:
        if not self.is_configured():
            return SmartHomeResult(
                success=False, hub=self.name,
                error="Alexa not configured (ALEXA_CLIENT_ID, ALEXA_CLIENT_SECRET, ALEXA_REFRESH_TOKEN)"
            )
        token = await self._get_token()
        if not token:
            return SmartHomeResult(success=False, hub=self.name, error="Alexa auth failed")

        directive = self._build_directive(cmd)
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    "https://api.amazonalexa.com/v3/events",
                    headers={"Authorization": f"Bearer {token}"},
                    json=directive,
                )
                return SmartHomeResult(
                    success=resp.status_code in (200, 202),
                    hub=self.name,
                    device_name=cmd.device_name,
                    message=f"HTTP {resp.status_code}",
                )
        except Exception as e:
            return SmartHomeResult(success=False, hub=self.name, error=str(e))

    def _build_directive(self, cmd: SmartHomeCommand) -> dict[str, Any]:
        namespace_map = {
            CommandType.TURN_ON: ("Alexa.PowerController", "TurnOn"),
            CommandType.TURN_OFF: ("Alexa.PowerController", "TurnOff"),
            CommandType.SET_BRIGHTNESS: ("Alexa.BrightnessController", "SetBrightness"),
            CommandType.LOCK: ("Alexa.LockController", "Lock"),
            CommandType.UNLOCK: ("Alexa.LockController", "Unlock"),
        }
        ns, name = namespace_map.get(cmd.command, ("Alexa.PowerController", "TurnOn"))
        payload: dict[str, Any] = {}
        if cmd.command == CommandType.SET_BRIGHTNESS and cmd.value is not None:
            payload["brightness"] = cmd.value

        return {
            "directive": {
                "header": {
                    "namespace": ns,
                    "name": name,
                    "messageId": __import__("uuid").uuid4().hex,
                    "payloadVersion": "3",
                },
                "endpoint": {
                    "scope": {"type": "BearerToken", "token": ""},
                    "endpointId": cmd.device_id or cmd.device_name or "unknown",
                },
                "payload": payload,
            }
        }

    async def list_devices(self) -> list[dict[str, Any]]:
        return [{"hub": "alexa", "status": "list_requires_skill_api"}]


# ---------------------------------------------------------------------------
# Google Home Bridge
# ---------------------------------------------------------------------------


class GoogleHomeBridge(SmartHomeHub):
    name = "google_home"

    def __init__(self) -> None:
        self.api_key = os.getenv("GOOGLE_HOME_API_KEY", "")
        self.project_id = os.getenv("GOOGLE_HOME_PROJECT_ID", "")

    def is_configured(self) -> bool:
        return bool(self.api_key and self.project_id)

    async def execute(self, cmd: SmartHomeCommand) -> SmartHomeResult:
        if not self.is_configured():
            return SmartHomeResult(
                success=False, hub=self.name,
                error="Google Home not configured (GOOGLE_HOME_API_KEY, GOOGLE_HOME_PROJECT_ID)"
            )

        execution = self._build_execution(cmd)
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    f"https://homegraph.googleapis.com/v1/devices:executeRequest?key={self.api_key}",
                    json={
                        "requestId": __import__("uuid").uuid4().hex,
                        "inputs": [{
                            "intent": "action.devices.EXECUTE",
                            "payload": {
                                "commands": [{
                                    "devices": [{"id": cmd.device_id or "unknown"}],
                                    "execution": [execution],
                                }]
                            },
                        }],
                    },
                )
                return SmartHomeResult(
                    success=resp.status_code == 200,
                    hub=self.name,
                    device_name=cmd.device_name,
                    state=resp.json() if resp.status_code == 200 else {},
                    message=f"HTTP {resp.status_code}",
                )
        except Exception as e:
            return SmartHomeResult(success=False, hub=self.name, error=str(e))

    def _build_execution(self, cmd: SmartHomeCommand) -> dict[str, Any]:
        mapping = {
            CommandType.TURN_ON: {"command": "action.devices.commands.OnOff", "params": {"on": True}},
            CommandType.TURN_OFF: {"command": "action.devices.commands.OnOff", "params": {"on": False}},
            CommandType.SET_BRIGHTNESS: {
                "command": "action.devices.commands.BrightnessAbsolute",
                "params": {"brightness": cmd.value or 100},
            },
            CommandType.LOCK: {"command": "action.devices.commands.LockUnlock", "params": {"lock": True}},
            CommandType.UNLOCK: {"command": "action.devices.commands.LockUnlock", "params": {"lock": False}},
            CommandType.SET_TEMPERATURE: {
                "command": "action.devices.commands.ThermostatTemperatureSetpoint",
                "params": {"thermostatTemperatureSetpoint": cmd.value or 70},
            },
        }
        return mapping.get(cmd.command, {"command": "action.devices.commands.OnOff", "params": {"on": True}})

    async def list_devices(self) -> list[dict[str, Any]]:
        return [{"hub": "google_home", "status": "list_requires_home_graph_api"}]


# ---------------------------------------------------------------------------
# SmartThings Bridge
# ---------------------------------------------------------------------------


class SmartThingsBridge(SmartHomeHub):
    name = "smartthings"

    def __init__(self) -> None:
        self.token = os.getenv("SMARTTHINGS_TOKEN", "")

    def is_configured(self) -> bool:
        return bool(self.token)

    async def list_devices(self) -> list[dict[str, Any]]:
        if not self.is_configured():
            return [{"error": "SMARTTHINGS_TOKEN not set"}]
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    "https://api.smartthings.com/v1/devices",
                    headers={"Authorization": f"Bearer {self.token}"},
                )
                data = resp.json()
                return data.get("items", [])
        except Exception as e:
            return [{"error": str(e)}]

    async def execute(self, cmd: SmartHomeCommand) -> SmartHomeResult:
        if not self.is_configured():
            return SmartHomeResult(
                success=False, hub=self.name,
                error="SmartThings not configured (SMARTTHINGS_TOKEN)"
            )
        if not cmd.device_id:
            return SmartHomeResult(
                success=False, hub=self.name,
                error="SmartThings requires device_id"
            )

        commands = self._build_commands(cmd)
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    f"https://api.smartthings.com/v1/devices/{cmd.device_id}/commands",
                    headers={"Authorization": f"Bearer {self.token}"},
                    json={"commands": commands},
                )
                return SmartHomeResult(
                    success=resp.status_code == 200,
                    hub=self.name,
                    device_name=cmd.device_name,
                    message=f"HTTP {resp.status_code}",
                )
        except Exception as e:
            return SmartHomeResult(success=False, hub=self.name, error=str(e))

    def _build_commands(self, cmd: SmartHomeCommand) -> list[dict[str, Any]]:
        mapping = {
            CommandType.TURN_ON: [{"capability": "switch", "command": "on"}],
            CommandType.TURN_OFF: [{"capability": "switch", "command": "off"}],
            CommandType.SET_BRIGHTNESS: [
                {"capability": "switchLevel", "command": "setLevel", "arguments": [cmd.value or 100]}
            ],
            CommandType.LOCK: [{"capability": "lock", "command": "lock"}],
            CommandType.UNLOCK: [{"capability": "lock", "command": "unlock"}],
            CommandType.SET_TEMPERATURE: [
                {"capability": "thermostatCoolingSetpoint", "command": "setCoolingSetpoint",
                 "arguments": [cmd.value or 72]}
            ],
        }
        return mapping.get(cmd.command, [{"capability": "switch", "command": "on"}])


# ---------------------------------------------------------------------------
# MQTT Bridge (local/offline)
# ---------------------------------------------------------------------------


class MQTTBridge(SmartHomeHub):
    name = "mqtt"

    def __init__(self) -> None:
        self.host = os.getenv("MQTT_HOST", "localhost")
        self.port = int(os.getenv("MQTT_PORT", "1883"))
        self.username = os.getenv("MQTT_USERNAME", "")
        self.password = os.getenv("MQTT_PASSWORD", "")

    def is_configured(self) -> bool:
        return True  # local MQTT always available if Mosquitto is running

    async def execute(self, cmd: SmartHomeCommand) -> SmartHomeResult:
        topic = self._command_to_topic(cmd)
        payload_str = json.dumps({"command": cmd.command.value, "value": cmd.value})
        try:
            proc = await asyncio.create_subprocess_exec(
                "mosquitto_pub",
                "-h", self.host,
                "-p", str(self.port),
                "-t", topic,
                "-m", payload_str,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await proc.communicate()
            if proc.returncode == 0:
                return SmartHomeResult(
                    success=True, hub=self.name,
                    device_name=cmd.device_name,
                    message=f"Published to {topic}",
                )
            return SmartHomeResult(
                success=False, hub=self.name,
                error=stderr.decode() or "mosquitto_pub failed"
            )
        except FileNotFoundError:
            return SmartHomeResult(
                success=False, hub=self.name,
                error="mosquitto_pub not installed — install Mosquitto clients"
            )
        except Exception as e:
            return SmartHomeResult(success=False, hub=self.name, error=str(e))

    def _command_to_topic(self, cmd: SmartHomeCommand) -> str:
        room = (cmd.room or "all").replace(" ", "_")
        device = (cmd.device_name or "device").replace(" ", "_")
        return f"home/{room}/{device}/{cmd.command.value}"

    async def list_devices(self) -> list[dict[str, Any]]:
        return [{"hub": "mqtt", "note": "Subscribe to home/# to discover devices"}]


# ---------------------------------------------------------------------------
# Unified Bridge
# ---------------------------------------------------------------------------


class SmartHomeBridge:
    """
    Fan-out to all configured smart home hubs.
    Parse natural language or accept structured commands.
    """

    def __init__(self) -> None:
        self.hubs: list[SmartHomeHub] = [
            AlexaBridge(),
            GoogleHomeBridge(),
            SmartThingsBridge(),
            MQTTBridge(),
        ]

    def configured_hubs(self) -> list[str]:
        return [h.name for h in self.hubs if h.is_configured()]

    async def send(self, cmd: SmartHomeCommand) -> list[SmartHomeResult]:
        """Send command to all configured hubs in parallel."""
        tasks = [
            hub.execute(cmd)
            for hub in self.hubs
            if hub.is_configured()
        ]
        if not tasks:
            return [SmartHomeResult(
                success=False, hub="none",
                error="No smart home hubs configured"
            )]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        out: list[SmartHomeResult] = []
        for r in results:
            if isinstance(r, Exception):
                out.append(SmartHomeResult(success=False, hub="unknown", error=str(r)))
            else:
                out.append(r)
        return out

    async def send_nl(self, text: str) -> dict[str, Any]:
        """Parse natural language and dispatch to all hubs."""
        cmd = parse_nl_command(text)
        results = await self.send(cmd)
        return {
            "parsed_command": cmd.command.value,
            "room": cmd.room,
            "value": cmd.value,
            "results": [
                {
                    "hub": r.hub,
                    "success": r.success,
                    "message": r.message,
                    "error": r.error,
                }
                for r in results
            ],
        }

    async def list_all_devices(self) -> dict[str, Any]:
        """List devices from all configured hubs."""
        out: dict[str, Any] = {}
        for hub in self.hubs:
            if hub.is_configured():
                try:
                    out[hub.name] = await hub.list_devices()
                except Exception as e:
                    out[hub.name] = [{"error": str(e)}]
        return out


# Singleton
bridge = SmartHomeBridge()


if __name__ == "__main__":
    async def demo() -> None:
        result = await bridge.send_nl("Turn on the living room lights")
        print(json.dumps(result, indent=2))

    asyncio.run(demo())
