import json
import os
import urllib.request
import urllib.error
from typing import Optional, List

# -------------------------
# CONFIG
# -------------------------
BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "meta-llama/llama-3-8b-instruct"

# -------------------------
# CORE CLIENT
# -------------------------
def _get_api_key() -> Optional[str]:
    return os.getenv("OPENROUTER_API_KEY")


def _call_openrouter(prompt: str, model: str = DEFAULT_MODEL) -> str:
    api_key = _get_api_key()
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY not set")

    url = f"{BASE_URL}/chat/completions"

    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 150
    }

    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = json.loads(response.read().decode())
            return body["choices"][0]["message"]["content"].strip()

    except urllib.error.HTTPError as e:
        details = e.read().decode("utf-8", errors="ignore")
        print(f"[OpenRouter ERROR {e.code}]: {details}")
        raise

    except Exception as e:
        print(f"[OpenRouter UNKNOWN ERROR]: {e}")
        raise


# -------------------------
# SAFE WRAPPER
# -------------------------
def _safe_generate(prompt: str) -> str:
    try:
        return _call_openrouter(prompt)
    except Exception:
        return "Explanation unavailable due to LLM service issue."


# -------------------------
# CITIZEN EXPLANATION
# -------------------------
def generate_citizen_explanation(domain: str, disparity_ratio: float, sample_size: int) -> str:
    if _get_api_key() is None:
        return (
            "This result suggests a statistical indication of bias, "
            "where this group experiences lower approval rates compared to others."
        )

    prompt = f"""
Explain this bias result simply.

Domain: {domain}
Disparity ratio: {disparity_ratio:.2f}
Sample size: {sample_size}

Write 2 short sentences.
Do not use the word discrimination.
"""

    return _safe_generate(prompt)


# -------------------------
# ORG RECOMMENDATION
# -------------------------
def generate_org_recommendation(domain: str, flagged_slices: List[dict]) -> str:
    if not flagged_slices:
        return "No statistical indications of bias detected."

    if _get_api_key() is None:
        return (
            "Focus on reviewing decision criteria and standardizing evaluation processes "
            "to reduce potential bias."
        )

    top = flagged_slices[:3]

    summary = "\n".join([
        f"{s['sex']} {s['race']} {s['age_group']} (ratio {s['disparity_ratio']:.2f})"
        for s in top
    ])

    prompt = f"""
Give a short recommendation for reducing bias in {domain}.

Flagged groups:
{summary}

Write 2 sentences only.
Do not use numbers or calculations.
"""

    return _safe_generate(prompt)