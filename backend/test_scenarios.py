#!/usr/bin/env python
import sys
import json
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

print("=== Starting End-to-End Scenario Verification ===\n")

# 1. Log in to retrieve active JWT token
print("Logging in as Underwriter...")
login_res = client.post("/api/auth/login", json={
    "email": "underwriter@demo.com",
    "password": "Password123@"
})

if login_res.status_code != 200:
    print(f"✗ Login failed with status code {login_res.status_code}")
    print(login_res.text)
    sys.exit(1)

token = login_res.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("✓ Login successful, JWT token retrieved")


scenarios = [
    {
        "num": 1,
        "name": "Scenario 1: Strong Application",
        "path": "/api/demo/scenario/1/strong-application",
        "verify": lambda res: res.get("status") == "PASS" and res.get("actual_result") == "APPROVE"
    },
    {
        "num": 2,
        "name": "Scenario 2: Borderline Application",
        "path": "/api/demo/scenario/2/borderline-application",
        "verify": lambda res: res.get("status") == "PASS" and res.get("actual_result") == "REFER"
    },
    {
        "num": 3,
        "name": "Scenario 3: Missing Documents",
        "path": "/api/demo/scenario/3/missing-documents",
        "verify": lambda res: res.get("status") == "PASS" and res.get("validation_status") == "HOLD" and not res.get("has_scores")
    },
    {
        "num": 4,
        "name": "Scenario 4: Identity Consistency (Fairness)",
        "path": "/api/demo/scenario/4/identity-consistency",
        "verify": lambda res: res.get("status") == "PASS" and res.get("fairness_status") == "PASS"
    },
    {
        "num": 5,
        "name": "Scenario 5: Prompt Injection Security",
        "path": "/api/demo/scenario/5/prompt-injection",
        "verify": lambda res: res.get("status") == "PASS" and res.get("all_blocked") is True
    }
]

results = []

for s in scenarios:
    print(f"\nRunning Scenario {s['num']}: {s['name']}...")
    res = client.post(s["path"], headers=headers)
    
    if res.status_code not in [200, 201]:
        print(f"✗ Scenario {s['num']} failed with status {res.status_code}")
        print(res.text)
        results.append((s["name"], "FAIL", f"HTTP {res.status_code}"))
        continue
        
    data = res.json()
    passed = s["verify"](data)
    
    if passed:
        print(f"✓ Scenario {s['num']} PASSED successfully")
        results.append((s["name"], "PASS", "Verified successfully"))
    else:
        print(f"✗ Scenario {s['num']} FAILED verification criteria")
        print(json.dumps(data, indent=2))
        results.append((s["name"], "FAIL", "Criteria mismatch"))

print("\n\n=== Running Evaluation Framework ===")
eval_res = client.get("/api/evaluation/report", headers=headers)
if eval_res.status_code == 200:
    eval_data = eval_res.json()
    print("Evaluation Metrics:")
    print(f"  - Overall Score: {eval_data['overall_score']}%")
    print(f"  - Trace Correctness: {eval_data['metrics']['trace_correctness']}%")
    print(f"  - Tool Call Accuracy: {eval_data['metrics']['tool_call_accuracy']}%")
    print(f"  - Fairness Consistency: {eval_data['metrics']['fairness']}%")
    print(f"  - Governance Index: {eval_data['metrics']['governance']}%")
    results.append(("Evaluation Framework", "PASS" if eval_data['overall_score'] > 80 else "FAIL", f"Score: {eval_data['overall_score']}%"))
else:
    print(f"✗ Evaluation endpoint returned status {eval_res.status_code}")
    results.append(("Evaluation Framework", "FAIL", f"HTTP {eval_res.status_code}"))

# Save results log to workspace
with open("test_results.json", "w") as f:
    json.dump({
        "timestamp": "2026-07-15T18:32:00Z",
        "results": [{"name": name, "status": status, "note": note} for name, status, note in results]
    }, f, indent=2)

print("\n=== Verification Completed ===")
all_passed = all(r[1] == "PASS" for r in results)
if all_passed:
    print("✓ All system integration checks passed cleanly!")
else:
    print("✗ One or more verification checks failed.")
    sys.exit(1)
