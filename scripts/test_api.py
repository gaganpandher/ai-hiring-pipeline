# -*- coding: utf-8 -*-
"""
test_api.py - Comprehensive API test for AI Hiring Pipeline
============================================================
Tests all endpoints in order:
  1. Auth    — register, login, refresh, me, logout
  2. Jobs    — CRUD + status change
  3. Applications — submit, list, get, decision
  4. Analytics   — dashboard, funnel, cohorts, bias, departments

Run from the project root:
  python scripts/test_api.py
"""

import io
import sys
import time
import uuid
import requests

BASE = "http://localhost:8000/api/v1"

# ── Helpers ───────────────────────────────────────────────────

PASS = "[PASS]"
FAIL = "[FAIL]"
WARN = "[WARN]"

results = []

def check(label: str, resp: requests.Response, expected: int):
    ok = resp.status_code == expected
    symbol = PASS if ok else FAIL
    body_preview = ""
    try:
        j = resp.json()
        if not ok:
            body_preview = f" → {j}"
    except Exception:
        body_preview = f" → {resp.text[:120]}"
    line = f"  {symbol}  [{resp.status_code}]  {label}{body_preview}"
    print(line)
    results.append((ok, label, resp.status_code, expected))
    return resp

def section(title: str):
    print(f"\n{'─'*60}")
    print(f"  {title}")
    print(f"{'─'*60}")

# ── 0. Root / health ──────────────────────────────────────────

section("Root")
resp = requests.get("http://localhost:8000/")
check("GET /", resp, 200)

# ── 1. Auth ───────────────────────────────────────────────────

section("Auth — register / login / me / logout")

uid = uuid.uuid4().hex[:8]

# --- Register recruiter
recruiter_email = f"recruiter_{uid}@test.com"
resp = requests.post(f"{BASE}/auth/register", json={
    "email": recruiter_email,
    "password": "TestPass123!",
    "full_name": "Test Recruiter",
    "role": "recruiter",
})
check("POST /auth/register (recruiter)", resp, 201)

# --- Register applicant
applicant_email = f"applicant_{uid}@test.com"
resp = requests.post(f"{BASE}/auth/register", json={
    "email": applicant_email,
    "password": "TestPass123!",
    "full_name": "Test Applicant",
    "role": "applicant",
})
check("POST /auth/register (applicant)", resp, 201)

# --- Duplicate register (should fail)
resp = requests.post(f"{BASE}/auth/register", json={
    "email": recruiter_email,
    "password": "TestPass123!",
    "full_name": "Dup",
    "role": "recruiter",
})
check("POST /auth/register (duplicate → 400/409)", resp, 409)

# --- Login recruiter (JSON)
resp = requests.post(f"{BASE}/auth/login/json", json={
    "email": recruiter_email,
    "password": "TestPass123!",
})
check("POST /auth/login/json (recruiter)", resp, 200)
recruiter_tokens = resp.json().get("data", {}).get("tokens", {})
recruiter_access  = recruiter_tokens.get("access_token", "")
recruiter_refresh = recruiter_tokens.get("refresh_token", "")

# --- Login applicant (JSON)
resp = requests.post(f"{BASE}/auth/login/json", json={
    "email": applicant_email,
    "password": "TestPass123!",
})
check("POST /auth/login/json (applicant)", resp, 200)
applicant_tokens  = resp.json().get("data", {}).get("tokens", {})
applicant_access  = applicant_tokens.get("access_token", "")
applicant_refresh = applicant_tokens.get("refresh_token", "")

# --- Login with bad password
resp = requests.post(f"{BASE}/auth/login/json", json={
    "email": recruiter_email,
    "password": "WrongPassword!",
})
check("POST /auth/login/json (bad password → 401)", resp, 401)

# --- Login form (OAuth2)
resp = requests.post(f"{BASE}/auth/login", data={
    "username": recruiter_email,
    "password": "TestPass123!",
})
check("POST /auth/login (form)", resp, 200)

# --- GET /me
r_headers = {"Authorization": f"Bearer {recruiter_access}"}
a_headers = {"Authorization": f"Bearer {applicant_access}"}
resp = requests.get(f"{BASE}/auth/me", headers=r_headers)
check("GET /auth/me (recruiter)", resp, 200)

# --- GET /me (no token)
resp = requests.get(f"{BASE}/auth/me")
check("GET /auth/me (no token → 401/403)", resp, 401)

