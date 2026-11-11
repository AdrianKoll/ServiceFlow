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
from core.form_utils import FormError, text, optional_int, optional_decimal, optional_datetime
from core.tenant_policy import get_scoped_or_404, scoped_query

bp = Blueprint('financeiro', __name__)

@bp.route('/financeiro')
@login_required
@module_required('financeiro')
def financeiro():
    current_user = get_current_user()
    type_f = request.args.get('type', '')
    q = db.session.query(Transaction, Client.name.label('client_name'),
                         Service.title.label('service_title'))\
        .outerjoin(Client, (Transaction.client_id == Client.id) & (Client.tenant_id == current_user.tenant_id))\
        .outerjoin(Service, (Transaction.service_id == Service.id) & (Service.tenant_id == current_user.tenant_id))\
        .filter(Transaction.tenant_id == current_user.tenant_id)
    if type_f: q = q.filter(Transaction.type == type_f)
    transactions  = q.order_by(Transaction.created_at.desc()).all()
    income        = scoped_query(Transaction).filter_by(type='income').with_entities(func.sum(Transaction.amount)).scalar() or 0
    expense       = scoped_query(Transaction).filter_by(type='expense').with_entities(func.sum(Transaction.amount)).scalar() or 0
    pending_count = scoped_query(Transaction).filter_by(status='pending').count()
    clients       = scoped_query(Client).order_by(Client.name).all()
    services      = scoped_query(Service).order_by(Service.title).all()
    return render_template('financeiro.html', transactions=transactions,
        income=income, expense=expense, balance=float(income)-float(expense),
        pending_count=pending_count, clients=clients, services=services, type_f=type_f)

@bp.route('/financeiro/novo', methods=['POST'])
@login_required
@module_required('financeiro')
def transacao_nova():
    try:
        current_user = get_current_user()
        client_id = optional_int(request.form, 'client_id')
        service_id = optional_int(request.form, 'service_id')
        if client_id:
            get_scoped_or_404(Client, client_id)
        if service_id:
            get_scoped_or_404(Service, service_id)
        t = Transaction(
            description=text(request.form, 'description', required=True),
            type=text(request.form, 'type', required=True),
            amount=optional_decimal(request.form, 'amount'),
            category=text(request.form, 'category'),
            status=request.form.get('status', 'pending'),
            client_id=client_id,
            service_id=service_id,
            due_date=optional_datetime(request.form, 'due_date', '%Y-%m-%d'),
            tenant_id=current_user.tenant_id,
        )
        if t.amount is None:
            raise FormError('Informe um valor válido para a transação.')
        db.session.add(t)
        db.session.commit()
        flash('Transação criada!', 'success')
    except FormError as exc:
        db.session.rollback()
        flash(str(exc), 'danger')
    return redirect(url_for('financeiro.financeiro'))

@bp.route('/financeiro/<int:id>/excluir', methods=['POST'])
@login_required
@role_required('admin', 'manager')
def transacao_excluir(id):
    t = get_scoped_or_404(Transaction, id)
    db.session.delete(t)
    db.session.commit()
    flash('Transação excluída.', 'info')
    return redirect(url_for('financeiro.financeiro'))
