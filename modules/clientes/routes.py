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
from core.tenant_policy import get_scoped_or_404, scoped_query

bp = Blueprint('clientes', __name__)

@bp.route('/clientes')
@login_required
@module_required('clientes')
def clientes():
    status_f = request.args.get('status', '')
    search_f = request.args.get('search', '')
    q = scoped_query(Client)
    if status_f: q = q.filter_by(status=status_f)
    if search_f: q = q.filter(Client.name.ilike(f'%{search_f}%'))
    clients = q.order_by(Client.created_at.desc()).all()
    return render_template('clientes.html', clients=clients,
        status_f=status_f, search_f=search_f)

@bp.route('/clientes/novo', methods=['POST'])
@login_required
@module_required('clientes')
def cliente_novo():
    ok, message = can_create_resource(get_current_user(), 'clients')
    if not ok:
        flash(message, 'warning')
        return redirect(url_for('assinatura.assinatura', blocked='clients'))
    c = Client(
        name=request.form['name'],
        email=request.form.get('email') or None,
        phone=request.form.get('phone') or None,
        company=request.form.get('company') or None,
        address=request.form.get('address') or None,
        city=request.form.get('city') or None,
        state=request.form.get('state') or None,
        status=request.form.get('status', 'active'),
        notes=request.form.get('notes') or None,
        tenant_id=get_current_user().tenant_id,
    )
    db.session.add(c)
    db.session.commit()
    flash('Cliente criado com sucesso!', 'success')
    return redirect(url_for('clientes.clientes'))

@bp.route('/clientes/<int:id>/editar', methods=['POST'])
@login_required
@module_required('clientes')
def cliente_editar(id):
    c = get_scoped_or_404(Client, id)
    c.name    = request.form['name']
    c.email   = request.form.get('email') or None
    c.phone   = request.form.get('phone') or None
    c.company = request.form.get('company') or None
    c.city    = request.form.get('city') or None
    c.state   = request.form.get('state') or None
    c.status  = request.form.get('status', 'active')
    c.notes   = request.form.get('notes') or None
    c.updated_at = datetime.utcnow()
    db.session.commit()
    flash('Cliente atualizado!', 'success')
    return redirect(url_for('clientes.clientes'))

@bp.route('/clientes/<int:id>/excluir', methods=['POST'])
@login_required
@role_required('admin', 'manager')
def cliente_excluir(id):
    c = get_scoped_or_404(Client, id)
    db.session.delete(c)
    db.session.commit()
    flash('Cliente excluído.', 'info')
    return redirect(url_for('clientes.clientes'))
