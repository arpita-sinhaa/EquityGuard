from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import citizen, audit

app = FastAPI(title="EquityGuard API", description="Bias Detection and Audit Platform")

# Allow all origins for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(citizen.router, tags=["Citizen"])
app.include_router(audit.router, tags=["Organization Audit"])

@app.get("/")
def root():
    return {"message": "EquityGuard API is running. Check /docs for endpoints."}
