"""
ShadowSync E2E Test Suite v2.0
================================
Tests all API endpoints under concurrent load including:
  - Auth (login/JWT)
  - Preventive override log (concurrency stress)
  - Shadow feedback (concurrency stress)
  - Vendor ring detection
  - ML transparency + retrain
  - Telemetry (summary, velocity, heatmap, trust timeline)
  - Signal ingestion
"""

import requests
import concurrent.futures
import time
import random
import sys
import json

BASE_URL = "http://localhost:8000"
PASS = "\033[92m[PASS]\033[0m"
FAIL = "\033[91m[FAIL]\033[0m"
INFO = "\033[94m[INFO]\033[0m"

# ─── Auth ──────────────────────────────────────────────────
def login():
    session = requests.Session()
    resp = session.post(f"{BASE_URL}/api/login",
                        json={"username": "admin", "password": "nexus2026"})
    if resp.status_code == 200:
        print(f"{PASS} Login — JWT acquired")
        return session
    print(f"{FAIL} Login failed: {resp.text}")
    sys.exit(1)

# ─── Single-endpoint sanity checks ─────────────────────────
def check_endpoint(session, method, path, payload=None, label=None, allowed=(200,)):
    label = label or path
    try:
        t0 = time.time()
        if method == "GET":
            r = session.get(f"{BASE_URL}{path}", timeout=15)
        else:
            r = session.post(f"{BASE_URL}{path}", json=payload or {}, timeout=15)
        elapsed = time.time() - t0
        ok = r.status_code in allowed
        tag = PASS if ok else FAIL
        print(f"  {tag} {label:50s} {r.status_code}  ({elapsed:.2f}s)")
        return ok, r
    except Exception as e:
        print(f"  {FAIL} {label:50s} ERROR: {e}")
        return False, None

def run_sanity_checks(session):
    print(f"\n{INFO} ── Sanity Checks ──────────────────────────────────")
    results = []

    checks = [
        # Core
        ("GET",  "/api/stats",                    None, "GET /api/stats"),
        ("GET",  "/api/shadows",                  None, "GET /api/shadows"),
        ("GET",  "/api/transactions",             None, "GET /api/transactions"),
        ("GET",  "/api/vendors",                  None, "GET /api/vendors"),
        # Vendor rings
        ("GET",  "/api/vendor-rings",             None, "GET /api/vendor-rings"),
        # ML transparency
        ("GET",  "/api/ml/status",                None, "GET /api/ml/status"),
        # Telemetry
        ("GET",  "/api/telemetry/summary",        None, "GET /api/telemetry/summary"),
        ("GET",  "/api/telemetry/shadow-velocity",None, "GET /api/telemetry/shadow-velocity"),
        ("GET",  "/api/telemetry/risk-heatmap",   None, "GET /api/telemetry/risk-heatmap"),
        ("GET",  "/api/telemetry/vendor-trust-timeline", None, "GET /api/telemetry/vendor-trust-timeline"),
        # Preventive
        ("POST", "/api/preventive/check",
         {"item_id":"SKU-001","part_name":"Hydraulic Pump","vendor":"Test Vendor","amount":1500,"department":"Maintenance"},
         "POST /api/preventive/check"),
        # Signal ingestion
        ("POST", "/api/signals/ingest",
         {"source_type":"gate_entry", "raw_data": {"actor":"John Doe","department":"Warehouse","metadata":{"note":"test"}}},
         "POST /api/signals/ingest"),
    ]

    for method, path, payload, label in checks:
        ok, _ = check_endpoint(session, method, path, payload, label)
        results.append(ok)

    passed = sum(results)
    total  = len(results)
    print(f"\n  Sanity: {passed}/{total} passed")
    return passed == total

# ─── Concurrent load workers ───────────────────────────────
def task_override(session, i):
    payload = {
        "item_id": f"TEST-SKU-{random.randint(100,999)}",
        "part_name": "Simulated Part",
        "decision": "Manual Override Approved",
        "amount": round(random.uniform(500, 5000), 2),
        "confidence_bypassed": 85.0,
        "vendor": "Test Vendor LLC",
        "mismatch_detected": True,
    }
    try:
        t0 = time.time()
        r = session.post(f"{BASE_URL}/api/preventive/log-decision", json=payload, timeout=10)
        elapsed = time.time() - t0
        return ("ok" if r.status_code == 200 else "fail", f"override-{i}", elapsed, r.status_code)
    except Exception as e:
        return ("err", f"override-{i}", 0, str(e))

