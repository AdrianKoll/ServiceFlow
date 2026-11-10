from __future__ import annotations

import calendar
from datetime import datetime
from typing import Any

from sqlalchemy import extract, func, and_

from core.constants import EMPLOYEE_ROLES
from core.tenant_policy import current_tenant_id, scoped_query
from models import Client, Service, Task, Transaction, User, db


def _now() -> datetime:
    return datetime.utcnow()


def _month_bounds(reference: datetime | None = None) -> tuple[datetime, datetime]:
    ref = reference or _now()
    start = datetime(ref.year, ref.month, 1)
    end = datetime(ref.year + 1, 1, 1) if ref.month == 12 else datetime(ref.year, ref.month + 1, 1)
    return start, end


def _safe_pct(part: int | float, total: int | float) -> int:
    return 0 if not total else round((part / total) * 100)


def core_kpis() -> dict[str, Any]:
    tenant_id = current_tenant_id()
    month_start, month_end = _month_bounds()
    prev_month_end = month_start
    prev_month_start = (
        datetime(month_start.year - 1, 12, 1)
        if month_start.month == 1
        else datetime(month_start.year, month_start.month - 1, 1)
    )

    services = scoped_query(Service)
    tasks = scoped_query(Task)
    transactions = scoped_query(Transaction)
    svc_total = services.count()
    svc_completed = services.filter_by(status="completed").count()
    svc_pending = services.filter_by(status="pending").count()
    svc_inprogress = services.filter_by(status="in_progress").count()
    svc_cancelled = services.filter_by(status="cancelled").count()

    services_month = services.filter(
        Service.created_at >= month_start, Service.created_at < month_end
    ).count()
    services_prev = services.filter(
        Service.created_at >= prev_month_start, Service.created_at < prev_month_end
    ).count()
    service_growth = _safe_pct(services_month - services_prev, services_prev) if services_prev else (100 if services_month else 0)

    income_month = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.tenant_id == tenant_id,
        Transaction.type == "income",
        Transaction.created_at >= month_start,
        Transaction.created_at < month_end,
    ).scalar() or 0
    expense_month = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.tenant_id == tenant_id,
        Transaction.type == "expense",
        Transaction.created_at >= month_start,
        Transaction.created_at < month_end,
    ).scalar() or 0

    today = _now()
    overdue_services = services.filter(
        Service.status.notin_(["completed", "cancelled"]),
        Service.due_date.isnot(None),
        Service.due_date < today,
    ).count()
    overdue_tasks = tasks.filter(
        Task.status.notin_(["done"]),
        Task.due_date.isnot(None),
        Task.due_date < today,
    ).count()
    open_tasks = tasks.filter(Task.status.notin_(["done"])).count()
    completed_tasks = tasks.filter_by(status="done").count()

    return {
        "svc_total": svc_total,
        "svc_pending": svc_pending,
        "svc_inprogress": svc_inprogress,
        "svc_completed": svc_completed,
        "svc_cancelled": svc_cancelled,
        "client_total": scoped_query(Client).count(),
        "user_total": scoped_query(User).filter(User.role.in_(EMPLOYEE_ROLES)).count(),
        "revenue_total": transactions.filter_by(type="income").with_entities(func.sum(Transaction.amount)).scalar() or 0,
        "services_month": services_month,
        "service_growth": service_growth,
        "income_month": income_month,
        "expense_month": expense_month,
        "balance_month": income_month - expense_month,
        "completion_rate": _safe_pct(svc_completed, svc_total),
        "task_completion_rate": _safe_pct(completed_tasks, completed_tasks + open_tasks),
        "overdue_services": overdue_services,
        "overdue_tasks": overdue_tasks,
    }


def service_activity_chart(months: int = 6) -> tuple[list[str], list[int], list[int]]:
    tenant_id = current_tenant_id()
    today = _now()
    labels, created, completed = [], [], []
    for i in range(months - 1, -1, -1):
        m, y = today.month - i, today.year
        while m <= 0:
            m += 12
            y -= 1
        labels.append(f"{calendar.month_abbr[m]}/{str(y)[2:]}")
        base = scoped_query(Service).filter(
            extract("month", Service.created_at) == m,
            extract("year", Service.created_at) == y,
        )
        created.append(base.count())
        completed.append(base.filter(Service.status == "completed").count())
    return labels, created, completed


