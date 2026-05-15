from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import func, extract

from models import db, User, Client, Service, Task, Event, Transaction, Message
from core.constants import EMPLOYEE_ROLES


def _now() -> datetime:
    return datetime.utcnow()


def _month_bounds(reference: datetime | None = None) -> tuple[datetime, datetime]:
    ref = reference or _now()
    start = datetime(ref.year, ref.month, 1)
    if ref.month == 12:
        end = datetime(ref.year + 1, 1, 1)
    else:
        end = datetime(ref.year, ref.month + 1, 1)
    return start, end


def _safe_pct(part: int | float, total: int | float) -> int:
    if not total:
        return 0
    return round((part / total) * 100)


def core_kpis() -> dict[str, Any]:
    month_start, month_end = _month_bounds()
    prev_month_end = month_start
    if month_start.month == 1:
        prev_month_start = datetime(month_start.year - 1, 12, 1)
    else:
        prev_month_start = datetime(month_start.year, month_start.month - 1, 1)

    svc_total = Service.query.count()
    svc_completed = Service.query.filter_by(status='completed').count()
    svc_pending = Service.query.filter_by(status='pending').count()
    svc_inprogress = Service.query.filter_by(status='in_progress').count()
    svc_cancelled = Service.query.filter_by(status='cancelled').count()

    services_month = Service.query.filter(Service.created_at >= month_start, Service.created_at < month_end).count()
    services_prev = Service.query.filter(Service.created_at >= prev_month_start, Service.created_at < prev_month_end).count()
    service_growth = _safe_pct(services_month - services_prev, services_prev) if services_prev else (100 if services_month else 0)

    income_month = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.type == 'income',
        Transaction.created_at >= month_start,
        Transaction.created_at < month_end,
    ).scalar() or 0
    expense_month = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.type == 'expense',
        Transaction.created_at >= month_start,
        Transaction.created_at < month_end,
    ).scalar() or 0

    today = _now()
    overdue_services = Service.query.filter(
        Service.status.notin_(['completed', 'cancelled']),
        Service.due_date.isnot(None),
        Service.due_date < today,
    ).count()
    overdue_tasks = Task.query.filter(
        Task.status.notin_(['done']),
        Task.due_date.isnot(None),
        Task.due_date < today,
    ).count()
    open_tasks = Task.query.filter(Task.status.notin_(['done'])).count()
    completed_tasks = Task.query.filter_by(status='done').count()

    return {
        'svc_total': svc_total,
        'svc_pending': svc_pending,
        'svc_inprogress': svc_inprogress,
        'svc_completed': svc_completed,
        'svc_cancelled': svc_cancelled,
        'client_total': Client.query.count(),
        'user_total': User.query.filter(User.role.in_(EMPLOYEE_ROLES)).count(),
        'revenue_total': db.session.query(func.sum(Transaction.amount)).filter_by(type='income').scalar() or 0,
        'services_month': services_month,
        'service_growth': service_growth,
        'income_month': income_month,
        'expense_month': expense_month,
        'balance_month': income_month - expense_month,
        'completion_rate': _safe_pct(svc_completed, svc_total),
        'task_completion_rate': _safe_pct(completed_tasks, completed_tasks + open_tasks),
        'overdue_services': overdue_services,
        'overdue_tasks': overdue_tasks,
    }


def service_activity_chart(months: int = 6) -> tuple[list[str], list[int], list[int]]:
    today = _now()
    labels: list[str] = []
    created: list[int] = []
    completed: list[int] = []
    for i in range(months - 1, -1, -1):
        m, y = today.month - i, today.year
        while m <= 0:
            m += 12
            y -= 1
        labels.append(f"{calendar.month_abbr[m]}/{str(y)[2:]}")
        created.append(Service.query.filter(extract('month', Service.created_at) == m, extract('year', Service.created_at) == y).count())
        completed.append(Service.query.filter(extract('month', Service.created_at) == m, extract('year', Service.created_at) == y, Service.status == 'completed').count())
    return labels, created, completed


