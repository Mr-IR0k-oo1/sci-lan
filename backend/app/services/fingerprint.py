import hashlib
import json
from typing import Any

from app.domain.models import GridModel


def compute_input_hash(
    grid: GridModel,
    scenario_modifications: dict[str, Any] | None = None,
    engine: str | None = None,
) -> str:
    """
    Computes a deterministic hash representing the input state of an analysis.
    This includes the grid topology and parameters, any scenario modifications,
    and the selected engine.
    """
    state: dict[str, Any] = {
        "grid": grid.model_dump(exclude={"name"}),  # Name changes shouldn't affect analysis
        "scenario": scenario_modifications or {},
        "engine": engine or "auto",
    }
    
    # Sort keys to ensure deterministic JSON serialization
    serialized = json.dumps(state, sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
