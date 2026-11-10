import os
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ.setdefault("SERVICEFLOW_ENV", "development")
os.environ.setdefault("SESSION_SECRET", "test-only-secret-not-for-production")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config.update(TESTING=True)
    with app.test_client() as test_client:
        yield test_client


def test_login_page_and_security_headers(client):
    response = client.get("/login")

    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "SAMEORIGIN"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"


def test_registration_rejects_short_password(client):
    page = client.get("/cadastro")
    csrf_token = re.search(r'name="csrf_token" value="([^"]+)"', page.get_data(as_text=True)).group(1)
    response = client.post(
        "/cadastro",
        data={
            "csrf_token": csrf_token,
            "company_name": "Empresa de Teste",
            "name": "Pessoa de Teste",
            "email": "teste@example.com",
            "password": "curta",
            "confirm": "curta",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "12 caracteres" in response.get_data(as_text=True)


def test_mutating_request_without_csrf_is_rejected(client):
    response = client.post(
        "/cadastro",
        data={"company_name": "Empresa", "name": "Pessoa", "email": "pessoa@example.com"},
    )

    assert response.status_code == 400
    assert "CSRF" in response.get_data(as_text=True)


def test_login_is_rate_limited(client):
    page = client.get("/login")
    csrf_token = re.search(r'name="csrf_token" value="([^"]+)"', page.get_data(as_text=True)).group(1)
    data = {"csrf_token": csrf_token, "email": "brute@example.com", "password": "senha-incorreta"}

    responses = [client.post("/login", data=data) for _ in range(6)]

    assert all(response.status_code == 200 for response in responses[:5])
    assert responses[-1].status_code == 429
