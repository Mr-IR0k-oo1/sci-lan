from fastapi import APIRouter
from app.scilab.capability import get_capability

router = APIRouter(tags=["health"])

@router.get("/health")
async def health_check():
    scilab_avail = get_capability().available
    return {
        "status": "healthy",
        "version": "0.1.0",
        "python_engine": True,
        "scilab_engine": scilab_avail
    }
