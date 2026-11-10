from datetime import datetime
from sqlalchemy.orm import declared_attr
from .extensions import db


class TimestampMixin:
    @declared_attr
    def created_at(cls):
        return db.Column(db.DateTime, default=datetime.utcnow)

    @declared_attr
    def updated_at(cls):
        return db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TenantMixin:
    """Base multi-tenant para o SaaS.

    Todo registro operacional pode pertencer a uma empresa/tenant.
    O relacionamento fica centralizado aqui para permitir chamadas como
    current_user.tenant em rotas, templates e regras de plano.
    """

    @declared_attr
    def tenant_id(cls):
        return db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False, index=True)

    @declared_attr
    def tenant(cls):
        return db.relationship('Tenant', lazy='joined')