# --- Refresh token
resp = requests.post(f"{BASE}/auth/refresh", json={"refresh_token": recruiter_refresh})
check("POST /auth/refresh", resp, 200)
new_data = resp.json().get("data", {})
recruiter_access = new_data.get("access_token", recruiter_access)
r_headers = {"Authorization": f"Bearer {recruiter_access}"}

# --- Logout
resp = requests.post(f"{BASE}/auth/logout", headers=r_headers)
check("POST /auth/logout", resp, 200)

# Re-login after logout
resp = requests.post(f"{BASE}/auth/login/json", json={
    "email": recruiter_email,
    "password": "TestPass123!",
})
recruiter_tokens = resp.json().get("data", {}).get("tokens", {})
recruiter_access  = recruiter_tokens.get("access_token", recruiter_access)
r_headers = {"Authorization": f"Bearer {recruiter_access}"}

# ── 2. Jobs ───────────────────────────────────────────────────

section("Jobs — CRUD + status change")

# --- List jobs (public)
resp = requests.get(f"{BASE}/jobs")
check("GET /jobs (public, no auth)", resp, 200)

# --- List jobs with filters
resp = requests.get(f"{BASE}/jobs?status=open&page=1&per_page=5")
check("GET /jobs?status=open&page=1&per_page=5", resp, 200)

# --- Create job (recruiter)
resp = requests.post(f"{BASE}/jobs", headers=r_headers, json={
    "title": "Senior AI Engineer",
    "department": "Engineering",
    "location": "Remote",
    "description": "Build and deploy large language model-based hiring tools for our AI-powered recruitment platform.",
    "requirements": "5+ years Python, ML experience required",
    "salary_min": 120000,
    "salary_max": 180000,
    "experience_level": "senior",
})
check("POST /jobs (recruiter)", resp, 201)
job_id = None
if resp.status_code == 201:
    job_id = resp.json().get("data", {}).get("id")

# --- Create job (applicant — should fail)
resp = requests.post(f"{BASE}/jobs", headers=a_headers, json={
    "title": "Unauthorized Job",
    "department": "X",
    "location": "X",
    "description": "This is a short description for an unauthorized job post.",
})
check("POST /jobs (applicant → 403)", resp, 403)

# --- Create job (no auth — should fail)
resp = requests.post(f"{BASE}/jobs", json={"title": "No auth", "description": "This is a short description for a job post with no auth."})
check("POST /jobs (no auth → 401)", resp, 401)

if job_id:
    # --- GET /jobs/{id}
    resp = requests.get(f"{BASE}/jobs/{job_id}")
    check(f"GET /jobs/{{id}}", resp, 200)

    # --- GET non-existent job
    resp = requests.get(f"{BASE}/jobs/nonexistent-job-id")
    check("GET /jobs/nonexistent-id → 404", resp, 404)

    # --- PATCH /jobs/{id}
    resp = requests.patch(f"{BASE}/jobs/{job_id}", headers=r_headers, json={
        "title": "Senior AI Engineer — Updated",
        "salary_max": 200000,
    })
    check("PATCH /jobs/{id}", resp, 200)

    # --- PATCH /jobs/{id}/status → open
    resp = requests.patch(f"{BASE}/jobs/{job_id}/status", headers=r_headers,
                          params={"new_status": "open"})
    check("PATCH /jobs/{id}/status → open", resp, 200)

# ── 3. Applications ───────────────────────────────────────────

section("Applications — submit / list / get / decision")

application_id = None

if job_id:
    # --- Submit application (applicant)
    resume_bytes = b"%PDF-1.4 fake resume content for testing"
    resp = requests.post(
        f"{BASE}/applications",
        headers=a_headers,
        data={
            "job_id": job_id,
            "cover_letter": "I am very excited about this role!",
            "linkedin_url": "https://linkedin.com/in/testapplicant",
        },
        files={"resume": ("resume.pdf", io.BytesIO(resume_bytes), "application/pdf")},
    )
    check("POST /applications (applicant)", resp, 201)
    if resp.status_code == 201:
        application_id = resp.json().get("data", {}).get("id")

    # --- Submit duplicate (should fail — already applied)
    resp = requests.post(
        f"{BASE}/applications",
        headers=a_headers,
        data={"job_id": job_id, "cover_letter": "Duplicate"},
        files={"resume": ("resume.pdf", io.BytesIO(resume_bytes), "application/pdf")},
    )
    check("POST /applications (duplicate → 400/409)", resp, 409)

    # --- Submit as recruiter (should fail)
    resp = requests.post(
        f"{BASE}/applications",
        headers=r_headers,
        data={"job_id": job_id},
        files={"resume": ("resume.pdf", io.BytesIO(resume_bytes), "application/pdf")},
    )
    check("POST /applications (recruiter → 403)", resp, 403)

