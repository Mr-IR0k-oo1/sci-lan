import os

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routes import analysis, grid, scenarios
from app.core.config import settings
from app.core.exceptions import (
    GridFlexError,
    GridNotFound,
    InvalidEngine,
    InvalidGrid,
    PowerFlowDidNotConverge,
    ScilabUnavailable,
)
from app.services import grid_service

app = FastAPI(
    title="GridFlex API",
    description="Interactive renewable energy integration and grid stability planning tool.",
    version="0.1.0",
)

app.include_router(grid.router, prefix="/api/v1")
app.include_router(analysis.router, prefix="/api/v1")
app.include_router(scenarios.router, prefix="/api/v1")


@app.on_event("startup")
def _load_example_grids() -> None:
    grid_service.load_sample_grid(settings.sample_grid_path)
    demo_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "examples",
        "demo_grid.json",
    )
    grid_service.load_sample_grid(demo_path)


def _error_response(status_code: int, code: str, message: str, extra: dict | None = None) -> JSONResponse:
    payload: dict = {"detail": {"code": code, "message": message}}
    if extra:
        payload["detail"].update(extra)
    return JSONResponse(status_code=status_code, content=payload)


@app.exception_handler(GridNotFound)
async def _grid_not_found(_request: Request, exc: GridNotFound) -> JSONResponse:
    return _error_response(404, "grid_not_found", str(exc))


@app.exception_handler(InvalidGrid)
async def _invalid_grid(_request: Request, exc: InvalidGrid) -> JSONResponse:
    return _error_response(
        422,
        "invalid_grid",
        str(exc),
        {"details": exc.details},
    )


@app.exception_handler(InvalidEngine)
async def _invalid_engine(_request: Request, exc: InvalidEngine) -> JSONResponse:
    return _error_response(422, "invalid_engine", str(exc))


@app.exception_handler(PowerFlowDidNotConverge)
async def _not_converged(_request: Request, exc: PowerFlowDidNotConverge) -> JSONResponse:
    return _error_response(
        409,
        "power_flow_not_converged",
        str(exc),
        {"max_mismatch": exc.max_mismatch, "iterations": exc.iterations},
    )


@app.exception_handler(ScilabUnavailable)
async def _scilab_unavailable(_request: Request, exc: ScilabUnavailable) -> JSONResponse:
    return _error_response(503, "scilab_unavailable", str(exc))


@app.exception_handler(GridFlexError)
async def _gridflex_error(_request: Request, exc: GridFlexError) -> JSONResponse:
    return _error_response(500, "internal_error", str(exc))
