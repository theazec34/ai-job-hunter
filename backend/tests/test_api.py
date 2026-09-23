from fastapi.testclient import TestClient


def test_health(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_preview_origin_is_allowed_by_cors(client: TestClient):
    response = client.options(
        "/api/auth/login",
        headers={
            "Origin": "http://127.0.0.1:43123",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:43123"


def test_register_login_and_duplicate_email(client: TestClient):
    credentials = {"email": "Alfredo@Example.com", "password": "secure-password"}
    registered = client.post("/api/auth/register", json=credentials)
    assert registered.status_code == 201
    assert registered.json()["token_type"] == "bearer"

    duplicate = client.post("/api/auth/register", json=credentials)
    assert duplicate.status_code == 409

    logged_in = client.post(
        "/api/auth/login",
        json={"email": "alfredo@example.com", "password": "secure-password"},
    )
    assert logged_in.status_code == 200
    assert logged_in.json()["access_token"]

    rejected = client.post(
        "/api/auth/login",
        json={"email": "alfredo@example.com", "password": "wrong"},
    )
    assert rejected.status_code == 401


def test_profile_requires_auth_and_is_isolated(client: TestClient, auth_headers: dict[str, str]):
    assert client.get("/api/profile").status_code == 401

    payload = {
        "name": "Alfredo",
        "headline": "Junior AI Engineer",
        "skills": ["Python", "FastAPI", "Python"],
        "desired_roles": ["AI Engineer"],
        "preferred_countries": ["Spain"],
    }
    saved = client.put("/api/profile", headers=auth_headers, json=payload)
    assert saved.status_code == 200
    assert saved.json()["skills"] == ["Python", "FastAPI"]

    ester = client.post(
        "/api/auth/register",
        json={"email": "ester@example.com", "password": "another-secure-password"},
    )
    ester_headers = {"Authorization": f"Bearer {ester.json()['access_token']}"}
    assert client.get("/api/profile", headers=ester_headers).status_code == 404


def test_jobs_matching_and_duplicate_protection(
    client: TestClient, auth_headers: dict[str, str]
):
    profile = {
        "name": "Alfredo",
        "headline": "AI Engineer",
        "skills": ["Python", "FastAPI", "TypeScript"],
        "desired_roles": ["AI Engineer"],
        "preferred_countries": ["Spain"],
    }
    assert client.put("/api/profile", headers=auth_headers, json=profile).status_code == 200

    job = {
        "source": "EURES",
        "external_id": "eures-1",
        "title": "Junior AI Engineer",
        "company": "Example Labs",
        "country": "Spain",
        "location": "Madrid",
        "description": "Build Python services with FastAPI.",
        "url": "https://example.com/jobs/1",
        "employment_type": "Full-time",
    }
    created = client.post("/api/jobs", headers=auth_headers, json=job)
    assert created.status_code == 201
    assert client.post("/api/jobs", headers=auth_headers, json=job).status_code == 409

    matches = client.get("/api/matches", headers=auth_headers)
    assert matches.status_code == 200
    assert matches.json()[0]["score"] == 70
    assert "Skill: python" in matches.json()[0]["reasons"]
    assert "Skill: fastapi" in matches.json()[0]["reasons"]


def test_matching_requires_profile(client: TestClient, auth_headers: dict[str, str]):
    response = client.get("/api/matches", headers=auth_headers)
    assert response.status_code == 400
