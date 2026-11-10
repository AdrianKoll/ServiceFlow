"""Políticas de autorização por tenant para entidades operacionais."""

from __future__ import annotations

from flask import abort


def current_tenant_id() -> int:
    """Retorna o tenant do usuário autenticado ou rejeita a operação."""
    from core.auth import get_current_user

    user = get_current_user()
    if not user or not user.tenant_id:
        abort(403, description="Usuário sem tenant associado.")
    return user.tenant_id


def scoped_query(model):
    """Inicia uma consulta limitada ao tenant do usuário atual."""
    if not hasattr(model, "tenant_id"):
        raise TypeError(f"{model.__name__} não possui tenant_id.")
    return model.query.filter(model.tenant_id == current_tenant_id())


def get_scoped_or_404(model, object_id):
    """Busca um objeto pelo ID somente dentro do tenant atual."""
    return scoped_query(model).filter(model.id == object_id).first_or_404()


def ensure_same_tenant(*objects) -> None:
    """Rejeita objetos ausentes ou pertencentes a outro tenant."""
    tenant_id = current_tenant_id()
    if any(obj is None or getattr(obj, "tenant_id", None) != tenant_id for obj in objects):
        abort(404)
