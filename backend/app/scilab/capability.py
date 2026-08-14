"""Scilab capability detection and health checking.

Detection results are cached for ``Settings.scilab_capability_ttl_seconds`` so
expensive subprocess probes are not repeated on every API request. Use
``invalidate_scilab_capability_cache`` after changing configuration.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

from app.core.config import Settings, settings as default_settings
from app.scilab import paths

_EXECUTABLE_CANDIDATES = ("scilab-cli", "scilab")
_SUPPORTED_OPERATIONS = ["power_flow", "ybus", "line_flow"]


@dataclass
class ScilabCapability:
    available: bool
    executable_path: str | None = None
    version: str | None = None
    health_check_status: str = "not_run"
    last_checked: float | None = None
    message: str = ""
    supported_operations: list[str] = field(default_factory=lambda: list(_SUPPORTED_OPERATIONS))

    @property
    def last_checked_iso(self) -> str | None:
        if self.last_checked is None:
            return None
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(self.last_checked))


def find_executable(settings: Settings = default_settings) -> str | None:
    """Return the Scilab executable path, honouring explicit configuration."""
    configured = settings.scilab_executable
    if configured:
        if os.path.isfile(configured) and os.access(configured, os.X_OK):
            return configured
        return None
    for candidate in _EXECUTABLE_CANDIDATES:
        path = shutil.which(candidate)
        if path:
            return path
    return None


def detect_version(
    executable: str, timeout_seconds: int = 30
) -> str | None:
    """Determine the Scilab version. Returns None when it cannot be found."""
    try:
        result = subprocess.run(
            [executable, "-version"],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    output = f"{result.stdout}\n{result.stderr}"
    match = re.search(r"(\d+\.\d+(?:\.\d+)?)", output)
    return match.group(1) if match else None


def _parse_health_check(text: str) -> dict:
    status = "failed"
    message = text.strip()
    for line in text.splitlines():
        parts = line.split(None, 1)
        if len(parts) < 2:
            continue
        if parts[0] == "status":
            status = parts[1]
        elif parts[0] == "message":
            message = parts[1]
    return {"status": status, "message": message}


def run_health_check(
    executable: str,
    settings: Settings = default_settings,
) -> dict:
    """Run the internal health-check script in an isolated temp directory.

    Returns ``{"status": "ok"|"failed", "message": str}``.
    """
    with paths.temporary_workdir() as workdir:
        for name in (
            "build_ybus.sci",
            "newton_raphson.sci",
            "calculate_line_flows.sci",
            "health_check.sce",
        ):
            shutil.copy(paths.script(name), workdir / name)
        try:
            result = subprocess.run(
                [
                    executable,
                    "-nb",
                    "-nw",
                    "-e",
                    f"exec('{workdir / 'health_check.sce'}', -1)",
                ],
                capture_output=True,
                text=True,
                timeout=settings.scilab_timeout_seconds,
                cwd=str(workdir),
            )
        except subprocess.TimeoutExpired:
            return {"status": "failed", "message": "health check timed out"}
        except OSError as exc:
            return {"status": "failed", "message": f"could not launch Scilab: {exc}"}

        health_path = workdir / "health_check.txt"
        if not health_path.exists():
            return {
                "status": "failed",
                "message": "Scilab ran but produced no health-check output",
            }
        parsed = _parse_health_check(health_path.read_text())
        if result.returncode != 0 and parsed["status"] != "ok":
            return {"status": "failed", "message": parsed["message"]}
        return parsed


_cache_lock = threading.Lock()
_cache: dict = {}


def get_capability(
    settings: Settings = default_settings,
    force: bool = False,
) -> ScilabCapability:
    """Return (and cache) the Scilab capability, running a health check.

    Never runs expensive process detection more often than the configured TTL.
    """
    key = (
        settings.scilab_executable,
        settings.scilab_timeout_seconds,
    )
    with _cache_lock:
        cached = _cache.get(key)
        now = time.time()
        if (
            not force
            and cached is not None
            and now - cached.last_checked < settings.scilab_capability_ttl_seconds
        ):
            return cached

    executable = find_executable(settings)
    if executable is None:
        capability = ScilabCapability(
            available=False,
            health_check_status="not_run",
            last_checked=now,
            message=(
                "Scilab is not installed, not configured via "
                "GRIDFLEX_SCILAB_EXECUTABLE, or not present on the PATH."
            ),
        )
    else:
        version = detect_version(executable)
        health = run_health_check(executable, settings)
        ok = health["status"] == "ok"
        capability = ScilabCapability(
            available=ok,
            executable_path=executable,
            version=version,
            health_check_status=health["status"],
            last_checked=now,
            message=(
                health["message"]
                if not ok
                else f"Scilab is available at {executable}."
            ),
        )

    with _cache_lock:
        _cache[key] = capability
    return capability


def invalidate_scilab_capability_cache() -> None:
    with _cache_lock:
        _cache.clear()


def scilab_status_payload(
    settings: Settings = default_settings,
    force: bool = False,
) -> dict:
    """Public-facing status payload for ``GET /engines/scilab/status``."""
    capability = get_capability(settings, force=force)
    return {
        "available": capability.available,
        "version": capability.version,
        "executable_path": capability.executable_path,
        "health_check": capability.health_check_status,
        "supported_operations": list(capability.supported_operations),
        "last_checked": capability.last_checked_iso,
        "message": capability.message,
    }
