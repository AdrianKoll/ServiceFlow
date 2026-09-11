import json
from flask import Blueprint, render_template, Response
from sqlalchemy import func
from services.analytics import core_kpis, status_distribution, finance_chart, report_rankings, employee_performance
from core.auth import login_required, module_required
from models import Service, Client, Transaction, db

bp = Blueprint('relatorios', __name__)

@bp.route('/relatorios')
@login_required
@module_required('relatorios')
def relatorios():
    kpis = core_kpis()
    status_labels, status_data = status_distribution()
    finance_labels, finance_income, finance_expense = finance_chart(6)
    rankings = report_rankings()
    return render_template(
        'relatorios.html',
        chart_status_labels=json.dumps(status_labels),
        chart_status_data=json.dumps(status_data),
        finance_labels=json.dumps(finance_labels),
        finance_income=json.dumps(finance_income),
        finance_expense=json.dumps(finance_expense),
        top_clients=rankings['top_clients'],
        top_team=rankings['top_team'],
        **kpis,
    )

@bp.route('/relatorios/exportar.csv')
@login_required
@module_required('relatorios')
def relatorios_exportar_csv():
    rows = ['tipo,total']
    rows.append(f"servicos,{Service.query.count()}")
    rows.append(f"servicos_concluidos,{Service.query.filter_by(status='completed').count()}")
    rows.append(f"servicos_em_andamento,{Service.query.filter_by(status='in_progress').count()}")
    rows.append(f"servicos_pendentes,{Service.query.filter_by(status='pending').count()}")
    rows.append(f"clientes,{Client.query.count()}")
    income = db.session.query(func.sum(Transaction.amount)).filter_by(type='income').scalar() or 0
    expense = db.session.query(func.sum(Transaction.amount)).filter_by(type='expense').scalar() or 0
    rows.append(f"receita,{float(income):.2f}")
    rows.append(f"despesas,{float(expense):.2f}")
    csv = '\n'.join(rows) + '\n'
    return Response(csv, mimetype='text/csv; charset=utf-8', headers={'Content-Disposition': 'attachment; filename=serviceflow_relatorio.csv'})
