import os
import json
import calendar
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from sqlalchemy import func, extract
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Client, Service, Task, Event, Transaction, MessageThread, ThreadParticipant, Message, Notification
from core.auth import get_current_user, login_required, role_required, module_required, home_for_role
from core.security import local_redirect
from core.constants import EMPLOYEE_ROLES

bp = Blueprint('notifications', __name__)

@bp.route('/notifications/<int:id>/read', methods=['POST'])
@login_required
def notification_read(id):
    user = get_current_user()
    n = Notification.query.filter_by(
        id=id, user_id=user.id, tenant_id=user.tenant_id
    ).first_or_404()
    n.read = True
    db.session.commit()
    return redirect(local_redirect(request.referrer, url_for('main.dashboard')))

@bp.route('/notifications/mark-all-read', methods=['POST'])
@login_required
def notifications_mark_all():
    user = get_current_user()
    Notification.query.filter_by(
        user_id=user.id, tenant_id=user.tenant_id, read=False
    ).update({'read': True})
    db.session.commit()
    return redirect(local_redirect(request.referrer, url_for('main.dashboard')))
