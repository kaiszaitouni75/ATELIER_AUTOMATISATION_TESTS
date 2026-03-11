"""
flask_app.py — Application Flask principale.
Routes :
  GET /            → dashboard HTML
  GET /run         → lance un run de tests, sauvegarde en SQLite, retourne JSON
  GET /runs        → historique des runs (JSON)
  GET /dashboard   → alias de /
  GET /export      → export JSON complet (bonus)
  GET /health      → état de santé rapide (bonus)
"""
import os
import sys

# Ajouter le répertoire courant au path pour les imports relatifs
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify, render_template, request
from storage import init_db, save_run, list_runs, seconds_since_last_run, export_json
from tester.runner import run_all

app = Flask(__name__, template_folder="templates")

# Initialisation de la BDD au démarrage
init_db()

# Anti-spam : intervalle minimum entre deux runs (secondes)
MIN_INTERVAL = 300  # 5 minutes


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/run")
def run_tests():
    """Lance un run complet, sauvegarde en BDD, retourne le résultat JSON."""
    # Anti-spam
    secs = seconds_since_last_run()
    if secs < MIN_INTERVAL:
        wait = int(MIN_INTERVAL - secs)
        return jsonify({
            "error": f"Anti-spam actif — prochain run dans {wait}s "
                     f"(limite : 1 run / {MIN_INTERVAL // 60} min)."
        }), 429

    result = run_all()
    save_run(result)
    return jsonify(result)


@app.route("/runs")
def get_runs():
    """Retourne l'historique des runs (50 derniers)."""
    return jsonify(list_runs(limit=50))


@app.route("/export")
def export():
    """Export JSON complet (200 derniers runs) — bonus."""
    return jsonify(export_json(limit=200))


@app.route("/health")
def health():
    """Endpoint /health : état de santé rapide — bonus."""
    runs = list_runs(limit=1)
    last = runs[0] if runs else None
    status = "ok"
    if last:
        if last["availability"] < 80:
            status = "degraded"
        if last["availability"] < 50:
            status = "critical"

    return jsonify({
        "status": status,
        "api_monitored": "Frankfurter (api.frankfurter.app)",
        "last_run": last["timestamp"] if last else None,
        "last_availability": last["availability"] if last else None,
        "last_latency_avg_ms": last["latency_avg"] if last else None,
        "total_runs_stored": len(list_runs(limit=10000)),
        "anti_spam_next_run_in_s": max(0, int(MIN_INTERVAL - seconds_since_last_run())),
    })


# ── Lancement local ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, port=5000)
