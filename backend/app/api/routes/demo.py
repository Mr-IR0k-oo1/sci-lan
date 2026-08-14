"""Demo reset endpoint — clears all in-memory state derived from case-study runs
and reloads the sample grids so every demo starts from a clean, known baseline.

The source case-study JSON files on disk are never modified.
"""

from fastapi import APIRouter

from app.core.logging import logger
from app.services import grid_service
from app.services.analysis_history_service import clear_analyses
from app.core.config import settings
import os

router = APIRouter(tags=["demo"])


@router.post("/demo/reset", summary="Reset demo state to baseline")
def reset_demo() -> dict:
    """Clear all in-memory analysis records and reload the bundled sample grids.

    This operation is:
    - **Deterministic**: the resulting in-memory state is identical after every call.
    - **Non-destructive to source data**: case-study JSON files are never mutated.
    - **Safe to call repeatedly**: idempotent.
    """
    # 1. Clear analysis history (stress records, mitigations, etc.)
    clear_analyses()

    # 2. Clear grid store and reload bundled grids
    grid_service.clear_storage()

    loaded: list[str] = []

    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    examples_dir = os.path.join(here, "..", "..", "examples")

    for filename in ("sample_grid.json", "demo_grid.json"):
        path = os.path.join(examples_dir, filename)
        if os.path.exists(path):
            grid_id = grid_service.load_sample_grid(path)
            loaded.append(grid_id)

    logger.info(f"Demo reset complete. Loaded grids: {loaded}")

    return {
        "status": "reset",
        "message": "Demo state cleared. Sample grids reloaded.",
        "grids_loaded": loaded,
    }
