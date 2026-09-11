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

bp = Blueprint('dev', __name__)

@bp.route('/seed')
@login_required
@role_required('admin')
def seed():
    from werkzeug.security import generate_password_hash as gph
    # Adiciona senha ao admin se ainda não tiver
    admin = User.query.filter_by(role='admin').first()
    if admin and not admin.password_hash:
        admin.password_hash = gph('admin123')
        db.session.commit()
        flash('Senha do admin definida como: admin123', 'success')
    else:
        flash('Seed executado. Admin já possui senha.', 'info')
    return redirect(url_for('main.dashboard'))
