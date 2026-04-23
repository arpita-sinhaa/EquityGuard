from fastapi import APIRouter
from fastapi.responses import FileResponse

from services.report_service import build_report_data, generate_pdf

router = APIRouter(prefix="/report", tags=["report"])


@router.get("/generate")
async def generate():

    data = await build_report_data()

    file_path = generate_pdf(data)

    return FileResponse(
        path=file_path,
        media_type='application/pdf',
        filename="EquityGuard_Report.pdf"
    )