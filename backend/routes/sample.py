from fastapi import APIRouter

from backend.schemas.responses import SampleDataResponse
from sample_data import SAMPLE_DATA, SAMPLE_DESCRIPTION

router = APIRouter()


@router.get("/sample")
def get_sample_data() -> SampleDataResponse:
    return SampleDataResponse(csv=SAMPLE_DATA, description=SAMPLE_DESCRIPTION)


@router.get("/retailers")
def get_retailers() -> dict[str, dict]:
    from gtin_core import RETAILER_PROFILES

    return {
        name: {
            "description": profile["description"],
            "requires_hierarchy": profile["requires_hierarchy"],
            "requires_case_gtin": profile["requires_case_gtin"],
            "notes": profile.get("notes", ""),
        }
        for name, profile in RETAILER_PROFILES.items()
    }