def finance_chart(months: int = 6) -> tuple[list[str], list[float], list[float]]:
    today = _now()
    labels: list[str] = []
    incomes: list[float] = []
    expenses: list[float] = []
    for i in range(months - 1, -1, -1):
        m, y = today.month - i, today.year
        while m <= 0:
            m += 12
            y -= 1
        labels.append(f"{calendar.month_abbr[m]}/{str(y)[2:]}")
        incomes.append(float(db.session.query(func.sum(Transaction.amount)).filter(Transaction.type == 'income', extract('month', Transaction.created_at) == m, extract('year', Transaction.created_at) == y).scalar() or 0))
        expenses.append(float(db.session.query(func.sum(Transaction.amount)).filter(Transaction.type == 'expense', extract('month', Transaction.created_at) == m, extract('year', Transaction.created_at) == y).scalar() or 0))
    return labels, incomes, expenses


def employee_performance(limit: int | None = None) -> list[dict[str, Any]]:
    users = User.query.filter(User.role.in_(EMPLOYEE_ROLES)).order_by(User.name.asc()).all()
    today = _now()
    rows: list[dict[str, Any]] = []
    for user in users:
        task_total = Task.query.filter_by(assignee_id=user.id).count()
        task_done = Task.query.filter_by(assignee_id=user.id, status='done').count()
        task_overdue = Task.query.filter(
            Task.assignee_id == user.id,
            Task.status != 'done',
            Task.due_date.isnot(None),
            Task.due_date < today,
        ).count()
        services_total = Service.query.filter_by(responsible_id=user.id).count()
        services_completed = Service.query.filter_by(responsible_id=user.id, status='completed').count()
        completion = _safe_pct(task_done + services_completed, task_total + services_total)
        quality_penalty = min(35, task_overdue * 8)
        score = max(0, min(100, completion - quality_penalty + (5 if user.status == 'active' else -10)))
        rows.append({
            'user': user,
            'task_total': task_total,
            'task_done': task_done,
            'task_overdue': task_overdue,
            'services_total': services_total,
            'services_completed': services_completed,
            'completion': completion,
            'score': score,
            'risk': 'high' if task_overdue >= 3 else ('medium' if task_overdue else 'low'),
        })
    rows.sort(key=lambda r: (r['score'], r['task_done'] + r['services_completed']), reverse=True)
    return rows[:limit] if limit else rows


def recent_activity(limit: int = 8) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for service in Service.query.order_by(Service.created_at.desc()).limit(limit).all():
        items.append({'type': 'service', 'title': service.title, 'description': 'Serviço criado/atualizado', 'date': service.created_at, 'status': service.status})
    for client in Client.query.order_by(Client.created_at.desc()).limit(limit).all():
        items.append({'type': 'client', 'title': client.name, 'description': 'Cliente cadastrado', 'date': client.created_at, 'status': client.status})
    for task in Task.query.order_by(Task.created_at.desc()).limit(limit).all():
        items.append({'type': 'task', 'title': task.title, 'description': 'Tarefa registrada', 'date': task.created_at, 'status': task.status})
    for tx in Transaction.query.order_by(Transaction.created_at.desc()).limit(limit).all():
        items.append({'type': 'finance', 'title': tx.description, 'description': 'Movimento financeiro', 'date': tx.created_at, 'status': tx.status})
    items.sort(key=lambda x: x.get('date') or datetime.min, reverse=True)
    return items[:limit]


def status_distribution() -> tuple[list[str], list[int]]:
    return ['Pendente', 'Em Andamento', 'Concluído', 'Cancelado'], [
        Service.query.filter_by(status='pending').count(),
        Service.query.filter_by(status='in_progress').count(),
        Service.query.filter_by(status='completed').count(),
        Service.query.filter_by(status='cancelled').count(),
    ]


def report_rankings() -> dict[str, Any]:
    top_clients = db.session.query(
        Client,
        func.count(Service.id).label('services_count'),
        func.coalesce(func.sum(Service.value), 0).label('total_value'),
    ).outerjoin(Service, Service.client_id == Client.id).group_by(Client.id).order_by(func.coalesce(func.sum(Service.value), 0).desc()).limit(6).all()

    top_team = employee_performance(limit=6)
    return {'top_clients': top_clients, 'top_team': top_team}
