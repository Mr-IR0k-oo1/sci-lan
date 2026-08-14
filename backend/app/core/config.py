from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    tolerance: float = 1e-6
    max_iterations: int = 20

    line_warning_threshold: float = 80.0
    line_overload_threshold: float = 100.0

    voltage_warning_low: float = 0.95
    voltage_warning_high: float = 1.05
    voltage_critical_low: float = 0.90
    voltage_critical_high: float = 1.10

    default_engine: str = "python"

    @property
    def sample_grid_path(self) -> str:
        here = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(here, "..", "..", "examples", "sample_grid.json")


settings = Settings()
