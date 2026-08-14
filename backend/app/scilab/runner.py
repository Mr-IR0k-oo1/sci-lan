"""Safe Scilab runner.

Executes the internal GridFlex Scilab scripts in an isolated temporary
directory with an explicit argument list, a hard timeout, and strict structured
output parsing. Never builds shell commands through string concatenation and
never executes user-provided code.

Pipeline:

    GridModel -> normalized input variables (inputs.sci)
              -> subprocess(scilab -nb -nw -e "exec('power_flow.sce')")
              -> gridflex_results.txt (documented deterministic format, or JSON)
              -> dict  (raw structured result)
"""

from __future__ import annotations

import json
import shutil
import subprocess
from typing import Any

from app.core.config import Settings, settings as default_settings
from app.core.exceptions import ScilabUnavailable
from app.domain.models import GridModel
from app.scilab import paths
from app.scilab.capability import find_executable
from app.scilab.input_format import render_scilab_input_variables

_SCRIPTS = (
    "build_ybus.sci",
    "newton_raphson.sci",
    "calculate_line_flows.sci",
    "export_results.sci",
    "power_flow.sce",
)


class ScilabRunner:
    def __init__(
        self,
        executable: str | None = None,
        timeout_seconds: int | None = None,
    ):
        self._executable = executable
        self._timeout_seconds = timeout_seconds

    @property
    def executable(self) -> str | None:
        return self._executable

    def _resolve(self, settings: Settings) -> str:
        executable = self._executable or find_executable(settings)
        if executable is None:
            raise ScilabUnavailable(
                "Scilab is not installed or not present on the PATH."
            )
        return executable

    @staticmethod
    def _timeout(settings: Settings) -> int:
        return settings.scilab_timeout_seconds

    def _prepare_workdir(self, workdir, grid: GridModel, tolerance: float, max_iterations: int) -> None:
        (workdir / paths.INPUT_FILE).write_text(
            render_scilab_input_variables(grid, tolerance, max_iterations)
        )
        for name in _SCRIPTS:
            shutil.copy(paths.script(name), workdir / name)

    def solve(
        self,
        grid: GridModel,
        tolerance: float,
        max_iterations: int,
        settings: Settings = default_settings,
    ) -> dict[str, Any]:
        """Run the Scilab power flow and return the raw structured result dict."""
        executable = self._resolve(settings)
        timeout = self._timeout(settings)

        with paths.temporary_workdir() as workdir:
            self._prepare_workdir(workdir, grid, tolerance, max_iterations)
            output_path = workdir / paths.RESULT_FILE

            # Explicit argument list; nothing is shell-interpolated.
            command = [
                executable,
                "-nb",
                "-nw",
                "-e",
                f"exec('{workdir / 'power_flow.sce'}', -1)",
            ]
            try:
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=str(workdir),
                )
            except subprocess.TimeoutExpired as exc:
                raise ScilabUnavailable(
                    f"Scilab execution timed out after {timeout} seconds."
                ) from exc
            except OSError as exc:
                raise ScilabUnavailable(f"Could not launch Scilab: {exc}") from exc

            if not output_path.exists():
                detail = (result.stderr or "").strip().splitlines()[-1:] or [
                    "no output produced"
                ]
                raise ScilabUnavailable(
                    "Scilab produced no structured output; the solve failed "
                    f"({detail[0]})."
                )

            return parse_result_file(output_path.read_text())


def parse_result_file(text: str) -> dict[str, Any]:
    """Parse a Scilab result file.

    Accepts the documented deterministic line format (v1) and JSON output, so
    a future Scilab release that emits JSON keeps working unchanged.
    """
    stripped = text.lstrip()
    if stripped.startswith("{"):
        return _parse_json_result(stripped)
    return _parse_line_format(stripped)


def _parse_json_result(text: str) -> dict[str, Any]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ScilabUnavailable(
            f"Scilab produced invalid JSON output: {exc}"
        ) from exc
    return payload


def _parse_line_format(text: str) -> dict[str, Any]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines or lines[0] != "gridflex_results v1":
        raise ScilabUnavailable(
            "Scilab produced an unrecognized output format "
            "(expected 'gridflex_results v1')."
        )

    def values_for(key: str, expected_count: int | None = None) -> list[float]:
        for line in lines[1:]:
            parts = line.split()
            if parts and parts[0] == key:
                values = [float(part) for part in parts[1:]]
                if expected_count is not None and len(values) != expected_count:
                    raise ScilabUnavailable(
                        f"Scilab output line '{key}' has {len(values)} values; "
                        f"expected {expected_count}."
                    )
                return values
        raise ScilabUnavailable(f"Scilab output is missing the '{key}' section.")

    try:
        converged = int(values_for("converged", 1)[0]) == 1
        iterations = int(values_for("iterations", 1)[0])
        max_mismatch = values_for("max_mismatch", 1)[0]
        bus_count = int(values_for("bus_count", 1)[0])
        bus_v = values_for("bus_v", bus_count)
        bus_theta_deg = values_for("bus_theta_deg", bus_count)
        bus_p_pu = values_for("bus_p_pu", bus_count)
        bus_q_pu = values_for("bus_q_pu", bus_count)
        line_count = int(values_for("line_count", 1)[0])
        line_flows = values_for("line_flows", line_count * 4)
    except (ValueError, IndexError) as exc:
        raise ScilabUnavailable(
            f"Scilab output is malformed: {exc}"
        ) from exc

    flows = [
        {
            "index": k,
            "P_from_pu": line_flows[k * 4],
            "Q_from_pu": line_flows[k * 4 + 1],
            "P_to_pu": line_flows[k * 4 + 2],
            "Q_to_pu": line_flows[k * 4 + 3],
        }
        for k in range(line_count)
    ]
    buses = [
        {
            "index": i,
            "V": bus_v[i],
            "theta_deg": bus_theta_deg[i],
            "P_pu": bus_p_pu[i],
            "Q_pu": bus_q_pu[i],
        }
        for i in range(bus_count)
    ]
    return {
        "converged": converged,
        "iterations": iterations,
        "max_mismatch": max_mismatch,
        "buses": buses,
        "lines": flows,
    }
