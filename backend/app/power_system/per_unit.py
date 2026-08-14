def power_to_per_unit(value_mw: float, base_mva: float) -> float:
    return value_mw / base_mva


def power_from_per_unit(value_pu: float, base_mva: float) -> float:
    return value_pu * base_mva


def voltage_to_per_unit(value_kv: float, base_kv: float) -> float:
    return value_kv / base_kv


def voltage_from_per_unit(value_pu: float, base_kv: float) -> float:
    return value_pu * base_kv
