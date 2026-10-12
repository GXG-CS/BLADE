"""HTTP access to the Jev API: endpoint, model, request hashing and one request with retries."""
import hashlib
import json
import time
import urllib.error
import urllib.request

ENDPOINT = "https://api.typesafe.ai/v1/systemone"
MODEL = "jev-1.13.0"
PRICE_PER_MILLION = 0.042  # USD per million input tokens; output is free


def canonical(obj) -> str:
    """Canonical JSON of a request (sorted keys, no whitespace)."""
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(obj) -> str:
    """SHA-256 of the canonical request: the cache key."""
    return hashlib.sha256(canonical(obj).encode()).hexdigest()


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def call_api(payload: dict, key: str) -> dict:
    """One request, retried once on a transient HTTP status. Returns {"response": ... or None, "attempts": [...]}."""
    attempts = []
    for retry in range(2):
        started = time.monotonic()
        req = urllib.request.Request(
            ENDPOINT, data=json.dumps(payload, ensure_ascii=False).encode(),
            headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.build_opener(_NoRedirect).open(req, timeout=45) as response:
                data = json.load(response)
            attempts.append({"status": 200, "elapsed_s": round(time.monotonic() - started, 3)})
            return {"response": data, "attempts": attempts}
        except urllib.error.HTTPError as exc:
            # Headers, credentials and provider error bodies are never logged.
            attempts.append({"status": exc.code, "elapsed_s": round(time.monotonic() - started, 3)})
            if exc.code not in (429, 500, 502, 503, 504, 529):
                break
        except Exception as exc:
            attempts.append({"error_type": type(exc).__name__, "elapsed_s": round(time.monotonic() - started, 3)})
            break  # a timed-out request may still be billed; do not resend it blindly
        if retry == 0:
            time.sleep(2)
    return {"response": None, "attempts": attempts}
