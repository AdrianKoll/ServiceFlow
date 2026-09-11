import re
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from sqlalchemy import func
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Client, Tenant
from core.auth import get_current_user, home_for_role
from services.plans import PLAN_CATALOG, apply_plan

bp = Blueprint('auth', __name__)


def _slugify_company(name: str) -> str:
    base = re.sub(r'[^a-z0-9]+', '-', (name or '').lower()).strip('-') or 'empresa'
    slug = base
    i = 2
    while Tenant.query.filter_by(slug=slug).first():
        slug = f'{base}-{i}'
        i += 1
    return slug


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user_id'):
        user = get_current_user()
        return redirect(home_for_role(user.role) if user else url_for('main.dashboard'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = User.query.filter(func.lower(User.email) == email).first()

        if not user or not user.password_hash:
            flash('E-mail ou senha incorretos.', 'danger')
            return render_template('login.html', email=email)
        if not check_password_hash(user.password_hash, password):
            flash('E-mail ou senha incorretos.', 'danger')
            return render_template('login.html', email=email)
        if user.status != 'active':
            flash('Conta inativa. Entre em contato com o administrador.', 'warning')
            return render_template('login.html', email=email)
        if user.tenant and user.tenant.status != 'active':
            flash('Empresa inativa. Regularize a assinatura para continuar.', 'warning')
            return render_template('login.html', email=email)

        session.clear()
        session['user_id']   = user.id
        session['user_role'] = user.role
        session.permanent    = True
        flash(f'Bem-vindo(a), {user.name.split()[0]}!', 'success')

        next_url = request.args.get('next')
        if next_url and next_url.startswith('/'):
            return redirect(next_url)
        return redirect(home_for_role(user.role))

    return render_template('login.html', email='')


@bp.route('/logout')
def logout():
    session.clear()
    flash('Sessão encerrada. Até logo!', 'info')
    return redirect(url_for('auth.login'))


@bp.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    """Cadastro público do contratante.

    Quem cria conta por aqui é o dono/administrador da empresa. Ao finalizar,
    o sistema cria a empresa (tenant), aplica o plano selecionado e vincula o
    usuário como administrador principal. Técnicos, gerentes e atendentes são
    criados depois pelo painel Equipe, dentro da empresa.
    """
    if session.get('user_id'):
        user = get_current_user()
        return redirect(home_for_role(user.role) if user else url_for('main.dashboard'))

    plan_slug = request.values.get('plano') or request.values.get('plan') or 'basic'
    if plan_slug not in PLAN_CATALOG:
        plan_slug = 'basic'
    selected_plan = PLAN_CATALOG[plan_slug]

    if request.method == 'POST':
        company_name = request.form.get('company_name', '').strip()
        name     = request.form.get('name', '').strip()
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm', '')

        errors = []
        if not company_name: errors.append('Informe o nome da empresa/negócio.')
        if not name:         errors.append('Informe seu nome completo.')
        if not email:        errors.append('Informe seu e-mail.')
        if len(password) < 12: errors.append('A senha deve ter no mínimo 12 caracteres.')
        if password != confirm: errors.append('As senhas não coincidem.')
        if User.query.filter(func.lower(User.email) == email).first():
            errors.append('Este e-mail já está cadastrado.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('cadastro.html',
                company_name=company_name, name=name, email=email,
                plan=plan_slug, selected_plan=selected_plan)

        tenant = Tenant(
            name=company_name,
            slug=_slugify_company(company_name),
            status='active',
            plan=plan_slug,
            billing_status='trial',
            billing_email=email,
            trial_ends_at=datetime.utcnow() + timedelta(days=30),
        )
        apply_plan(tenant, plan_slug, payment_method='demo', billing_cycle='monthly')
        db.session.add(tenant)
        db.session.flush()

        admin = User(
            name=name,
            email=email,
            role='admin',
            status='active',
            password_hash=generate_password_hash(password),
            tenant_id=tenant.id,
            department='Administração',
        )
        db.session.add(admin)
        db.session.commit()

        flash('Conta de administrador criada com sucesso! Faça login para acessar seu ambiente.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('cadastro.html', company_name='', name='', email='', plan=plan_slug, selected_plan=selected_plan)
