from typing import List
from fastapi import APIRouter, HTTPException

from app.schemas.case_study import CaseStudyMetadata, CaseStudyDetails, CaseStudyRunResponse
from app.services import case_study as case_study_service

router = APIRouter(tags=["case_studies"])

@router.get("/case-studies", response_model=List[CaseStudyMetadata])
def list_case_studies():
    return case_study_service.list_case_studies()

@router.get("/case-studies/{case_id}", response_model=CaseStudyDetails)
def get_case_study(case_id: str):
    case = case_study_service.get_case_study(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case study not found")
    return case

@router.post("/case-studies/{case_id}/run", response_model=CaseStudyRunResponse)
def run_case_study(case_id: str):
    try:
        return case_study_service.run_case_study(case_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
