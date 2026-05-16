import re

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response, StreamingResponse

from backend.cache import get_result
from csv_report import generate_corrected_csv, generate_csv_report
from pdf_report import generate_pdf_report

router = APIRouter()


def _safe_filename(company_name: str, suffix: str) -> str:
    if not company_name:
        return f"gtin_{suffix}"
    clean = re.sub(r"[^a-zA-Z0-9_\-]", "", company_name.replace(" ", "_"))
    return f"{clean}_{suffix}" if clean else f"gtin_{suffix}"


@router.get("/csv/{token}")
def download_csv_report(token: str, company_name: str = "") -> Response:
    entry = get_result(token)
    if entry is None:
        raise HTTPException(404, "Validation result expired or not found.")

    csv_string = generate_csv_report(entry.batch_result)
    filename = _safe_filename(company_name, "report.csv")
    return Response(
        content=csv_string,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/corrected/{token}")
def download_corrected_csv(token: str, company_name: str = "") -> Response:
    entry = get_result(token)
    if entry is None:
        raise HTTPException(404, "Validation result expired or not found.")

    csv_string = generate_corrected_csv(entry.batch_result)
    filename = _safe_filename(company_name, "corrected.csv")
    return Response(
        content=csv_string,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/pdf/{token}")
def download_pdf_report(token: str, company_name: str = "") -> StreamingResponse:
    entry = get_result(token)
    if entry is None:
        raise HTTPException(404, "Validation result expired or not found.")

    pdf_buffer = generate_pdf_report(entry.batch_result, company_name)
    filename = _safe_filename(company_name, "report.pdf")
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
