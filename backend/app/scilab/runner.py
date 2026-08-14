import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass

from app.core.config import Settings
from app.core.exceptions import PowerFlowDidNotConverge, ScilabUnavailable
from app.domain.enums import BusType
from app.domain.models import GridModel
from app.power_system.per_unit import power_to_per_unit
from app.power_system.results import PowerFlowResult, build_failed_result, build_power_flow_result
from app.power_system.ybus import build_ybus

SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts")
SOLVER_SCRIPT = "power_flow.sci"
MAIN_SCRIPT = "gridflex_main.sci"
OUTPUT_FILE = "gridflex_output.txt"

_TYPE_CODE = {BusType.SLACK: 1, BusType.PV: 2, BusType.PQ: 3}


@dataclass
class ScilabCapability:
    available: bool
    version: str | None
    message: str


def _find_executable() -> str | None:
    for candidate in ("scilab-cli", "scilab"):
        path = shutil.which(candidate)
        if path:
            return path
    return None


def detect_scilab() -> ScilabCapability:
    executable = _find_executable()
    if executable is None:
        return ScilabCapability(
            available=False,
            version=None,
            message="Scilab is not installed or not present on the PATH.",
        )
    try:
        result = subprocess.run(
            [executable, "-version"],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return ScilabCapability(
            available=False,
            version=None,
            message=f"Scilab executable was found but could not be run: {exc}",
        )
    output = f"{result.stdout}\n{result.stderr}".strip()
    match = re.search(r"(\d+\.\d+\.\d+)", output)
    version = match.group(1) if match else None
    return ScilabCapability(available=True, version=version, message="Scilab is available.")


class ScilabRunner:
    def __init__(self, executable: str | None = None):
        self._executable = executable or _find_executable()

    @property
    def executable(self) -> str | None:
        return self._executable

    def _render_inputs(self, grid: GridModel, tolerance: float, max_iterations: int) -> str:
        index = {bus.id: i for i, bus in enumerate(grid.buses)}
        bus_type = [str(_TYPE_CODE[bus.type]) for bus in grid.buses]
        bus_v0 = []
        bus_theta0 = []
        for bus in grid.buses:
            if bus.type == BusType.SLACK:
                bus_v0.append(str(bus.voltage_magnitude))
                bus_theta0.append(str(bus.voltage_angle))
            elif bus.type == BusType.PV:
                bus_v0.append(str(bus.voltage_magnitude))
                bus_theta0.append("0")
            else:
                bus_v0.append("1")
                bus_theta0.append("0")

        p_spec = [0.0] * len(grid.buses)
        q_spec = [0.0] * len(grid.buses)
        for gen in grid.generators:
            i = index[gen.bus_id]
            p_spec[i] += power_to_per_unit(gen.active_power, grid.base_mva)
            q_spec[i] += power_to_per_unit(gen.reactive_power, grid.base_mva)
        for load in grid.loads:
            i = index[load.bus_id]
            p_spec[i] -= power_to_per_unit(load.active_power, grid.base_mva)
            q_spec[i] -= power_to_per_unit(load.reactive_power, grid.base_mva)

        line_rows = []
        for line in grid.lines:
            i = index[line.from_bus] + 1
            j = index[line.to_bus] + 1
            line_rows.append(f"{i} {j} {line.resistance} {line.reactance} {line.susceptance}")

        return "\n".join(
            [
                f"base_mva = {grid.base_mva};",
                f"tolerance = {tolerance};",
                f"max_iterations = {max_iterations};",
                f"bus_count = {len(grid.buses)};",
                f"bus_type = [{', '.join(bus_type)}];",
                f"bus_v0 = [{', '.join(bus_v0)}];",
                f"bus_theta0 = [{', '.join(bus_theta0)}];",
                f"bus_p_spec = [{', '.join(f'{v:.9g}' for v in p_spec)}];",
                f"bus_q_spec = [{', '.join(f'{v:.9g}' for v in q_spec)}];",
                f"line_count = {len(grid.lines)};",
                "lines = [",
                ";".join("[" + " ".join(row) + "]" for row in line_rows),
                "];",
            ]
        )

    def _parse_output(self, text: str) -> tuple[bool, int, float, list[float], list[float]]:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if len(lines) < 4:
            raise ScilabUnavailable("Scilab produced an unreadable or empty output file.")
        header = lines[0].split()
        converged = int(float(header[0])) == 1
        iterations = int(float(header[1]))
        max_mismatch = float(header[2])
        voltage = [float(v) for v in lines[1].split()]
        angle_deg = [float(v) for v in lines[2].split()]
        return converged, iterations, max_mismatch, voltage, angle_deg

    def solve(
        self,
        grid: GridModel,
        tolerance: float,
        max_iterations: int,
        settings: Settings,
    ) -> PowerFlowResult:
        if self._executable is None:
            raise ScilabUnavailable("Scilab is not installed or not present on the PATH.")

        with tempfile.TemporaryDirectory() as workdir:
            inputs_path = os.path.join(workdir, "gridflex_inputs.sci")
            main_path = os.path.join(workdir, MAIN_SCRIPT)
            solver_path = os.path.join(SCRIPTS_DIR, SOLVER_SCRIPT)
            output_path = os.path.join(workdir, OUTPUT_FILE)

            with open(inputs_path, "w") as handle:
                handle.write(self._render_inputs(grid, tolerance, max_iterations))

            main_content = "\n".join(
                [
                    f"exec('{inputs_path}', -1);",
                    f"exec('{solver_path}', -1);",
                    "[converged, iterations, max_mismatch, V, theta] = gridflex_solve(..",
                    "    base_mva, bus_type, bus_v0, bus_theta0, bus_p_spec, bus_q_spec, ..",
                    "    lines, line_count, tolerance, max_iterations);",
                    f"fd = mopen('{output_path}', 'w');",
                    "mfprintf(fd, '%d %d %.9g\\n', converged, iterations, max_mismatch);",
                    "mfprintf(fd, '%.9g ', V);",
                    "mfprintf(fd, '\\n');",
                    "mfprintf(fd, '%.9g ', theta * 180 / %pi);",
                    "mfprintf(fd, '\\n');",
                    "mclose(fd);",
                    "exit;",
                ]
            )
            with open(main_path, "w") as handle:
                handle.write(main_content)

            command = [self._executable, "-nb", "-e", f"exec('{main_path}')"]
            try:
                subprocess.run(command, capture_output=True, text=True, timeout=120, cwd=workdir)
            except subprocess.TimeoutExpired as exc:
                raise ScilabUnavailable(f"Scilab execution timed out: {exc}")
            except OSError as exc:
                raise ScilabUnavailable(f"Could not launch Scilab: {exc}")

            if not os.path.exists(output_path):
                raise ScilabUnavailable(
                    "Scilab ran but produced no output file; the solve may have failed."
                )

            with open(output_path) as handle:
                converged, iterations, max_mismatch, voltage, angle_deg = self._parse_output(
                    handle.read()
                )

        if not converged:
            raise PowerFlowDidNotConverge(
                f"Scilab power flow did not converge after {iterations} iterations "
                f"(max mismatch {max_mismatch:.3e}).",
                max_mismatch=max_mismatch,
                iterations=iterations,
            )

        import numpy as np

        ybus = build_ybus(grid)
        solution = build_power_flow_result(
            grid,
            ybus,
            _solution_from(voltage, angle_deg, converged, iterations, max_mismatch),
            self.name(),
            settings,
        )
        return solution

    @staticmethod
    def name() -> str:
        return "scilab"


def _solution_from(
    voltage: list[float],
    angle_deg: list[float],
    converged: bool,
    iterations: int,
    max_mismatch: float,
):
    from app.power_system.power_flow import PowerFlowSolution

    import numpy as np

    return PowerFlowSolution(
        converged=converged,
        iterations=iterations,
        max_mismatch=max_mismatch,
        voltage_magnitude=np.array(voltage),
        voltage_angle=np.deg2rad(np.array(angle_deg)),
    )
