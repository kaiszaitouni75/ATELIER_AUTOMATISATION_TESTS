"""
tests.py — Suite de tests pour l'API Frankfurter (taux de change).
Chaque test retourne un dict :
  { name, status ("PASS"|"FAIL"|"ERROR"), latency_ms, message }
"""
from tester.client import get

BASE = "https://api.frankfurter.app"


def _make_result(name: str, res: dict, ok: bool, message: str) -> dict:
    if res["error"]:
        return {"name": name, "status": "ERROR",
                "latency_ms": res["latency_ms"], "message": res["error"]}
    return {
        "name": name,
        "status": "PASS" if ok else "FAIL",
        "latency_ms": res["latency_ms"],
        "message": message,
    }


# ── A. Tests Contrat (fonctionnels) ──────────────────────────────────────────

def test_latest_http200():
    """HTTP 200 sur /latest"""
    res = get(f"{BASE}/latest?from=EUR")
    ok = res["status_code"] == 200
    return _make_result("GET /latest → HTTP 200", res,
                        ok, f"HTTP {res['status_code']}")


def test_latest_content_type_json():
    """Content-Type contient application/json"""
    import requests as _req
    import time
    start = time.perf_counter()
    try:
        r = _req.get(f"{BASE}/latest?from=EUR", timeout=5)
        lat = int((time.perf_counter() - start) * 1000)
        ct = r.headers.get("Content-Type", "")
        ok = "json" in ct
        return {"name": "GET /latest → Content-Type: JSON",
                "status": "PASS" if ok else "FAIL",
                "latency_ms": lat,
                "message": f"Content-Type: {ct}"}
    except Exception as e:
        return {"name": "GET /latest → Content-Type: JSON",
                "status": "ERROR", "latency_ms": 0, "message": str(e)}


def test_latest_fields():
    """Champs 'base', 'date', 'rates' présents"""
    res = get(f"{BASE}/latest?from=EUR")
    d = res["json"] or {}
    missing = [f for f in ("base", "date", "rates") if f not in d]
    ok = len(missing) == 0
    return _make_result("GET /latest → champs base/date/rates présents", res,
                        ok, f"manquants: {missing}" if missing else "Tous présents")


def test_latest_base_is_eur():
    """Champ 'base' == 'EUR'"""
    res = get(f"{BASE}/latest?from=EUR")
    d = res["json"] or {}
    ok = d.get("base") == "EUR"
    return _make_result("GET /latest → base == 'EUR'", res,
                        ok, f"base={d.get('base','N/A')}")


def test_latest_rates_types():
    """Tous les taux sont des float > 0"""
    res = get(f"{BASE}/latest?from=EUR")
    d = res["json"] or {}
    rates = d.get("rates", {})
    invalid = {k: v for k, v in rates.items()
               if not isinstance(v, (int, float)) or v <= 0}
    ok = len(invalid) == 0 and len(rates) > 0
    return _make_result("GET /latest → tous les taux sont float > 0", res,
                        ok, f"{len(rates)} taux, invalides: {list(invalid.keys())[:3]}")


def test_latest_usd_present():
    """Le taux USD est présent dans les rates EUR"""
    res = get(f"{BASE}/latest?from=EUR")
    d = res["json"] or {}
    ok = "USD" in d.get("rates", {})
    return _make_result("GET /latest → taux USD présent", res,
                        ok, f"USD={'présent' if ok else 'absent'}")


def test_convert_eur_to_usd():
    """Conversion EUR→USD : montant retourné > 0"""
    res = get(f"{BASE}/latest?amount=100&from=EUR&to=USD")
    d = res["json"] or {}
    usd = d.get("rates", {}).get("USD")
    ok = isinstance(usd, (int, float)) and usd > 0
    return _make_result("GET /latest?amount=100&from=EUR&to=USD → montant > 0", res,
                        ok, f"100 EUR = {usd} USD")


def test_historical_date():
    """Données historiques — date fixe 2024-01-15"""
    res = get(f"{BASE}/2024-01-15?from=EUR")
    d = res["json"] or {}
    ok = res["status_code"] == 200 and d.get("date") == "2024-01-15"
    return _make_result("GET /2024-01-15 → date correcte dans la réponse", res,
                        ok, f"date={d.get('date','N/A')}")


def test_currencies_list():
    """GET /currencies → dict non vide avec codes 3 lettres"""
    res = get(f"{BASE}/currencies")
    d = res["json"] or {}
    ok = (res["status_code"] == 200
          and isinstance(d, dict)
          and len(d) > 10
          and all(len(k) == 3 for k in d.keys()))
    return _make_result("GET /currencies → dict de devises valide", res,
                        ok, f"{len(d)} devises")


# ── B. Robustesse & erreurs attendues ────────────────────────────────────────

def test_invalid_currency_404():
    """Devise inexistante → code 404 ou 422"""
    res = get(f"{BASE}/latest?from=ZZZ")
    ok = res["status_code"] in (404, 422, 400)
    return _make_result("GET /latest?from=ZZZ → erreur 4xx attendue", res,
                        ok, f"HTTP {res['status_code']}")


def test_invalid_date_404():
    """Date invalide → code 404 ou 422"""
    res = get(f"{BASE}/9999-99-99")
    ok = res["status_code"] in (404, 422, 400)
    return _make_result("GET /9999-99-99 → erreur 4xx attendue", res,
                        ok, f"HTTP {res['status_code']}")


def test_timeout_resilience():
    """Timeout strict à 3s — doit répondre dans les temps"""
    res = get(f"{BASE}/latest?from=EUR", timeout=3.0)
    ok = res["error"] is None and res["latency_ms"] < 3000
    return _make_result("GET /latest → répond en < 3s (timeout resilience)", res,
                        ok, f"{res['latency_ms']} ms | error={res['error']}")


# ── Registre complet ─────────────────────────────────────────────────────────

ALL_TESTS = [
    test_latest_http200,
    test_latest_content_type_json,
    test_latest_fields,
    test_latest_base_is_eur,
    test_latest_rates_types,
    test_latest_usd_present,
    test_convert_eur_to_usd,
    test_historical_date,
    test_currencies_list,
    test_invalid_currency_404,
    test_invalid_date_404,
    test_timeout_resilience,
]