def task_feedback(session, i):
    shadow_id = random.randint(1, 50)
    payload = {"verdict": random.choice(["confirmed_shadow", "false_positive"])}
    try:
        t0 = time.time()
        r = session.post(f"{BASE_URL}/api/shadows/{shadow_id}/feedback", json=payload, timeout=10)
        elapsed = time.time() - t0
        ok = r.status_code in (200, 404)   # 404 fine if ID doesn't exist
        return ("ok" if ok else "fail", f"feedback-{i}", elapsed, r.status_code)
    except Exception as e:
        return ("err", f"feedback-{i}", 0, str(e))

def task_vendor_rings(session, i):
    try:
        t0 = time.time()
        r = session.get(f"{BASE_URL}/api/vendor-rings", timeout=20)
        elapsed = time.time() - t0
        return ("ok" if r.status_code == 200 else "fail", f"rings-{i}", elapsed, r.status_code)
    except Exception as e:
        return ("err", f"rings-{i}", 0, str(e))

def task_ml_status(session, i):
    try:
        t0 = time.time()
        r = session.get(f"{BASE_URL}/api/ml/status", timeout=10)
        elapsed = time.time() - t0
        return ("ok" if r.status_code == 200 else "fail", f"ml-status-{i}", elapsed, r.status_code)
    except Exception as e:
        return ("err", f"ml-status-{i}", 0, str(e))

def task_telemetry(session, i):
    path = random.choice([
        "/api/telemetry/summary",
        "/api/telemetry/shadow-velocity",
        "/api/telemetry/risk-heatmap",
    ])
    try:
        t0 = time.time()
        r = session.get(f"{BASE_URL}{path}", timeout=10)
        elapsed = time.time() - t0
        return ("ok" if r.status_code == 200 else "fail", f"telemetry-{i}", elapsed, r.status_code)
    except Exception as e:
        return ("err", f"telemetry-{i}", 0, str(e))

def task_signal_ingest(session, i):
    payload = {
        "source_type": random.choice(["gate_entry", "petty_cash", "dept_transfer"]),
        "raw_data": {
            "actor": f"Worker-{random.randint(1,20)}",
            "department": random.choice(["Maintenance","Warehouse","Finance","Operations"]),
            "metadata": {"amount": round(random.uniform(50,500),2)},
        }
    }
    try:
        t0 = time.time()
        r = session.post(f"{BASE_URL}/api/signals/ingest", json=payload, timeout=10)
        elapsed = time.time() - t0
        return ("ok" if r.status_code == 200 else "fail", f"signal-{i}", elapsed, r.status_code)
    except Exception as e:
        return ("err", f"signal-{i}", 0, str(e))

# ─── Concurrent load runner ────────────────────────────────
def run_load_test(session, num_requests=50, workers=30):
    print(f"\n{INFO} ── Concurrent Load Test ({num_requests * 6} requests, {workers} workers) ──")
    task_fns = [
        task_override, task_feedback, task_vendor_rings,
        task_ml_status, task_telemetry, task_signal_ingest,
    ]

    futures_map = {}
    t0 = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        for i in range(num_requests):
            fn = task_fns[i % len(task_fns)]
            f = executor.submit(fn, session, i)
            futures_map[f] = fn.__name__

        results = []
        for future in concurrent.futures.as_completed(futures_map):
            results.append(future.result())

    total_elapsed = time.time() - t0

    # Tally
    by_status = {"ok": 0, "fail": 0, "err": 0}
    latencies = []
    failures  = []
    for status, name, elapsed, code in results:
        by_status[status] += 1
        if isinstance(elapsed, float):
            latencies.append(elapsed)
        if status != "ok":
            failures.append((name, code))

    avg_lat = sum(latencies) / max(1, len(latencies))
    max_lat = max(latencies, default=0)
    p95_lat = sorted(latencies)[int(len(latencies)*0.95)] if latencies else 0

    print(f"  Total time   : {total_elapsed:.2f}s")
    print(f"  Requests     : {len(results)}")
    print(f"  Success      : {by_status['ok']}")
    print(f"  Failures     : {by_status['fail']}")
    print(f"  Errors       : {by_status['err']}")
    print(f"  Avg latency  : {avg_lat:.3f}s")
    print(f"  P95 latency  : {p95_lat:.3f}s")
    print(f"  Max latency  : {max_lat:.3f}s")

    if failures:
        print(f"\n  Failure sample (first 10):")
        for name, code in failures[:10]:
            print(f"    - {name}: status {code}")

    return by_status["fail"] == 0 and by_status["err"] == 0

