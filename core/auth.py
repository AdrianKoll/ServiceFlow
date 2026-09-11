from functools import wraps
from flask import session, g, flash, redirect, url_for, request
from models import User, Notification
from .constants import ROLE_ACCESS
from services.plans import module_allowed_by_plan

def get_current_user():
    uid = session.get('user_id')
    if not uid:
        return None
    if not hasattr(g, '_current_user'):
        g._current_user = User.query.get(uid)
    return g._current_user

def get_notifications():
    user = get_current_user()
    if not user:
        return []
    return Notification.query.filter_by(user_id=user.id).order_by(Notification.created_at.desc()).limit(10).all()

def get_unread_count():
    user = get_current_user()
    if not user:
        return 0
    return Notification.query.filter_by(user_id=user.id, read=False).count()

def can_access(module: str) -> bool:
    user = get_current_user()
    if not user:
        return False
    allowed = ROLE_ACCESS.get(user.role, set())
    role_allowed = allowed == '*' or module in allowed
    return bool(role_allowed and module_allowed_by_plan(user, module))

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('user_id'):
            flash('Faça login para continuar.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated

def home_for_role(role: str) -> str:
    if role == 'client':
        return url_for('portal.portal')
    return url_for('main.dashboard')

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user = get_current_user()
            if not user:
                return redirect(url_for('auth.login'))
            if user.role not in roles:
                flash('Você não tem permissão para acessar esta área.', 'danger')
                return redirect(home_for_role(user.role))
            return f(*args, **kwargs)
        return decorated
    return decorator

def module_required(module: str):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user = get_current_user()
            if not user:
                return redirect(url_for('auth.login'))
            if not can_access(module):
                if not module_allowed_by_plan(user, module):
                    flash('Este módulo faz parte do plano Pro. Faça upgrade para liberar.', 'warning')
                    return redirect(url_for('assinatura.assinatura', blocked=module))
                flash('Você não tem permissão para acessar este módulo.', 'danger')
                return redirect(home_for_role(user.role))
            return f(*args, **kwargs)
        return decorated
    return decorator
