import os
import json
import calendar
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from sqlalchemy import func, extract
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Client, Service, Task, Event, Transaction, MessageThread, ThreadParticipant, Message, Notification
from core.auth import get_current_user, login_required, role_required, module_required, home_for_role
from core.constants import EMPLOYEE_ROLES
from services.plans import can_create_resource
from core.form_utils import FormError, text, optional_int, optional_decimal, optional_datetime

bp = Blueprint('servicos', __name__)

@bp.route('/servicos')
@login_required
@module_required('servicos')
def servicos():
    status_f = request.args.get('status', '')
    search_f = request.args.get('search', '')
    q = db.session.query(Service, Client.name.label('client_name'), User.name.label('resp_name'))\
        .outerjoin(Client, Service.client_id == Client.id)\
        .outerjoin(User, Service.responsible_id == User.id)
    if status_f: q = q.filter(Service.status == status_f)
    if search_f: q = q.filter(Service.title.ilike(f'%{search_f}%'))
    services = q.order_by(Service.created_at.desc()).all()
    clients  = Client.query.order_by(Client.name).all()
    users    = User.query.filter(User.status == 'active',
                                 User.role.in_(EMPLOYEE_ROLES)).order_by(User.name).all()
    return render_template('servicos.html', services=services, clients=clients,
        users=users, status_f=status_f, search_f=search_f)

@bp.route('/servicos/novo', methods=['POST'])
@login_required
@module_required('servicos')
def servico_novo():
    ok, message = can_create_resource(get_current_user(), 'services')
    if not ok:
        flash(message, 'warning')
        return redirect(url_for('assinatura.assinatura', blocked='services'))
    try:
        s = Service(
            title=text(request.form, 'title', required=True),
            description=text(request.form, 'description'),
            status=request.form.get('status', 'pending'),
            priority=request.form.get('priority', 'medium'),
            client_id=optional_int(request.form, 'client_id'),
            responsible_id=optional_int(request.form, 'responsible_id'),
            value=optional_decimal(request.form, 'value'),
            due_date=optional_datetime(request.form, 'due_date', '%Y-%m-%d'),
            tenant_id=get_current_user().tenant_id,
        )
        db.session.add(s)
        db.session.commit()
        flash('Serviço criado com sucesso!', 'success')
    except FormError as exc:
        db.session.rollback()
        flash(str(exc), 'danger')
    return redirect(url_for('servicos.servicos'))

@bp.route('/servicos/<int:id>/editar', methods=['POST'])
@login_required
@module_required('servicos')
def servico_editar(id):
    s = Service.query.get_or_404(id)
    try:
        s.title          = text(request.form, 'title', required=True)
        s.description    = text(request.form, 'description')
        s.status         = request.form.get('status', 'pending')
        s.priority       = request.form.get('priority', 'medium')
        s.client_id      = optional_int(request.form, 'client_id')
        s.responsible_id = optional_int(request.form, 'responsible_id')
        s.value          = optional_decimal(request.form, 'value')
        s.due_date       = optional_datetime(request.form, 'due_date', '%Y-%m-%d')
        s.updated_at     = datetime.utcnow()
        db.session.commit()
        flash('Serviço atualizado!', 'success')
    except FormError as exc:
        db.session.rollback()
        flash(str(exc), 'danger')
    return redirect(url_for('servicos.servicos'))

@bp.route('/servicos/<int:id>/excluir', methods=['POST'])
@login_required
@role_required('admin', 'manager')
def servico_excluir(id):
    s = Service.query.get_or_404(id)
    db.session.delete(s)
    db.session.commit()
    flash('Serviço excluído.', 'info')
    return redirect(url_for('servicos.servicos'))
