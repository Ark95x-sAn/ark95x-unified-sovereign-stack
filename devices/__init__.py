"""ARK95X devices adapter -- scoped local docker-compose execution, gated
through the single control plane. See devices/local_exec.py."""
from .local_exec import DevicesAdapter

__all__ = ["DevicesAdapter"]
