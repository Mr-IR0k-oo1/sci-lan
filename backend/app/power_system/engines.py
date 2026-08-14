from abc import ABC, abstractmethod

from app.core.config import Settings
from app.core.exceptions import InvalidEngine, PowerFlowDidNotConverge
from app.domain.models import GridModel
from app.power_system.power_flow import solve_power_flow
from app.power_system.results import PowerFlowResult, build_power_flow_result
from app.power_system.ybus import build_ybus
from app.scilab.runner import ScilabRunner, detect_scilab
from app.schemas.analysis import EngineInfoResponse


class PowerFlowEngine(ABC):
    name: str = ""

    @abstractmethod
    def info(self) -> EngineInfoResponse:
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
        import platform

        return EngineInfoResponse(
            name=self.name,
            available=True,
            version=platform.python_version(),
            status="available",
        )

    def run(
        self,
        grid: GridModel,
        tolerance: float,
        max_iterations: int,
        settings: Settings,
    ) -> PowerFlowResult:
        ybus = build_ybus(grid)
        solution = solve_power_flow(grid, ybus, tolerance, max_iterations)
        if not solution.converged:
            raise PowerFlowDidNotConverge(
                f"Power flow did not converge after {solution.iterations} "
                f"iterations (max mismatch {solution.max_mismatch:.3e}).",
                max_mismatch=solution.max_mismatch,
                iterations=solution.iterations,
            )
        return build_power_flow_result(grid, ybus, solution, self.name, settings)


class ScilabPowerFlowEngine(PowerFlowEngine):
    name = "scilab"

    def info(self) -> EngineInfoResponse:
        capability = detect_scilab()
        return EngineInfoResponse(
            name=self.name,
            available=capability.available,
            version=capability.version,
            status="available" if capability.available else "unavailable",
        )

    def run(
        self,
        grid: GridModel,
        tolerance: float,
        max_iterations: int,
        settings: Settings,
    ) -> PowerFlowResult:
        return ScilabRunner().solve(grid, tolerance, max_iterations, settings)


class EngineRegistry:
    def __init__(self, engines: list[PowerFlowEngine]):
        self._engines = engines

    @property
    def engines(self) -> list[PowerFlowEngine]:
        return self._engines

    def info_all(self) -> list[EngineInfoResponse]:
        return [engine.info() for engine in self._engines]

    def select(self, name: str) -> PowerFlowEngine | None:
        for engine in self._engines:
            if engine.name == name:
                return engine if engine.info().available else None
        return None

    def default(self, default_name: str) -> PowerFlowEngine:
        selected = self.select(default_name)
        if selected is not None:
            return selected
        for engine in self._engines:
            if engine.info().available:
                return engine
        raise InvalidEngine("No power-flow engine is available.")


def build_registry() -> EngineRegistry:
    return EngineRegistry([PythonPowerFlowEngine(), ScilabPowerFlowEngine()])
