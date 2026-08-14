from __future__ import annotations

from abc import ABC, abstractmethod
import platform
import time

from app.core.config import Settings, settings as default_settings
from app.core.exceptions import InvalidEngine, PowerFlowDidNotConverge
from app.domain.models import GridModel
from app.power_system.power_flow import solve_power_flow
from app.power_system.results import PowerFlowResult, build_power_flow_result
from app.power_system.ybus import build_ybus
from app.scilab import normalize
from app.scilab.capability import get_capability
from app.scilab.runner import ScilabRunner
from app.schemas.analysis import EngineInfoResponse

# Selection modes. AUTO prefers Scilab when it is available and operational,
# otherwise falls back to Python.
AUTO = "auto"


class PowerFlowEngine(ABC):
    name: str = ""

    @abstractmethod
    def info(self) -> EngineInfoResponse:
        raise NotImplementedError

    @abstractmethod
    def engine_version(self, settings: Settings) -> str | None:
        raise NotImplementedError

    @abstractmethod
    def run(
        self,
        grid: GridModel,
        tolerance: float,
        max_iterations: int,
        settings: Settings,
    ) -> PowerFlowResult:
        raise NotImplementedError


class PythonPowerFlowEngine(PowerFlowEngine):
    name = "python"

    def info(self) -> EngineInfoResponse:
        return EngineInfoResponse(
            name=self.name,
            available=True,
            version=platform.python_version(),
            status="available",
        )

    def engine_version(self, settings: Settings) -> str | None:
        return platform.python_version()

    def run(
        self,
        grid: GridModel,
        tolerance: float,
        max_iterations: int,
        settings: Settings,
    ) -> PowerFlowResult:
        started = time.perf_counter()
        ybus = build_ybus(grid)
        solution = solve_power_flow(grid, ybus, tolerance, max_iterations)
        if not solution.converged:
            raise PowerFlowDidNotConverge(
                f"Power flow did not converge after {solution.iterations} "
                f"iterations (max mismatch {solution.max_mismatch:.3e}).",
                max_mismatch=solution.max_mismatch,
                iterations=solution.iterations,
            )
        result = build_power_flow_result(
            grid,
            ybus,
            solution,
            self.name,
            settings,
            engine_version=self.engine_version(settings),
        )
        result.execution_time_ms = (time.perf_counter() - started) * 1000.0
        return result


class ScilabPowerFlowEngine(PowerFlowEngine):
    name = "scilab"

    def info(self) -> EngineInfoResponse:
        capability = get_capability()
        return EngineInfoResponse(
            name=self.name,
            available=capability.available,
            version=capability.version,
            status="available" if capability.available else "unavailable",
        )

    def engine_version(self, settings: Settings) -> str | None:
        return get_capability(settings).version

    def run(
        self,
        grid: GridModel,
        tolerance: float,
        max_iterations: int,
        settings: Settings,
    ) -> PowerFlowResult:
        capability = get_capability(settings, force=True)
        if not capability.available:
            raise InvalidEngine(
                "Scilab is not available; it cannot execute the power flow."
            )
        started = time.perf_counter()
        raw = ScilabRunner().solve(grid, tolerance, max_iterations, settings)
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        if not raw.get("converged"):
            raise PowerFlowDidNotConverge(
                f"Scilab power flow did not converge after {raw.get('iterations', 0)} "
                f"iterations (max mismatch {raw.get('max_mismatch', 0.0):.3e}).",
                max_mismatch=raw.get("max_mismatch"),
                iterations=raw.get("iterations"),
            )
        return normalize.normalize_scilab_result(
            raw,
            grid,
            engine_version=capability.version,
            settings=settings,
            execution_time_ms=elapsed_ms,
        )


class EngineRegistry:
    def __init__(self, engines: list[PowerFlowEngine]):
        self._engines = engines

    @property
    def engines(self) -> list[PowerFlowEngine]:
        return self._engines

    def info_all(self, settings: Settings = default_settings) -> list[EngineInfoResponse]:
        return [engine.info() for engine in self._engines]

    def by_name(self, name: str) -> PowerFlowEngine | None:
        for engine in self._engines:
            if engine.name == name:
                return engine
        return None

    def select(self, name: str) -> PowerFlowEngine | None:
        """Select an engine by exact name; unavailable engines resolve to None."""
        engine = self.by_name(name)
        if engine is None:
            return None
        if engine.info().available:
            return engine
        return None

    def resolve(
        self,
        requested: str | None,
        settings: Settings = default_settings,
    ) -> PowerFlowEngine:
        """Resolve a requested engine name (or the configured default / AUTO).

        - "auto" (the default): use Scilab if available and operational,
          otherwise Python. The resolved engine is always reported explicitly in
          the result — a fallback is never silent.
        - explicit name: return that engine only if available, otherwise raise.
        """
        name = requested or settings.default_engine
        if name == AUTO:
            scilab = self.by_name("scilab")
            if scilab is not None and scilab.info().available:
                return scilab
            python = self.by_name("python")
            if python is not None:
                return python
            raise InvalidEngine("No power-flow engine is available.")

        engine = self.by_name(name)
        if engine is None:
            raise InvalidEngine(f"Unknown power-flow engine '{name}'.")
        if engine.info().available:
            return engine
        raise InvalidEngine(
            f"Power-flow engine '{name}' is not available. "
            "Use 'auto' to allow fallback to the Python engine."
        )

    def default(self, default_name: str) -> PowerFlowEngine:
        """Backward-compatible helper: resolve using the given default name."""
        return self.resolve(default_name)


def build_registry() -> EngineRegistry:
    return EngineRegistry([PythonPowerFlowEngine(), ScilabPowerFlowEngine()])
