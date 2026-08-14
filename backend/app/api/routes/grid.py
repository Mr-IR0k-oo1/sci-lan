from fastapi import APIRouter, status

from app.domain.models import GridModel
from app.schemas.grid import GridResponse, ValidationResponse
from app.services import grid_service, validation_service

router = APIRouter(tags=["grids"])


@router.post("/grids", response_model=GridResponse, status_code=status.HTTP_201_CREATED)
def create_grid(grid: GridModel) -> GridResponse:
    grid_id = grid_service.create_grid(grid)
    return grid_service.get_grid(grid_id)


@router.get("/grids/{grid_id}", response_model=GridResponse)
def get_grid(grid_id: str) -> GridResponse:
    return grid_service.get_grid(grid_id)


@router.post("/grids/{grid_id}/validate", response_model=ValidationResponse)
def validate_grid(grid_id: str) -> ValidationResponse:
    grid = grid_service.get_grid(grid_id)
    issues = validation_service.validate_grid(grid)
    return ValidationResponse(valid=not issues, errors=issues)
