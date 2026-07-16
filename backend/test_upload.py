"""
Test script to verify the document upload endpoint.
Tests all 5 document types: PAN, Aadhaar, Salary Slip, Employment Letter, Bank Statement
"""
import urllib.request
import urllib.error
import json
import os
import io

BASE_URL = "http://localhost:8000"

def api_post_json(path, data, token=None):
    url = BASE_URL + path
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read()), resp.getcode()
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return json.loads(body), e.code

def multipart_post(path, fields, file_field, filename, file_content, content_type, token=None):
    """Send multipart/form-data POST with urllib."""
    boundary = "----TestBoundary1234567890"
    body_parts = []
    
    for key, value in fields.items():
        body_parts.append(
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"{key}\"\r\n\r\n{value}\r\n"
        )
    
    body_parts.append(
        f"--{boundary}\r\n"
        f"Content-Disposition: form-data; name=\"{file_field}\"; filename=\"{filename}\"\r\n"
        f"Content-Type: {content_type}\r\n\r\n"
    )
    
    body = "".join(body_parts).encode("utf-8")
    body += file_content
    body += f"\r\n--{boundary}--\r\n".encode("utf-8")
    
    url = BASE_URL + path
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read()), resp.getcode()
    except urllib.error.HTTPError as e:
        body_resp = e.read().decode()
        try:
            return json.loads(body_resp), e.code
        except:
            return {"raw": body_resp}, e.code

# --- Step 1: Login ---
print("=" * 60)
print("STEP 1: Login as applicant")
login_resp, code = api_post_json("/api/auth/login", {
    "email": "applicant@demo.com",
    "password": "Password123@"
})
print(f"  Status: {code}")
if code != 200:
    print(f"  ERROR: {login_resp}")
    exit(1)

token = login_resp["access_token"]
print(f"  Token acquired: {token[:20]}...")

# --- Step 2: Create application ---
print("\nSTEP 2: Create application")
boundary = "----AppBoundary9876543210"
app_fields = {
    "loan_amount": "500000",
    "loan_purpose": "Home Purchase",
    "term_months": "60",
    "monthly_debt_obligations": "5000",
    "monthly_income": "80000",
    "employer_name": "TCS Ltd",
    "employment_type": "Salaried",
    "employment_stability_months": "36",
    "phone": "9999999999",
    "date_of_birth": "1990-01-01",
    "address": "123 Main Street, Mumbai",
    "gender": "Male"
}

body_parts = []
for key, value in app_fields.items():
    body_parts.append(
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"{key}\"\r\n\r\n{value}\r\n"
    )
body_parts.append(f"--{boundary}--\r\n")
app_body = "".join(body_parts).encode("utf-8")

url = BASE_URL + "/api/applications/"
req = urllib.request.Request(url, data=app_body, method="POST")
req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
req.add_header("Authorization", f"Bearer {token}")

try:
    with urllib.request.urlopen(req) as resp:
        app_data = json.loads(resp.read())
        app_code = resp.getcode()
except urllib.error.HTTPError as e:
    app_data = json.loads(e.read().decode())
    app_code = e.code

print(f"  Status: {app_code}")
if app_code not in (200, 201):
    print(f"  ERROR: {app_data}")
    exit(1)

app_id = app_data["id"]
print(f"  Application created with ID: {app_id}")

# --- Step 3: Upload Documents ---
print("\nSTEP 3: Upload documents")
doc_types = ["PAN", "Aadhaar", "Salary Slip", "Employment Letter", "Bank Statement"]

# Create a minimal fake PDF (just a text file for testing)
fake_file_content = b"%PDF-1.4 fake pdf content for testing"

results = {}
for doc_type in doc_types:
    filename = f"test_{doc_type.replace(' ', '_')}.pdf"
    resp_data, resp_code = multipart_post(
        f"/api/applications/{app_id}/documents",
        {"document_type": doc_type},
        "file",
        filename,
        fake_file_content,
        "application/pdf",
        token
    )
    status = "PASS" if resp_code in (200, 201) else "FAIL"
    results[doc_type] = {"status": status, "http_code": resp_code, "response": resp_data}
    print(f"  {doc_type}: {status} (HTTP {resp_code})")
    if status == "FAIL":
        print(f"    Error: {resp_data}")

# --- Step 4: Verify files saved ---
print("\nSTEP 4: Verify uploaded files in backend/uploads/")
uploads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
if os.path.exists(uploads_dir):
    files = [f for f in os.listdir(uploads_dir) if str(app_id) in f]
    print(f"  Files found for app {app_id}: {files}")
else:
    print(f"  Uploads dir not found at: {uploads_dir}")

# --- Step 5: Verify DB records ---
print("\nSTEP 5: Verify DB records via GET /documents")
url = BASE_URL + f"/api/applications/{app_id}/documents"
req = urllib.request.Request(url, method="GET")
req.add_header("Authorization", f"Bearer {token}")
try:
    with urllib.request.urlopen(req) as resp:
        docs_data = json.loads(resp.read())
        docs_code = resp.getcode()
except urllib.error.HTTPError as e:
    docs_data = json.loads(e.read().decode())
    docs_code = e.code

print(f"  Status: {docs_code}")
if docs_code == 200:
    print(f"  Documents in DB: {len(docs_data)}")
    for d in docs_data:
        print(f"    - {d.get('document_type')}: {d.get('status')} | path: {d.get('file_path')}")
else:
    print(f"  ERROR fetching docs: {docs_data}")

# --- Summary ---
print("\n" + "=" * 60)
print("UPLOAD TEST SUMMARY")
print("=" * 60)
all_pass = all(v["status"] == "PASS" for v in results.values())
for doc_type, r in results.items():
    print(f"  {doc_type}: {r['status']}")
print(f"\nOverall: {'PASS' if all_pass else 'FAIL'}")
print("=" * 60)
