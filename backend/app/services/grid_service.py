import json
import uuid

from app.core.exceptions import GridNotFound
from app.domain.models import GridModel

_storage: dict[str, GridModel] = {}


def create_grid(grid: GridModel) -> str:
    grid_id = grid.grid_id or uuid.uuid4().hex[:8]
    if grid_id not in _storage:
        _storage[grid_id] = grid.model_copy(update={"grid_id": grid_id})
    return grid_id


def get_grid(grid_id: str) -> GridModel:
    if grid_id not in _storage:
        raise GridNotFound(grid_id)
    return _storage[grid_id]


def list_grids() -> list[GridModel]:
    return list(_storage.values())


def load_sample_grid(path: str) -> str:
    with open(path) as handle:
        payload = json.load(handle)
    return create_grid(GridModel.model_validate(payload))


def clear_storage() -> None:
    _storage.clear()
