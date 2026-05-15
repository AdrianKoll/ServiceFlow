from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, User, Tenant
from core.auth import login_required, get_current_user, role_required
from services.plans import (
    PLAN_CATALOG, PAYMENT_METHODS, apply_plan, get_current_plan, trial_days_left,
    get_usage_summary, plan_features_matrix, cancel_subscription_at_period_end, normalize_plan
)

bp = Blueprint('assinatura', __name__)


def _ensure_tenant_for_user(user):
    if not user:
        return None
    tenant = getattr(user, 'tenant', None)
    if tenant:
        return tenant

    company_name = f"Empresa de {user.name or 'Administrador'}"
    base_slug = ''.join(ch.lower() if ch.isalnum() else '-' for ch in company_name).strip('-') or 'empresa'
    slug = base_slug
    counter = 2
    while Tenant.query.filter_by(slug=slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1

    tenant = Tenant(
        name=company_name,
        slug=slug,
        status='active',
        plan=normalize_plan(getattr(user, 'plan', 'basic')),
        billing_status='trial',
        billing_email=user.email,
        trial_ends_at=datetime.utcnow() + timedelta(days=30),
    )
    apply_plan(tenant, tenant.plan, payment_method='demo', billing_cycle='monthly')
    db.session.add(tenant)
    db.session.flush()
    user.tenant_id = tenant.id
    if not user.role:
        user.role = 'admin'
    db.session.commit()
    return tenant


@bp.route('/assinatura')
@login_required
def assinatura():
    user = get_current_user()
    tenant = _ensure_tenant_for_user(user)
    current_plan = get_current_plan(user)
    users_count = User.query.filter_by(tenant_id=tenant.id).count() if tenant else 0
    blocked = request.args.get('blocked')
    return render_template(
        'assinatura.html',
        plans=PLAN_CATALOG,
        payment_methods=PAYMENT_METHODS,
        current_plan=current_plan,
        tenant=tenant,
        users_count=users_count,
        blocked=blocked,
        trial_days=trial_days_left(tenant),
        usage_summary=get_usage_summary(user),
        feature_matrix=plan_features_matrix(),
    )


@bp.route('/assinatura/alterar', methods=['POST'])
@login_required
@role_required('admin')
def alterar_plano():
    user = get_current_user()
    tenant = _ensure_tenant_for_user(user)
    plan = request.form.get('plan', 'basic')
    method = request.form.get('payment_method', 'card')
    billing_cycle = request.form.get('billing_cycle', 'monthly')

    if plan not in PLAN_CATALOG:
        flash('Plano inválido.', 'danger')
        return redirect(url_for('assinatura.assinatura'))
    if method not in {m['slug'] for m in PAYMENT_METHODS}:
        flash('Forma de pagamento inválida.', 'danger')
        return redirect(url_for('assinatura.assinatura'))

    apply_plan(tenant, plan, method, billing_cycle)
    db.session.commit()
    flash(f'Plano {PLAN_CATALOG[plan]["name"]} ativado em modo demonstrativo.', 'success')
    return redirect(url_for('assinatura.assinatura'))


@bp.route('/assinatura/cancelar', methods=['POST'])
@login_required
@role_required('admin')
def cancelar_assinatura():
    tenant = _ensure_tenant_for_user(get_current_user())
    cancel_subscription_at_period_end(tenant)
    db.session.commit()
    flash('Cancelamento agendado para o fim do período demonstrativo.', 'info')
    return redirect(url_for('assinatura.assinatura'))
