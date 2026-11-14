import os
import re
import sys
import json
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ.setdefault("SERVICEFLOW_ENV", "development")
os.environ.setdefault("SESSION_SECRET", "test-only-secret-not-for-production")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app import create_app
from core.security import is_safe_local_url
from models import Client as ClientModel, Service, Task, Transaction, Tenant, User, db
from werkzeug.security import generate_password_hash


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


def test_redirect_targets_are_local_only():
    assert is_safe_local_url("/dashboard?tab=seguranca")
    assert not is_safe_local_url("//attacker.example/login")
    assert not is_safe_local_url("https://attacker.example/login")


def test_trace_is_not_an_allowed_method(client):
    response = client.open("/login", method="TRACE")

    assert response.status_code == 405


def _create_two_tenants(app):
    with app.app_context():
        tenant_a = Tenant(name="Empresa A", slug="empresa-a")
        tenant_b = Tenant(name="Empresa B", slug="empresa-b")
        db.session.add_all([tenant_a, tenant_b])
        db.session.flush()
        user_a = User(
            name="Admin A",
            email="admin-a@example.com",
            role="admin",
            tenant_id=tenant_a.id,
            password_hash=generate_password_hash("senha-de-teste-com-12"),
        )
        client_a = ClientModel(name="Cliente A", tenant_id=tenant_a.id)
        client_b = ClientModel(name="Cliente B privado", tenant_id=tenant_b.id)
        db.session.add_all([user_a, client_a, client_b])
        db.session.commit()
        return user_a.id, client_a.id, client_b.id


def _login_as_session(client, user_id):
    with client.session_transaction() as session:
        session["user_id"] = user_id


def test_tenant_cannot_list_or_edit_another_tenant_client(client):
    user_a_id, client_a_id, client_b_id = _create_two_tenants(client.application)
    _login_as_session(client, user_a_id)

    page = client.get("/clientes")
    assert page.status_code == 200
    assert "Cliente A" in page.get_data(as_text=True)
    assert "Cliente B privado" not in page.get_data(as_text=True)

    csrf_token = re.search(
        r'name="csrf_token" value="([^"]+)"', page.get_data(as_text=True)
    ).group(1)
    response = client.post(
        f"/clientes/{client_b_id}/editar",
        data={
            "csrf_token": csrf_token,
            "name": "Tentativa cross-tenant",
        },
    )
    assert response.status_code == 404


def test_tenant_cannot_associate_service_with_foreign_client(client):
    user_a_id, _, client_b_id = _create_two_tenants(client.application)
    _login_as_session(client, user_a_id)
    page = client.get("/servicos")
    csrf_token = re.search(
        r'name="csrf_token" value="([^"]+)"', page.get_data(as_text=True)
    ).group(1)

    response = client.post(
        "/servicos/novo",
        data={
            "csrf_token": csrf_token,
            "title": "Serviço inválido",
            "client_id": str(client_b_id),
        },
    )
    assert response.status_code == 404


def test_dashboard_uses_tenant_data_and_light_theme(client):
    user_id, client_id, _ = _create_two_tenants(client.application)
    with client.application.app_context():
        user = db.session.get(User, user_id)
        db.session.add_all([
            Service(
                tenant_id=user.tenant_id,
                title="Serviço real",
                client_id=client_id,
                status="completed",
                value=1250,
            ),
            Task(
                tenant_id=user.tenant_id,
                title="Tarefa aberta",
                status="todo",
                assignee_id=user_id,
            ),
            Transaction(
                tenant_id=user.tenant_id,
                description="Receita real",
                type="income",
                amount=1250,
                status="paid",
            ),
        ])
        db.session.commit()

    _login_as_session(client, user_id)
    with client.session_transaction() as session:
        session["theme"] = "light"
    response = client.get("/dashboard")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert '<html lang="pt-BR" class="light">' in html
    assert "Serviço real" in html or "Receita real" in html
    assert "12.1h" not in html
    assert "in range" not in html
    ranges_match = re.search(r'data-ranges=\'([^\']+)\'', html)
    assert ranges_match
    ranges = json.loads(ranges_match.group(1))
    assert set(ranges) == {"week", "month", "year"}
    assert len(ranges["month"]["created"]) == 30
