"""
runner.py — Exécute la suite de tests et calcule les métriques QoS.
"""
import statistics
from datetime import datetime, timezone
from tester.tests import ALL_TESTS


def run_all() -> dict:
    """
    Exécute tous les tests et retourne un run complet :
    {
      "api": str,
      "timestamp": str (ISO 8601),
      "summary": { passed, failed, errors, total,
                   error_rate, availability,
                   latency_ms_avg, latency_ms_p95 },
      "tests": [ {name, status, latency_ms, message}, … ]
    }
    """
    results = []
    for fn in ALL_TESTS:
        try:
            results.append(fn())
        except Exception as exc:
            results.append({
                "name": getattr(fn, "__name__", "unknown"),
                "status": "ERROR",
                "latency_ms": 0,
                "message": f"Exception inattendue : {exc}",
            })

    passed  = sum(1 for r in results if r["status"] == "PASS")
    failed  = sum(1 for r in results if r["status"] == "FAIL")
    errors  = sum(1 for r in results if r["status"] == "ERROR")
    total   = len(results)

    latencies = [r["latency_ms"] for r in results if r["latency_ms"] > 0]
    avg_ms = int(statistics.mean(latencies)) if latencies else 0
    p95_ms = int(statistics.quantiles(latencies, n=100)[94]) if len(latencies) >= 2 else (latencies[0] if latencies else 0)

    error_rate   = round((failed + errors) / total, 3) if total else 0
    availability = round(passed / total * 100, 1) if total else 0

    return {
        "api": "Frankfurter",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
        "summary": {
            "passed":          passed,
            "failed":          failed,
            "errors":          errors,
            "total":           total,
            "error_rate":      error_rate,
            "availability":    availability,
            "latency_ms_avg":  avg_ms,
            "latency_ms_p95":  p95_ms,
        },
        "tests": results,
    }
