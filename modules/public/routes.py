from flask import Blueprint, render_template, redirect, url_for, request, flash
from core.auth import get_current_user, home_for_role
from services.plans import PLAN_CATALOG, PAYMENT_METHODS

bp = Blueprint('public', __name__)
PLANS = list(PLAN_CATALOG.values())


@bp.route('/')
def landing():
    user = get_current_user()
    if user:
        return redirect(home_for_role(user.role))
    return render_template('landing.html', plans=PLANS)


@bp.route('/planos')
def planos():
    user = get_current_user()
    if user:
        return redirect(url_for('assinatura.assinatura'))
    return render_template('planos.html', plans=PLANS)


@bp.route('/pagamento-demo', methods=['GET', 'POST'])
def pagamento_demo():
    plan_slug = request.values.get('plano') or request.values.get('plan') or 'pro'
    if plan_slug not in PLAN_CATALOG:
        plan_slug = 'pro'
    plan = PLAN_CATALOG[plan_slug]
    if request.method == 'POST':
        flash('Pagamento demonstrativo registrado. Agora crie a conta administradora da empresa.', 'success')
        return redirect(url_for('auth.cadastro', plano=plan['slug']))
    return render_template('pagamento_demo.html', plan=plan, payment_methods=PAYMENT_METHODS)


@bp.route('/entrar')
def entrar_alias():
    return redirect(url_for('auth.login'))


@bp.route('/criar-conta')
def criar_conta_alias():
    plan_slug = request.args.get('plano', 'basic')
    return redirect(url_for('auth.cadastro', plano=plan_slug))
