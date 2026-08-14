from enum import Enum


class BusType(str, Enum):
    SLACK = "SLACK"
    PV = "PV"
    PQ = "PQ"


class GeneratorType(str, Enum):
    CONVENTIONAL = "CONVENTIONAL"
    SOLAR = "SOLAR"
    WIND = "WIND"
    STORAGE = "STORAGE"


class StorageState(str, Enum):
    IDLE = "IDLE"
    CHARGING = "CHARGING"
    DISCHARGING = "DISCHARGING"


class BusStatus(str, Enum):
    NORMAL = "NORMAL"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class LineStatus(str, Enum):
    NORMAL = "NORMAL"
    WARNING = "WARNING"
    OVERLOADED = "OVERLOADED"