# --- List applications (recruiter)
resp = requests.get(f"{BASE}/applications", headers=r_headers)
check("GET /applications (recruiter)", resp, 200)

# --- List applications (applicant — own only)
resp = requests.get(f"{BASE}/applications", headers=a_headers)
check("GET /applications (applicant)", resp, 200)

# --- List with filters
if job_id:
    resp = requests.get(f"{BASE}/applications?job_id={job_id}", headers=r_headers)
    check(f"GET /applications?job_id={{id}} (recruiter)", resp, 200)

# --- GET single application
if application_id:
    resp = requests.get(f"{BASE}/applications/{application_id}", headers=r_headers)
    check("GET /applications/{id} (recruiter)", resp, 200)

    resp = requests.get(f"{BASE}/applications/{application_id}", headers=a_headers)
    check("GET /applications/{id} (applicant — own)", resp, 200)

    # --- Make decision (recruiter)
    resp = requests.patch(
        f"{BASE}/applications/{application_id}/decision",
        headers=r_headers,
        json={"status": "shortlist", "recruiter_notes": "Strong candidate"},
    )
    check("PATCH /applications/{id}/decision -> shortlist", resp, 200)

    # --- Make decision (applicant — should fail)
    resp = requests.patch(
        f"{BASE}/applications/{application_id}/decision",
        headers=a_headers,
        json={"status": "hired"},
    )
    check("PATCH /applications/{id}/decision (applicant → 403)", resp, 403)

# ── 4. Analytics ──────────────────────────────────────────────

section("Analytics — dashboard / funnel / cohorts / bias / departments")

# --- Dashboard (recruiter)
resp = requests.get(f"{BASE}/analytics/dashboard", headers=r_headers)
check("GET /analytics/dashboard (recruiter)", resp, 200)

# --- Dashboard (applicant — should fail)
resp = requests.get(f"{BASE}/analytics/dashboard", headers=a_headers)
check("GET /analytics/dashboard (applicant → 403)", resp, 403)

# --- Dashboard (no auth — should fail)
resp = requests.get(f"{BASE}/analytics/dashboard")
check("GET /analytics/dashboard (no auth → 401)", resp, 401)

# --- Funnel (all jobs)
resp = requests.get(f"{BASE}/analytics/funnel", headers=r_headers)
check("GET /analytics/funnel (all jobs)", resp, 200)

# --- Funnel (specific job)
if job_id:
    resp = requests.get(f"{BASE}/analytics/funnel?job_id={job_id}", headers=r_headers)
    check("GET /analytics/funnel?job_id={id}", resp, 200)

# --- Cohorts
resp = requests.get(f"{BASE}/analytics/cohorts?months=6", headers=r_headers)
check("GET /analytics/cohorts?months=6", resp, 200)

# --- Departments
resp = requests.get(f"{BASE}/analytics/departments", headers=r_headers)
check("GET /analytics/departments", resp, 200)

# --- Bias report
if job_id:
    resp = requests.get(f"{BASE}/analytics/bias/{job_id}", headers=r_headers)
    check(f"GET /analytics/bias/{{job_id}}", resp, 200)

    resp = requests.get(f"{BASE}/analytics/bias/nonexistent-job", headers=r_headers)
    check("GET /analytics/bias/nonexistent -> 200 (empty report)", resp, 200)

# ── 5. Cleanup — delete test job ─────────────────────────────

section("Cleanup")

if job_id:
    resp = requests.delete(f"{BASE}/jobs/{job_id}", headers=r_headers)
    check("DELETE /jobs/{id} (recruiter)", resp, 200)

    # Delete again — should 404
    resp = requests.delete(f"{BASE}/jobs/{job_id}", headers=r_headers)
    check("DELETE /jobs/{id} (already deleted → 404)", resp, 404)

# ── Summary ───────────────────────────────────────────────────

section("Summary")
total   = len(results)
passed  = sum(1 for r in results if r[0])
failed  = total - passed

print(f"\n  Total : {total}")
print(f"  {PASS} Passed : {passed}")
print(f"  {FAIL} Failed : {failed}")

if failed:
    print("\n  Failed tests:")
    for ok, label, got, exp in results:
        if not ok:
            print(f"    • {label}  (got {got}, expected {exp})")

print()
sys.exit(0 if failed == 0 else 1)
