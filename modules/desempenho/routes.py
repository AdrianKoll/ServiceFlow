import json
from flask import Blueprint, render_template

from core.auth import login_required, module_required
from services.analytics import employee_performance, core_kpis, service_activity_chart

bp = Blueprint('desempenho', __name__)

@bp.route('/desempenho')
@login_required
@module_required('desempenho')
def desempenho():
    rows = employee_performance()
    kpis = core_kpis()
    labels, created, completed = service_activity_chart(6)
    return render_template(
        'desempenho.html',
        rows=rows,
        kpis=kpis,
        chart_labels=json.dumps(labels),
        chart_created=json.dumps(created),
        chart_completed=json.dumps(completed),
    )