def finance_chart(months: int = 6) -> tuple[list[str], list[float], list[float]]:
    tenant_id = current_tenant_id()
    today = _now()
    labels, incomes, expenses = [], [], []
    for i in range(months - 1, -1, -1):
        m, y = today.month - i, today.year
        while m <= 0:
            m += 12
            y -= 1
        labels.append(f"{calendar.month_abbr[m]}/{str(y)[2:]}")
        common = (
            Transaction.tenant_id == tenant_id,
            extract("month", Transaction.created_at) == m,
            extract("year", Transaction.created_at) == y,
        )
        incomes.append(float(db.session.query(func.sum(Transaction.amount)).filter(Transaction.type == "income", *common).scalar() or 0))
        expenses.append(float(db.session.query(func.sum(Transaction.amount)).filter(Transaction.type == "expense", *common).scalar() or 0))
    return labels, incomes, expenses


def employee_performance(limit: int | None = None) -> list[dict[str, Any]]:
    users = scoped_query(User).filter(User.role.in_(EMPLOYEE_ROLES)).order_by(User.name.asc()).all()
    today = _now()
    rows: list[dict[str, Any]] = []
    for user in users:
        task_query = scoped_query(Task).filter(Task.assignee_id == user.id)
        service_query = scoped_query(Service).filter(Service.responsible_id == user.id)
        task_total = task_query.count()
        task_done = task_query.filter_by(status="done").count()
        task_overdue = task_query.filter(
            Task.status != "done", Task.due_date.isnot(None), Task.due_date < today
        ).count()
        services_total = service_query.count()
        services_completed = service_query.filter_by(status="completed").count()
        completion = _safe_pct(task_done + services_completed, task_total + services_total)
        quality_penalty = min(35, task_overdue * 8)
        score = max(0, min(100, completion - quality_penalty + (5 if user.status == "active" else -10)))
        rows.append({
            "user": user,
            "task_total": task_total,
            "task_done": task_done,
            "task_overdue": task_overdue,
            "services_total": services_total,
            "services_completed": services_completed,
            "completion": completion,
            "score": score,
            "risk": "high" if task_overdue >= 3 else ("medium" if task_overdue else "low"),
        })
    rows.sort(key=lambda row: (row["score"], row["task_done"] + row["services_completed"]), reverse=True)
    return rows[:limit] if limit else rows


def recent_activity(limit: int = 8) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for service in scoped_query(Service).order_by(Service.created_at.desc()).limit(limit).all():
        items.append({"type": "service", "title": service.title, "description": "Serviço criado/atualizado", "date": service.created_at, "status": service.status})
    for client in scoped_query(Client).order_by(Client.created_at.desc()).limit(limit).all():
        items.append({"type": "client", "title": client.name, "description": "Cliente cadastrado", "date": client.created_at, "status": client.status})
    for task in scoped_query(Task).order_by(Task.created_at.desc()).limit(limit).all():
        items.append({"type": "task", "title": task.title, "description": "Tarefa registrada", "date": task.created_at, "status": task.status})
    for transaction in scoped_query(Transaction).order_by(Transaction.created_at.desc()).limit(limit).all():
        items.append({"type": "finance", "title": transaction.description, "description": "Movimento financeiro", "date": transaction.created_at, "status": transaction.status})
    items.sort(key=lambda item: item.get("date") or datetime.min, reverse=True)
    return items[:limit]


def status_distribution() -> tuple[list[str], list[int]]:
    services = scoped_query(Service)
    return ["Pendente", "Em Andamento", "Concluído", "Cancelado"], [
        services.filter_by(status="pending").count(),
        services.filter_by(status="in_progress").count(),
        services.filter_by(status="completed").count(),
        services.filter_by(status="cancelled").count(),
    ]


def report_rankings() -> dict[str, Any]:
    tenant_id = current_tenant_id()
    top_clients = db.session.query(
        Client,
        func.count(Service.id).label("services_count"),
        func.coalesce(func.sum(Service.value), 0).label("total_value"),
    ).outerjoin(
        Service,
        and_(Service.client_id == Client.id, Service.tenant_id == tenant_id),
    ).filter(
        Client.tenant_id == tenant_id,
    ).group_by(Client.id).order_by(
        func.coalesce(func.sum(Service.value), 0).desc()
    ).limit(6).all()
    return {"top_clients": top_clients, "top_team": employee_performance(limit=6)}
