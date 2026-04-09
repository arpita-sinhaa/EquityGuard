from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

app = FastAPI(title="EquityGuard API", description="Bias Detection and Audit Platform")


def _load_env_fallback(env_path: Path) -> None:
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, raw = stripped.split("=", 1)
        key = key.strip()
        if key and key not in os.environ:
            os.environ[key] = raw.strip().strip('"').strip("'")


env_path = Path(__file__).resolve().parent.parent / ".env"
if load_dotenv is not None:
    load_dotenv(dotenv_path=env_path)
else:
    _load_env_fallback(env_path)

print("Loaded .env from:", env_path)

def _resolve_google_credentials() -> str | None:
    current = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if current:
        return current

    # Allow an alternate var name in .env for readability.
    alt = os.getenv("GOOGLE_CREDENTIALS_PATH")
    if alt:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = alt
        return alt

    # Optional local convention: backend/credentials/service-account.json
    fallback = Path(__file__).resolve().parent.parent / "credentials" / "service-account.json"
    if fallback.exists():
        resolved = str(fallback)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = resolved
        return resolved

    return None


credential_path = _resolve_google_credentials()
print("CREDENTIAL PATH:", credential_path)
if credential_path:
    print("CREDENTIAL FILE EXISTS:", Path(credential_path).exists())

# Allow all origins for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.routes import citizen, audit

app.include_router(citizen.router, tags=["Citizen"])
app.include_router(audit.router, tags=["Organization Audit"])

@app.get("/")
def root():
    return {"message": "EquityGuard API is running. Check /docs for endpoints."}
