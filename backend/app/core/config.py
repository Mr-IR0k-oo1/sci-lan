from dataclasses import dataclass, replace
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

    # Engine selection: "python", "scilab", or "auto".
    # "auto" prefers Scilab when it is available and operational, otherwise Python.
    default_engine: str = "auto"

    # Optional explicit Scilab executable path. When None the PATH is searched
    # for "scilab-cli" / "scilab".
    scilab_executable: str | None = None

    # Capability cache TTL in seconds (detection/health checks are expensive).
    scilab_capability_ttl_seconds: int = 300

    # Hard timeout for any Scilab subprocess invocation.
    scilab_timeout_seconds: int = 120

    @property
    def sample_grid_path(self) -> str:
        here = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(here, "..", "..", "examples", "sample_grid.json")
        
    def validate(self):
        from app.core.exceptions import InvalidConfiguration
        if self.tolerance <= 0:
            raise InvalidConfiguration("Tolerance must be positive.")
        if self.max_iterations <= 0:
            raise InvalidConfiguration("max_iterations must be positive.")
        if self.line_warning_threshold < 0 or self.line_warning_threshold > self.line_overload_threshold:
            raise InvalidConfiguration("Invalid line thresholds.")
        if self.voltage_critical_low >= self.voltage_warning_low:
            raise InvalidConfiguration("Invalid voltage low thresholds.")
        if self.voltage_critical_high <= self.voltage_warning_high:
            raise InvalidConfiguration("Invalid voltage high thresholds.")
        if self.default_engine not in ["python", "scilab", "auto"]:
            raise InvalidConfiguration(f"Invalid default_engine: {self.default_engine}")
        if self.scilab_timeout_seconds <= 0:
            raise InvalidConfiguration("scilab_timeout_seconds must be positive.")


settings = Settings()
if os.environ.get("GRIDFLEX_SCILAB_EXECUTABLE"):
    settings = replace(settings, scilab_executable=os.environ["GRIDFLEX_SCILAB_EXECUTABLE"])
if os.environ.get("GRIDFLEX_DEFAULT_ENGINE"):
    settings = replace(settings, default_engine=os.environ["GRIDFLEX_DEFAULT_ENGINE"])

settings.validate()
