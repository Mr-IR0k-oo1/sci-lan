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


class SeverityLevel(str, Enum):
    NORMAL = "NORMAL"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class VoltageClass(str, Enum):
    NORMAL = "NORMAL"
    UNDER_VOLTAGE = "UNDER_VOLTAGE"
    OVER_VOLTAGE = "OVER_VOLTAGE"


class StressLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IssueCategory(str, Enum):
    VOLTAGE_STRESS = "VOLTAGE_STRESS"
    TRANSMISSION_STRESS = "TRANSMISSION_STRESS"
    GENERATION_BALANCE = "GENERATION_BALANCE"
    RENEWABLE_IMPACT = "RENEWABLE_IMPACT"


class GenerationDetection(str, Enum):
    GENERATION_INSUFFICIENT = "GENERATION_INSUFFICIENT"
    GENERATOR_AT_LIMIT = "GENERATOR_AT_LIMIT"
    EXCESS_GENERATION = "EXCESS_GENERATION"
    IMBALANCED_SYSTEM = "IMBALANCED_SYSTEM"


class ImpactLevel(str, Enum):
    POSITIVE = "POSITIVE"
    NEUTRAL = "NEUTRAL"
    NEGATIVE = "NEGATIVE"
    HIGH_RISK = "HIGH_RISK"


class RecommendationPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ConfidenceLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
