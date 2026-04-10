from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
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


def _extract_multiline_json_env(env_path: Path, key: str) -> str | None:
    if not env_path.exists():
        return None

    content = env_path.read_text(encoding="utf-8")
    marker = f"{key}="
    start = content.find(marker)
    if start == -1:
        return None

    json_start = content.find("{", start)
    if json_start == -1:
        return None

    depth = 0
    in_string = False
    escape = False

    for idx in range(json_start, len(content)):
        char = content[idx]

        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return content[json_start: idx + 1].strip()

    return None


def _load_google_credentials_json(env_path: Path) -> bool:
    raw_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")

    def _try_parse(value: str | None) -> dict | None:
        if not value:
            return None
        try:
            parsed_value = json.loads(value)
            if isinstance(parsed_value, dict):
                return parsed_value
        except Exception:
            return None
        return None

    parsed = _try_parse(raw_json)

    # Dotenv commonly breaks multiline JSON and may set this variable to only "{".
    # If parse fails, recover by extracting the full JSON block directly from .env.
    if parsed is None:
        extracted = _extract_multiline_json_env(env_path, "GOOGLE_APPLICATION_CREDENTIALS_JSON")
        parsed = _try_parse(extracted)
        if parsed is not None:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS_JSON"] = json.dumps(parsed)
            return True

    if parsed is None:
        if raw_json:
            print("Invalid GOOGLE_APPLICATION_CREDENTIALS_JSON: could not parse JSON credentials")
        return False

    os.environ["GOOGLE_APPLICATION_CREDENTIALS_JSON"] = json.dumps(parsed)
    return True


env_path = Path(__file__).resolve().parent.parent / ".env"
if load_dotenv is not None:
    load_dotenv(dotenv_path=env_path)
else:
    _load_env_fallback(env_path)

print("Loaded .env from:", env_path)
has_json_credentials = _load_google_credentials_json(env_path)
print("JSON CREDENTIALS LOADED:", has_json_credentials)

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
