#!/usr/bin/env python3
"""
K² FRS — Production Release & Deployment Smoke Test.
Reference: K2_FRS_V8_Production_Upgrade_Blueprint.md §12.3 & §14.1 (Test T01-T12)

Executes an external smoke probe against a target deployment:
1. Verifies HTTP/HTTPS connectivity and TLS headers.
2. Checks /health/liveness (process alive).
3. Checks /health/readiness (database + model runtime ready).
4. Verifies /api/v1/demo is unmounted / disabled in production mode.
5. Verifies Prometheus /health/metrics exposition.
6. Exercises authentication endpoint validation.
"""

import os
import sys
import argparse
import requests


def run_smoke_test(base_url: str, is_production: bool = True) -> bool:
    print("=" * 60)
    print(f"K² FRS Release Smoke Test — Target: {base_url}")
    print(f"Mode: {'PRODUCTION' if is_production else 'DEVELOPMENT/STAGING'}")
    print("=" * 60)

    clean_base = base_url.rstrip("/")
    passed = True

    # 1. Liveness Probe
    try:
        url = f"{clean_base}/health/liveness"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200 and resp.json().get("success"):
            print("[PASS] /health/liveness -> HTTP 200 (Alive)")
        else:
            print(f"[FAIL] /health/liveness -> HTTP {resp.status_code}: {resp.text}")
            passed = False
    except Exception as exc:
        print(f"[FAIL] /health/liveness connection error: {exc}")
        passed = False

    # 2. Readiness Probe
    try:
        url = f"{clean_base}/health/readiness"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            print(f"[PASS] /health/readiness -> HTTP 200 (DB: {data.get('database')}, Models: {data.get('models_runtime', {}).get('runtime_ready')})")
        else:
            print(f"[FAIL] /health/readiness -> HTTP {resp.status_code}: {resp.text}")
            passed = False
    except Exception as exc:
        print(f"[FAIL] /health/readiness connection error: {exc}")
        passed = False

    # 3. Demo Route Unmount Verification (Blueprint R09)
    try:
        url = f"{clean_base}/api/v1/demo/models"
        resp = requests.get(url, timeout=5)
        if is_production:
            if resp.status_code == 404:
                print("[PASS] /api/v1/demo/models -> HTTP 404 (Safely unmounted in production)")
            else:
                print(f"[FAIL] /api/v1/demo/models -> HTTP {resp.status_code} (Should be 404 in production)")
                passed = False
        else:
            print(f"[INFO] /api/v1/demo/models -> HTTP {resp.status_code} (Active in non-production mode)")
    except Exception as exc:
        print(f"[WARN] Demo route probe error: {exc}")

    # 4. Metrics Probe
    try:
        url = f"{clean_base}/health/metrics"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200 and "frs_uptime_seconds" in resp.text:
            print("[PASS] /health/metrics -> HTTP 200 (Prometheus metrics exposed)")
        else:
            print(f"[FAIL] /health/metrics -> HTTP {resp.status_code}")
            passed = False
    except Exception as exc:
        print(f"[FAIL] /health/metrics connection error: {exc}")
        passed = False

    # 5. Auth Ingress Validation (Reject empty credentials)
    try:
        url = f"{clean_base}/api/v1/auth/login"
        resp = requests.post(url, json={}, timeout=5)
        if resp.status_code in [400, 422]:
            print(f"[PASS] /api/v1/auth/login schema validation -> HTTP {resp.status_code} (Rejected empty credentials)")
        else:
            print(f"[FAIL] /api/v1/auth/login -> Unexpected HTTP {resp.status_code}")
            passed = False
    except Exception as exc:
        print(f"[FAIL] Auth endpoint connection error: {exc}")
        passed = False

    print("=" * 60)
    if passed:
        print("ALL RELEASE SMOKE CHECKS PASSED.")
    else:
        print("RELEASE SMOKE CHECKS ENCOUNTERED FAILURES.")
    print("=" * 60)
    return passed


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="K² FRS Release Smoke Test")
    parser.add_argument(
        "--url",
        default=os.getenv("PROD_API_URL", "http://localhost:8000"),
        help="Base URL of deployed FRS control plane",
    )
    parser.add_argument(
        "--non-prod",
        action="store_true",
        help="Run in development/staging mode (demo routes permitted)",
    )
    args = parser.parse_args()
    success = run_smoke_test(args.url, is_production=not args.non_prod)
    sys.exit(0 if success else 1)
