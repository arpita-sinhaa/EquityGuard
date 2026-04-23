from fastapi import APIRouter, UploadFile, File
from services.timeline_service import process_and_store, get_timeline_data

router = APIRouter(prefix="/timeline", tags=["timeline"])


@router.post("/upload")
async def upload_batch(file: UploadFile = File(...)):
    result = await process_and_store(file)
    return {"rows_inserted": result}


@router.get("/data")
def get_data():
    return get_timeline_data()