from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from sqlalchemy import func
from werkzeug.security import generate_password_hash
from models import db, User
from core.auth import get_current_user, login_required, role_required, module_required
from core.constants import EMPLOYEE_ROLES
from services.plans import can_create_resource

bp = Blueprint('equipe', __name__)


def _team_query():
    current = get_current_user()
    q = User.query.filter(User.role.in_(EMPLOYEE_ROLES))
    if current and current.tenant_id:
        q = q.filter(User.tenant_id == current.tenant_id)
    return q


@bp.route('/equipe')
@login_required
@module_required('equipe')
def equipe():
    status_f = request.args.get('status', '')
    search_f = request.args.get('search', '')
    q = _team_query()
    if status_f:
        q = q.filter_by(status=status_f)
    if search_f:
        q = q.filter(User.name.ilike(f'%{search_f}%'))
    users = q.order_by(User.created_at.desc()).all()
    return render_template('equipe.html', users=users, status_f=status_f, search_f=search_f)


@bp.route('/equipe/novo', methods=['POST'])
@login_required
@role_required('admin')
def equipe_novo():
    current = get_current_user()
    ok, message = can_create_resource(current, 'users')
    if not ok:
        flash(message, 'warning')
        return redirect(url_for('assinatura.assinatura', blocked='users'))

    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip().lower()
    raw_pw = request.form.get('password', '').strip()
    role = request.form.get('role', 'technician')

    errors = []
    if not name: errors.append('Informe o nome do membro.')
    if not email: errors.append('Informe o e-mail do membro.')
    if len(raw_pw) < 6: errors.append('A senha inicial deve ter no mínimo 6 caracteres.')
    if role not in EMPLOYEE_ROLES: errors.append('Cargo inválido.')
    if User.query.filter(func.lower(User.email) == email).first():
        errors.append('Este e-mail já está cadastrado.')

    if errors:
        for e in errors:
            flash(e, 'danger')
        return redirect(url_for('equipe.equipe'))

    u = User(
        name=name,
        email=email,
        phone=request.form.get('phone') or None,
        role=role,
        status=request.form.get('status', 'active'),
        department=request.form.get('department') or None,
        password_hash=generate_password_hash(raw_pw),
        tenant_id=current.tenant_id,
    )
    db.session.add(u)
    db.session.commit()
    flash('Usuário criado! Ele já pode entrar pelo login inicial com o e-mail e a senha definida.', 'success')
    return redirect(url_for('equipe.equipe'))


@bp.route('/equipe/<int:id>/editar', methods=['POST'])
@login_required
@role_required('admin')
def equipe_editar(id):
    current = get_current_user()
    q = User.query.filter_by(id=id)
    if current.tenant_id:
        q = q.filter_by(tenant_id=current.tenant_id)
    u = q.first_or_404()

    email = request.form.get('email', '').strip().lower()
    duplicate = User.query.filter(func.lower(User.email) == email, User.id != u.id).first()
    if duplicate:
        flash('Este e-mail já está cadastrado em outra conta.', 'danger')
        return redirect(url_for('equipe.equipe'))

    u.name       = request.form.get('name', '').strip()
    u.email      = email
    u.phone      = request.form.get('phone') or None
    u.role       = request.form.get('role', 'technician')
    u.status     = request.form.get('status', 'active')
    u.department = request.form.get('department') or None
    raw_pw = request.form.get('password', '').strip()
    if raw_pw:
        if len(raw_pw) < 6:
            flash('A nova senha deve ter no mínimo 6 caracteres.', 'danger')
            return redirect(url_for('equipe.equipe'))
        u.password_hash = generate_password_hash(raw_pw)
    u.updated_at = datetime.utcnow()
    db.session.commit()
    flash('Usuário atualizado!', 'success')
    return redirect(url_for('equipe.equipe'))


@bp.route('/equipe/<int:id>/excluir', methods=['POST'])
@login_required
@role_required('admin')
def equipe_excluir(id):
    current = get_current_user()
    q = User.query.filter_by(id=id)
    if current.tenant_id:
        q = q.filter_by(tenant_id=current.tenant_id)
    u = q.first_or_404()
    if u.id == session.get('user_id'):
        flash('Você não pode excluir sua própria conta.', 'warning')
        return redirect(url_for('equipe.equipe'))
    db.session.delete(u)
    db.session.commit()
    flash('Usuário removido.', 'info')
    return redirect(url_for('equipe.equipe'))
