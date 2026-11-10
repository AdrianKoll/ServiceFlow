import os
import json
import calendar
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from sqlalchemy import func, extract
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Client, Service, Task, Event, Transaction, MessageThread, ThreadParticipant, Message, Notification
from core.auth import get_current_user, login_required, role_required, module_required, home_for_role
from core.tenant_policy import scoped_query
from core.constants import EMPLOYEE_ROLES

bp = Blueprint('portal', __name__)

@bp.route('/portal')
@login_required
@role_required('client')
def portal():
    user = get_current_user()
    client = user.client_link
    services = []
    if client:
        services = scoped_query(Service).filter_by(client_id=client.id)\
            .order_by(Service.created_at.desc()).all()
    total   = len(services)
    pending = sum(1 for s in services if s.status == 'pending')
    inprog  = sum(1 for s in services if s.status == 'in_progress')
    done    = sum(1 for s in services if s.status == 'completed')
    return render_template('portal.html',
        client=client, services=services,
        total=total, pending=pending, inprog=inprog, done=done)
