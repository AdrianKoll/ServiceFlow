import json
from flask import Blueprint, render_template

from models import db, Client, Service, User
from core.auth import get_current_user, login_required, module_required
from core.constants import EMPLOYEE_ROLES
from services.analytics import (
    core_kpis,
    service_activity_chart,
    status_distribution,
    employee_performance,
    recent_activity,
    finance_chart,
)

bp = Blueprint('main', __name__)

@bp.route('/dashboard')
@login_required
@module_required('dashboard')
def dashboard():
    current_user = get_current_user()
    kpis = core_kpis()
    labels, created, completed = service_activity_chart(6)
    finance_labels, finance_income, finance_expense = finance_chart(6)
    status_labels, status_data = status_distribution()

    recent_services = db.session.query(
        Service, Client.name.label('client_name'), User.name.label('resp_name')
    ).outerjoin(Client, Service.client_id == Client.id)\
     .outerjoin(User, Service.responsible_id == User.id)\
     .order_by(Service.created_at.desc()).limit(5).all()

    return render_template(
        'dashboard.html',
        current_user_name=current_user.name,
        recent_services=recent_services,
        team_performance=employee_performance(limit=4),
        recent_activity=recent_activity(limit=7),
        chart_labels=json.dumps(labels),
        chart_created=json.dumps(created),
        chart_completed=json.dumps(completed),
        chart_status_labels=json.dumps(status_labels),
        chart_status_data=json.dumps(status_data),
        finance_labels=json.dumps(finance_labels),
        finance_income=json.dumps(finance_income),
        finance_expense=json.dumps(finance_expense),
        **kpis,
    )
