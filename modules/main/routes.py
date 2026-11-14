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
    service_activity_days,
)

bp = Blueprint('main', __name__)

@bp.route('/dashboard')
@login_required
@module_required('dashboard')
def dashboard():
    current_user = get_current_user()
    kpis = core_kpis()
    labels, created, completed = service_activity_chart(12)
    daily_labels, daily_created, daily_completed = service_activity_days(30)
    finance_labels, finance_income, finance_expense = finance_chart(6)
    status_labels, status_data = status_distribution()

    recent_services = db.session.query(
        Service, Client.name.label('client_name'), User.name.label('resp_name')
    ).outerjoin(Client, (Service.client_id == Client.id) & (Client.tenant_id == current_user.tenant_id))\
     .outerjoin(User, (Service.responsible_id == User.id) & (User.tenant_id == current_user.tenant_id))\
     .filter(Service.tenant_id == current_user.tenant_id)\
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
        chart_ranges=json.dumps({
            'week': {
                'labels': daily_labels[-7:],
                'created': daily_created[-7:],
                'completed': daily_completed[-7:],
            },
            'month': {
                'labels': daily_labels,
                'created': daily_created,
                'completed': daily_completed,
            },
            'year': {
                'labels': labels,
                'created': created,
                'completed': completed,
            },
        }),
        daily_created=json.dumps(daily_created),
        daily_peak=max(daily_created or [0]),
        throughput_daily=round(kpis['services_month'] / kpis['month_days_elapsed'], 1),
        **kpis,
    )
