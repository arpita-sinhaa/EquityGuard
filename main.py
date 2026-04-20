from fastapi import FastAPI
from routes.bias_map import router as bias_map_router
from routes.report import router as report_router
from routes.timeline import router as timeline_router



app = FastAPI(
    title="EquityGuard API",
    version="1.0"
)
app.include_router(timeline_router)

app.include_router(report_router)

app.include_router(bias_map_router, prefix="/api/v1")