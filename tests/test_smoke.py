import os
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
    response = client.post(
        "/cadastro",
        data={
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
