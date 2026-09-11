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

bp = Blueprint('financeiro', __name__)

@bp.route('/financeiro')
@login_required
@module_required('financeiro')
def financeiro():
    type_f = request.args.get('type', '')
    q = db.session.query(Transaction, Client.name.label('client_name'),
                         Service.title.label('service_title'))\
        .outerjoin(Client, Transaction.client_id == Client.id)\
        .outerjoin(Service, Transaction.service_id == Service.id)
    if type_f: q = q.filter(Transaction.type == type_f)
    transactions  = q.order_by(Transaction.created_at.desc()).all()
    income        = db.session.query(func.sum(Transaction.amount)).filter_by(type='income').scalar() or 0
    expense       = db.session.query(func.sum(Transaction.amount)).filter_by(type='expense').scalar() or 0
    pending_count = Transaction.query.filter_by(status='pending').count()
    clients       = Client.query.order_by(Client.name).all()
    services      = Service.query.order_by(Service.title).all()
    return render_template('financeiro.html', transactions=transactions,
        income=income, expense=expense, balance=float(income)-float(expense),
        pending_count=pending_count, clients=clients, services=services, type_f=type_f)

@bp.route('/financeiro/novo', methods=['POST'])
@login_required
@module_required('financeiro')
def transacao_nova():
    try:
        t = Transaction(
            description=text(request.form, 'description', required=True),
            type=text(request.form, 'type', required=True),
            amount=optional_decimal(request.form, 'amount'),
            category=text(request.form, 'category'),
            status=request.form.get('status', 'pending'),
            client_id=optional_int(request.form, 'client_id'),
            service_id=optional_int(request.form, 'service_id'),
            due_date=optional_datetime(request.form, 'due_date', '%Y-%m-%d'),
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
    t = Transaction.query.get_or_404(id)
    db.session.delete(t)
    db.session.commit()
    flash('Transação excluída.', 'info')
    return redirect(url_for('financeiro.financeiro'))
