from pydantic import BaseModel, Field

from app.domain.enums import BusType, GeneratorType

_EMPTY = Field(default_factory=list)


class Bus(BaseModel):
    id: str
    name: str = ""
    type: BusType = BusType.PQ
    base_voltage: float = 138.0
    voltage_magnitude: float = 1.0
    voltage_angle: float = 0.0


class TransmissionLine(BaseModel):
    id: str
    name: str = ""
    from_bus: str
    to_bus: str
    resistance: float
    reactance: float
    susceptance: float = 0.0
    thermal_limit: float


class Generator(BaseModel):
    id: str
    name: str = ""
    bus_id: str
    type: GeneratorType = GeneratorType.CONVENTIONAL
    active_power: float = 0.0
    reactive_power: float = 0.0
    active_power_min: float = 0.0
    active_power_max: float = 1000.0
    reactive_power_min: float = -1000.0
    reactive_power_max: float = 1000.0


class Load(BaseModel):
    id: str
    name: str = ""
    bus_id: str
    active_power: float
    reactive_power: float = 0.0


class GridModel(BaseModel):
    grid_id: str = ""
    name: str = "Unnamed Grid"
    base_mva: float = 100.0
    buses: list[Bus] = _EMPTY
    lines: list[TransmissionLine] = _EMPTY
    generators: list[Generator] = _EMPTY
    loads: list[Load] = _EMPTY
