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

bp = Blueprint('agenda', __name__)

@bp.route('/agenda')
@login_required
@module_required('agenda')
def agenda():
    current_user = get_current_user()
    events   = scoped_query(Event).outerjoin(User, Event.user_id == User.id)\
        .order_by(Event.start_date).all()
    users    = User.query.filter(User.status == 'active',
                                  User.role.in_(EMPLOYEE_ROLES),
                                  User.tenant_id == current_user.tenant_id).order_by(User.name).all()
    services = scoped_query(Service).order_by(Service.title).all()
    return render_template('agenda.html', events=events, users=users, services=services)

@bp.route('/agenda/novo', methods=['POST'])
@login_required
@module_required('agenda')
def evento_novo():
    try:
        current_user = get_current_user()
        user_id = optional_int(request.form, 'user_id')
        service_id = optional_int(request.form, 'service_id')
        if user_id:
            get_scoped_or_404(User, user_id)
        if service_id:
            get_scoped_or_404(Service, service_id)
        e = Event(
            title=text(request.form, 'title', required=True),
            description=text(request.form, 'description'),
            start_date=optional_datetime(request.form, 'start_date', '%Y-%m-%dT%H:%M'),
            end_date=optional_datetime(request.form, 'end_date', '%Y-%m-%dT%H:%M'),
            type=request.form.get('type', 'other'),
            user_id=user_id,
            service_id=service_id,
            location=text(request.form, 'location'),
            tenant_id=current_user.tenant_id,
        )
        if e.start_date is None:
            raise FormError('Informe a data inicial do evento.')
        db.session.add(e)
        db.session.commit()
        flash('Evento criado!', 'success')
    except FormError as exc:
        db.session.rollback()
        flash(str(exc), 'danger')
    return redirect(url_for('agenda.agenda'))

@bp.route('/agenda/<int:id>/excluir', methods=['POST'])
@login_required
@module_required('agenda')
def evento_excluir(id):
    e = get_scoped_or_404(Event, id)
    db.session.delete(e)
    db.session.commit()
    flash('Evento excluído.', 'info')
    return redirect(url_for('agenda.agenda'))
