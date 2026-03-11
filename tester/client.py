"""
client.py — Wrapper HTTP avec timeout, retry, mesure de latence et gestion 429/5xx.
"""
import time
import requests


def get(url: str, timeout: float = 5.0, retries: int = 1) -> dict:
    """
    Effectue un GET avec timeout strict et 1 retry max.
    Gère les 429 (rate-limit) avec backoff et les 5xx avec retry.

    Retourne un dict :
        {
          "status_code": int | None,
          "json":        dict | list | None,
          "latency_ms":  int,
          "error":       str | None,   # message si exception
          "retried":     bool,
        }
    """
    attempt = 0
    retried = False

    while attempt <= retries:
        start = time.perf_counter()
        try:
            resp = requests.get(url, timeout=timeout)
            latency_ms = int((time.perf_counter() - start) * 1000)

            # Rate-limit : backoff 2s puis retry
            if resp.status_code == 429 and attempt < retries:
                retry_after = int(resp.headers.get("Retry-After", 2))
                time.sleep(retry_after)
                attempt += 1
                retried = True
                continue

            # 5xx : retry immédiat
            if resp.status_code >= 500 and attempt < retries:
                attempt += 1
                retried = True
                continue

            try:
                data = resp.json()
            except Exception:
                data = None

            return {
                "status_code": resp.status_code,
                "json": data,
                "latency_ms": latency_ms,
                "error": None,
                "retried": retried,
            }

        except requests.exceptions.Timeout:
            latency_ms = int((time.perf_counter() - start) * 1000)
            if attempt < retries:
                attempt += 1
                retried = True
                continue
            return {
                "status_code": None,
                "json": None,
                "latency_ms": latency_ms,
                "error": f"Timeout après {timeout}s",
                "retried": retried,
            }

        except Exception as exc:
            latency_ms = int((time.perf_counter() - start) * 1000)
            return {
                "status_code": None,
                "json": None,
                "latency_ms": latency_ms,
                "error": str(exc),
                "retried": retried,
            }
