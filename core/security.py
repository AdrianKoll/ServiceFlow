"""Proteções transversais de segurança da aplicação."""

from __future__ import annotations

import hashlib
import hmac
import secrets

from flask import Flask, abort, request, session


CSRF_SESSION_KEY = "csrf_token"
CSRF_FORM_FIELD = "csrf_token"
SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}


def _get_csrf_token() -> str:
    """Cria e retorna o token CSRF associado à sessão atual."""
    token = session.get(CSRF_SESSION_KEY)
    if not token:
        token = secrets.token_urlsafe(32)
        session[CSRF_SESSION_KEY] = token
    return token


def _validate_csrf() -> None:
    """Rejeita requisições mutáveis sem um token CSRF válido."""
    if request.method in SAFE_METHODS:
        return

    submitted_token = request.form.get(CSRF_FORM_FIELD) or request.headers.get("X-CSRFToken")
    expected_token = session.get(CSRF_SESSION_KEY)
    if not expected_token or not submitted_token or not hmac.compare_digest(
        expected_token, submitted_token
    ):
        abort(400, description="Token CSRF ausente ou inválido.")


def register_security_headers(app: Flask) -> None:
    """Registra proteção CSRF e cabeçalhos seguros sem quebrar o front-end."""
    app.jinja_env.globals["csrf_token"] = _get_csrf_token
    app.before_request(_validate_csrf)

    @app.after_request
    def add_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        return response


def login_rate_limit_key() -> str:
    """Combina IP e e-mail para dificultar contornos triviais do limite."""
    email = request.form.get("email", "").strip().lower()
    ip = request.remote_addr or "unknown"
    digest = hashlib.sha256(email.encode("utf-8")).hexdigest()[:16]
    return f"{ip}:{digest}"