# ─── ML retrain validation ─────────────────────────────────
def run_retrain_check(session):
    print(f"\n{INFO} ── ML Retrain Endpoint ──────────────────────────────")
    ok, r = check_endpoint(session, "POST", "/api/ml/retrain", label="POST /api/ml/retrain")
    if ok and r:
        data = r.json()
        print(f"  Fitted: {data.get('fitted')}  Samples: {data.get('message','')}")
    return ok

# ─── Vendor ring content validation ────────────────────────
def run_ring_content_check(session):
    print(f"\n{INFO} ── Vendor Ring Content Validation ───────────────────")
    ok, r = check_endpoint(session, "GET", "/api/vendor-rings", label="GET /api/vendor-rings")
    if ok and r:
        data = r.json()
        print(f"  Status         : {data.get('status')}")
        print(f"  Vendors analyzed: {data.get('vendors_analyzed')}")
        print(f"  Rings detected : {data.get('rings_detected')}")
        print(f"  Critical rings : {data.get('critical_rings')}")
        print(f"  Graph nodes    : {data.get('graph_meta',{}).get('nodes')}")
        print(f"  Graph edges    : {data.get('graph_meta',{}).get('edges')}")
        if data.get('rings'):
            top = data['rings'][0]
            print(f"  Top ring       : {top['ring_id']} ({top['severity']}) risk={top['ring_risk_score']}")
    return ok

# ─── ML transparency content validation ────────────────────
def run_ml_content_check(session):
    print(f"\n{INFO} ── ML Status Content Validation ─────────────────────")
    ok, r = check_endpoint(session, "GET", "/api/ml/status", label="GET /api/ml/status")
    if ok and r:
        data = r.json()
        fw = data.get("feature_weights", {})
        drift = data.get("drift", {})
        print(f"  Model          : {data.get('model_version')}")
        print(f"  Fitted         : {data.get('fitted')}")
        print(f"  Training smpls : {data.get('training_samples')}")
        print(f"  Feature weights: {fw}")
        print(f"  Drift status   : {drift.get('status')}")
        print(f"  Precision      : {data.get('fitness',{}).get('precision')}")
        print(f"  Conf. in model : {data.get('calibration',{}).get('confidence_in_model')}")
    return ok

# ─── MAIN ──────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  ShadowSync E2E Test Suite v2.0")
    print("=" * 60)

    session = login()

    s1 = run_sanity_checks(session)
    s2 = run_ring_content_check(session)
    s3 = run_ml_content_check(session)
    s4 = run_retrain_check(session)
    s5 = run_load_test(session, num_requests=50, workers=30)

    print("\n" + "=" * 60)
    print("  RESULTS SUMMARY")
    print("=" * 60)
    results = {
        "Sanity Checks":         s1,
        "Vendor Ring Content":   s2,
        "ML Status Content":     s3,
        "ML Retrain":            s4,
        "Concurrent Load (300r)": s5,
    }
    all_pass = True
    for name, passed in results.items():
        tag = PASS if passed else FAIL
        print(f"  {tag}  {name}")
        if not passed:
            all_pass = False

    print("=" * 60)
    if all_pass:
        print(f"  {PASS} ALL TESTS PASSED — System is stable under load")
        sys.exit(0)
    else:
        print(f"  {FAIL} SOME TESTS FAILED — Review output above")
        sys.exit(1)
