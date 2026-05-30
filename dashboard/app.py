import os
import json
from pathlib import Path
from flask import Flask, render_template, jsonify

app = Flask(__name__)

CHANNEL_CONFIG_FILE = Path(__file__).parent.parent / "channel_config.json"
ANALYSIS_LOG_FILE = Path(__file__).parent.parent / "analysis_log.json"


def load_channel_config():
    if CHANNEL_CONFIG_FILE.exists():
        with open(CHANNEL_CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}


def load_analysis_log():
    if ANALYSIS_LOG_FILE.exists():
        with open(ANALYSIS_LOG_FILE, "r") as f:
            return json.load(f)
    return []


def save_analysis_log(entry: dict):
    log = load_analysis_log()
    log.insert(0, entry)
    log = log[:100]
    with open(ANALYSIS_LOG_FILE, "w") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)


@app.route("/")
def index():
    config = load_channel_config()
    log = load_analysis_log()
    return render_template("index.html", config=config, log=log)


@app.route("/api/stats")
def stats():
    log = load_analysis_log()
    total = len(log)
    if total == 0:
        return jsonify({
            "total": 0, "avg_score": 0,
            "high_risk": 0, "medium_risk": 0, "low_risk": 0
        })

    scores = [e.get("score", 0) for e in log]
    avg_score = sum(scores) / total
    high_risk = sum(1 for s in scores if s >= 70)
    medium_risk = sum(1 for s in scores if 30 <= s < 70)
    low_risk = sum(1 for s in scores if s < 30)

    return jsonify({
        "total": total,
        "avg_score": round(avg_score, 1),
        "high_risk": high_risk,
        "medium_risk": medium_risk,
        "low_risk": low_risk,
    })


@app.route("/api/log")
def api_log():
    log = load_analysis_log()
    return jsonify(log)


def run_dashboard():
    port = int(os.getenv("DASHBOARD_PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
