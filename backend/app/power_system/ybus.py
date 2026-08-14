from dataclasses import dataclass

import numpy as np

from app.domain.models import GridModel


@dataclass
class YBus:
    matrix: np.ndarray
    bus_index: dict[str, int]


def build_ybus(grid: GridModel) -> YBus:
    n = len(grid.buses)
    bus_index = {bus.id: i for i, bus in enumerate(grid.buses)}
    y = np.zeros((n, n), dtype=complex)

    for line in grid.lines:
        i = bus_index[line.from_bus]
        j = bus_index[line.to_bus]
        series = 1.0 / complex(line.resistance, line.reactance)
        shunt = complex(0.0, line.susceptance / 2.0)

        y[i, i] += series + shunt
        y[j, j] += series + shunt
        y[i, j] -= series
        y[j, i] -= series

    return YBus(matrix=y, bus_index=bus_index)
