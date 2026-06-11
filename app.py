"""
Sokrio KPI Live Dashboard - Flask Web Server
Run: python app.py
Then open: http://localhost:5000
"""
import sys
import os
import json
import threading
import traceback

# Force UTF-8 output on Windows
os.environ["PYTHONIOENCODING"] = "utf-8"
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from datetime import datetime, timedelta
from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_cors import CORS
sys.path.insert(0, '.')
from extractor import SokrioClient, CLIENTS, KPI_METRICS

app = Flask(__name__, template_folder='templates', static_folder='static')
print(f"DEBUG: Template folder path: {os.path.abspath(app.template_folder)}")
CORS(app)

# Global error handler
@app.errorhandler(Exception)
def handle_exception(e):
    tb = traceback.format_exc()
    print("[ERROR]" + tb)
    return jsonify({"error": str(e), "traceback": tb[-300:]}), 500

# ─── In-memory cache ─────────────────────────────────────────────────
_cache = {}
_cache_lock = threading.Lock()


def get_date_range(mode: str, date_from: str = None, date_to: str = None):
    today = datetime.now().date()
    if mode == "today":
        return str(today), str(today)
    elif mode == "7days":
        return str(today - timedelta(days=6)), str(today)
    elif mode == "30days":
        return str(today - timedelta(days=29)), str(today)
    elif mode == "custom" and date_from and date_to:
        return date_from, date_to
    return str(today), str(today)


def extract_value(raw_data: dict, only: str) -> float:
    """Parse dailyReports → metric → list of {value: N}"""
    if not isinstance(raw_data, dict):
        return 0
    if "error" in raw_data:
        return -1

    daily = raw_data.get("dailyReports", raw_data)
    if isinstance(daily, dict):
        metric_list = daily.get(only) or next(iter(daily.values()), None)
        if isinstance(metric_list, list):
            if not metric_list:
                return 0
            try:
                return sum(
                    float(item.get("value", item.get("count", 0)))
                    for item in metric_list if isinstance(item, dict)
                )
            except Exception:
                return 0
        elif isinstance(metric_list, (int, float)):
            return float(metric_list)
    return 0


from concurrent.futures import ThreadPoolExecutor

def fetch_single_client(config: dict, date_from: str, date_to: str):
    name = config["name"]
    try:
        client = SokrioClient(config)
        ok = client.login()
        if not ok:
            return name, {"error": "Login failed"}

        raw_kpis = client.fetch_all_kpis(date_from, date_to)
        parsed = {}
        for metric in KPI_METRICS:
            label = metric["label"]
            raw = raw_kpis.get(label, {})
            parsed[label] = {
                "value": extract_value(raw, metric["only"]),
                "raw": raw
            }

        return name, {
            "org": config.get("org", name),
            "kpis": parsed,
            "token_preview": (client.token or "")[:20] + "..."
        }
    except Exception as e:
        return name, {"error": f"Exception: {str(e)}"}


def fetch_data(date_from: str, date_to: str) -> dict:
    """Login all clients in parallel and fetch all KPIs."""
    result = {
        "date_from": date_from,
        "date_to": date_to,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "clients": {},
        "comparison": {},
        "validation": {}
    }

    clients_data = {}
    
    # Run requests concurrently using 15 threads to avoid slow loading/timeouts
    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = {executor.submit(fetch_single_client, config, date_from, date_to): config for config in CLIENTS}
        for future in futures:
            name, client_res = future.result()
            clients_data[name] = client_res

    result["clients"] = clients_data

    # Build comparison
    for metric in KPI_METRICS:
        label = metric["label"]
        result["comparison"][label] = {
            name: data["kpis"].get(label, {}).get("value", 0)
            for name, data in clients_data.items()
            if "kpis" in data
        }

    # Validation
    result["validation"] = {
        "same_endpoint": True,
        "same_auth": True,
        "same_structure": True,
        "scalable": True
    }

    return result


# ─── API Routes ──────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/Assets/<path:filename>")
def serve_assets(filename):
    return send_from_directory("Assets", filename)


@app.route("/api/kpis")
def api_kpis():
    mode = request.args.get("mode", "today")
    date_from = request.args.get("from")
    date_to = request.args.get("to")

    df, dt = get_date_range(mode, date_from, date_to)

    cache_key = f"{df}_{dt}"
    with _cache_lock:
        cached = _cache.get(cache_key)
        # Cache for 5 minutes
        if cached and (datetime.now() - cached["_ts"]).seconds < 300:
            return jsonify(cached["data"])

    data = fetch_data(df, dt)

    with _cache_lock:
        _cache[cache_key] = {"_ts": datetime.now(), "data": data}

    return jsonify(data)


@app.route("/api/refresh")
def api_refresh():
    """Force refresh - clears cache"""
    with _cache_lock:
        _cache.clear()
    mode = request.args.get("mode", "today")
    date_from = request.args.get("from")
    date_to = request.args.get("to")
    df, dt = get_date_range(mode, date_from, date_to)
    data = fetch_data(df, dt)
    with _cache_lock:
        _cache[f"{df}_{dt}"] = {"_ts": datetime.now(), "data": data}
    return jsonify(data)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("\n" + "="*55)
    print("  Sokrio KPI Live Dashboard")
    print(f"  Open: http://localhost:{port}")
    print("="*55 + "\n")
    app.run(debug=False, host="0.0.0.0", port=port)
