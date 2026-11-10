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
from core.form_utils import FormError, text, optional_int, optional_datetime
from core.tenant_policy import get_scoped_or_404, scoped_query

bp = Blueprint('tarefas', __name__)

@bp.route('/tarefas')
@login_required
@module_required('tarefas')
def tarefas():
    current_user = get_current_user()
    tasks_by_status = {
        'todo':        scoped_query(Task).filter_by(status='todo').order_by(Task.created_at.desc()).all(),
        'in_progress': scoped_query(Task).filter_by(status='in_progress').order_by(Task.created_at.desc()).all(),
        'review':      scoped_query(Task).filter_by(status='review').order_by(Task.created_at.desc()).all(),
        'done':        scoped_query(Task).filter_by(status='done').order_by(Task.created_at.desc()).all(),
    }
    users    = User.query.filter(User.status == 'active',
                                  User.role.in_(EMPLOYEE_ROLES),
                                  User.tenant_id == current_user.tenant_id).order_by(User.name).all()
    services = scoped_query(Service).order_by(Service.title).all()
    return render_template('tarefas.html', tasks_by_status=tasks_by_status,
        users=users, services=services)

@bp.route('/tarefas/novo', methods=['POST'])
@login_required
@module_required('tarefas')
def tarefa_nova():
    try:
        current_user = get_current_user()
        assignee_id = optional_int(request.form, 'assignee_id')
        service_id = optional_int(request.form, 'service_id')
        if assignee_id:
            get_scoped_or_404(User, assignee_id)
        if service_id:
            get_scoped_or_404(Service, service_id)
        t = Task(
            title=text(request.form, 'title', required=True),
            description=text(request.form, 'description'),
            status=request.form.get('status', 'todo'),
            priority=request.form.get('priority', 'medium'),
            assignee_id=assignee_id,
            service_id=service_id,
            due_date=optional_datetime(request.form, 'due_date', '%Y-%m-%d'),
            tenant_id=current_user.tenant_id,
        )
        db.session.add(t)
        db.session.commit()
        flash('Tarefa criada!', 'success')
    except FormError as exc:
        db.session.rollback()
        flash(str(exc), 'danger')
    return redirect(url_for('tarefas.tarefas'))

@bp.route('/tarefas/<int:id>/mover', methods=['POST'])
@login_required
@module_required('tarefas')
def tarefa_mover(id):
    t = get_scoped_or_404(Task, id)
    t.status     = request.form['status']
    t.updated_at = datetime.utcnow()
    db.session.commit()
    return redirect(url_for('tarefas.tarefas'))

@bp.route('/tarefas/<int:id>/excluir', methods=['POST'])
@login_required
@module_required('tarefas')
def tarefa_excluir(id):
    t = get_scoped_or_404(Task, id)
    db.session.delete(t)
    db.session.commit()
    flash('Tarefa excluída.', 'info')
    return redirect(url_for('tarefas.tarefas'))
