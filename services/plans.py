from __future__ import annotations
from datetime import datetime, timedelta
from functools import wraps
from flask import flash, redirect, url_for

PLAN_CATALOG = {
    "basic": {
        "slug": "basic", "name": "Básico", "price": 49, "price_label": "R$ 49/mês",
        "tag": "Operação inicial", "recommended": False, "max_users": 3, "max_clients": 80,
        "max_services_month": 120, "max_storage_mb": 500,
        "description": "Para pequenos times que precisam organizar atendimento, clientes, agenda, tarefas e comunicação interna.",
        "features": {"dashboard", "servicos", "tarefas", "agenda", "clientes", "equipe", "mensagens", "configuracoes", "assinatura", "portal"},
        "feature_list": ["Até 3 usuários", "Até 80 clientes cadastrados", "Até 120 serviços por mês", "Clientes, serviços, equipe, tarefas e agenda", "Mensagens internas", "Configurações e perfil da empresa"],
        "locked_list": ["Financeiro completo", "Relatórios gerenciais", "Desempenho da equipe", "Exportações avançadas", "Integrações avançadas"],
    },
    "pro": {
        "slug": "pro", "name": "Pro", "price": 99, "price_label": "R$ 99/mês",
        "tag": "Mais completo", "recommended": True, "max_users": 15, "max_clients": 1000,
        "max_services_month": 2000, "max_storage_mb": 5000,
        "description": "Para empresas que precisam de visão gerencial, financeiro, relatórios, produtividade e gestão avançada.",
        "features": {"dashboard", "servicos", "tarefas", "agenda", "clientes", "equipe", "financeiro", "relatorios", "desempenho", "mensagens", "configuracoes", "assinatura", "integracoes", "exportacoes", "portal"},
        "feature_list": ["Até 15 usuários", "Até 1.000 clientes cadastrados", "Até 2.000 serviços por mês", "Tudo do Básico", "Financeiro completo", "Relatórios gerenciais", "Desempenho da equipe", "Exportações CSV", "Integrações demonstrativas"],
        "locked_list": [],
    },
}

FEATURE_LABELS = {
    "dashboard": "Dashboard operacional", "servicos": "Gestão de serviços", "tarefas": "Kanban de tarefas",
    "agenda": "Agenda da equipe", "clientes": "CRM de clientes", "equipe": "Gestão de equipe",
    "financeiro": "Financeiro completo", "relatorios": "Relatórios gerenciais", "desempenho": "Desempenho da equipe",
    "mensagens": "Mensagens internas", "configuracoes": "Configurações", "integracoes": "Integrações avançadas", "exportacoes": "Exportações",
}

PAYMENT_METHODS = [
    {"slug": "card", "name": "Cartão de crédito", "desc": "Recorrência mensal. Em produção, confirmar assinatura por webhook do gateway.", "icon": "💳"},
    {"slug": "pix", "name": "Pix", "desc": "Entrada rápida para primeira cobrança. Recorrência depende do provedor escolhido.", "icon": "◆"},
    {"slug": "boleto", "name": "Boleto", "desc": "Alternativa para empresas que preferem pagamento faturado.", "icon": "🧾"},
]

MODULE_FEATURE = {"dashboard":"dashboard", "servicos":"servicos", "tarefas":"tarefas", "agenda":"agenda", "clientes":"clientes", "equipe":"equipe", "financeiro":"financeiro", "relatorios":"relatorios", "desempenho":"desempenho", "mensagens":"mensagens", "configuracoes":"configuracoes", "portal":"portal", "assinatura":"assinatura", "integracoes":"integracoes", "exportacoes":"exportacoes"}

def normalize_plan(plan): return plan if plan in PLAN_CATALOG else "basic"
def get_user_tenant(user): return getattr(user, "tenant", None) if user else None
def get_tenant_plan(tenant): return PLAN_CATALOG[normalize_plan(getattr(tenant, "plan", "basic"))]
def get_current_plan(user): return get_tenant_plan(get_user_tenant(user))
def tenant_has_feature(tenant, feature): return bool(tenant and feature in get_tenant_plan(tenant)["features"])

def user_has_feature(user, feature):
    if not user: return False
    if getattr(user, "role", None) == "admin" and feature == "assinatura": return True
    if getattr(user, "role", None) == "client" and feature in {"portal", "mensagens"}: return True
    return tenant_has_feature(get_user_tenant(user), feature)

def module_allowed_by_plan(user, module): return user_has_feature(user, MODULE_FEATURE.get(module, module))

def feature_required(feature):
    def deco(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            from core.auth import get_current_user
            if not user_has_feature(get_current_user(), feature):
                flash("Este recurso faz parte do plano Pro. Faça upgrade para liberar.", "warning")
                return redirect(url_for("assinatura.assinatura", blocked=feature))
            return func(*args, **kwargs)
        return wrapper
    return deco

def apply_plan(tenant, plan_slug, payment_method="card", billing_cycle="monthly"):
    now = datetime.utcnow(); plan_slug = normalize_plan(plan_slug)
    tenant.plan = plan_slug; tenant.payment_method = payment_method; tenant.billing_cycle = billing_cycle
    tenant.billing_status = "active"; tenant.cancel_at_period_end = False
    tenant.subscription_started_at = tenant.subscription_started_at or now
    tenant.subscription_ends_at = now + timedelta(days=30 if billing_cycle == "monthly" else 365)
    tenant.next_invoice_at = tenant.subscription_ends_at; tenant.last_payment_at = now
    if not getattr(tenant, "trial_ends_at", None): tenant.trial_ends_at = now + timedelta(days=30)
    return tenant

def cancel_subscription_at_period_end(tenant):
    tenant.cancel_at_period_end = True; tenant.billing_status = "cancel_scheduled"; return tenant

def trial_days_left(tenant):
    end = getattr(tenant, "trial_ends_at", None); return max(0, (end - datetime.utcnow()).days) if end else 0

def plan_features_matrix():
    return [{"key": k, "label": v, "basic": k in PLAN_CATALOG["basic"]["features"], "pro": k in PLAN_CATALOG["pro"]["features"]} for k, v in FEATURE_LABELS.items()]

def get_usage_summary(user):
    from models import User, Client, Service
    tenant = get_user_tenant(user); plan = get_current_plan(user)
    if not tenant: return []
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    data = [
        {"key":"users", "label":"Usuários", "used":User.query.filter_by(tenant_id=tenant.id).count(), "limit":plan["max_users"]},
        {"key":"clients", "label":"Clientes", "used":Client.query.filter_by(tenant_id=tenant.id).count(), "limit":plan["max_clients"]},
        {"key":"services", "label":"Serviços no mês", "used":Service.query.filter(Service.tenant_id == tenant.id, Service.created_at >= month_start).count(), "limit":plan["max_services_month"]},
    ]
    for item in data:
        item["pct"] = min(100, round((item["used"] / item["limit"]) * 100)) if item["limit"] else 0
        item["blocked"] = item["used"] >= item["limit"]
    return data

def can_create_resource(user, resource):
    summary = {i["key"]: i for i in get_usage_summary(user)}; item = summary.get(resource)
    if item and item["blocked"]: return False, f"Limite do plano atingido para {item['label']}: {item['used']}/{item['limit']}. Faça upgrade para continuar."
    return True, None
