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

bp = Blueprint('mensagens', __name__)


def _thread_for_user(thread_id, user, require_participant=True):
    """Retorna apenas conversas do tenant atual e, por padrão, do usuário atual."""
    query = MessageThread.query.filter_by(id=thread_id, tenant_id=user.tenant_id)
    if require_participant:
        query = query.join(ThreadParticipant).filter(ThreadParticipant.user_id == user.id)
    return query.first_or_404()

@bp.route('/mensagens')
@login_required
@module_required('mensagens')
def mensagens():
    current_user = get_current_user()
    thread_id    = request.args.get('thread', type=int)
    threads_query = MessageThread.query.join(ThreadParticipant).filter(
        MessageThread.tenant_id == current_user.tenant_id,
        ThreadParticipant.user_id == current_user.id,
    )
    threads = threads_query.order_by(MessageThread.updated_at.desc()).all()
    active_thread, thread_messages = None, []

    if thread_id:
        active_thread = _thread_for_user(thread_id, current_user)
        if active_thread:
            thread_messages = db.session.query(Message, User.name.label('sender_name'))\
                .outerjoin(User, (Message.sender_id == User.id) & (User.tenant_id == current_user.tenant_id))\
                .filter(Message.thread_id == active_thread.id)\
                .order_by(Message.created_at).all()

    employees = User.query.filter(
        User.status == 'active', User.role.in_(EMPLOYEE_ROLES), User.tenant_id == current_user.tenant_id
    ).order_by(User.role, User.name).all()
    users_by_role = {}
    for u in employees:
        users_by_role.setdefault(u.role, []).append(u)

    return render_template('mensagens.html',
        threads=threads, active_thread=active_thread,
        thread_messages=thread_messages,
        users=employees, users_by_role=users_by_role,
        thread_id=thread_id, current_user_id=current_user.id,
        threads_total=len(threads), messages_total=Message.query.join(MessageThread).filter(
            MessageThread.tenant_id == current_user.tenant_id
        ).count(), employees_total=len(employees))

@bp.route('/mensagens/novo-thread', methods=['POST'])
@login_required
@module_required('mensagens')
def mensagem_novo_thread():
    title = request.form.get('title', '').strip()
    if not title:
        flash('Informe um nome para a conversa.', 'warning')
        return redirect(url_for('mensagens.mensagens'))
    current_user = get_current_user()
    t = MessageThread(title=title, tenant_id=current_user.tenant_id)
    db.session.add(t)
    db.session.flush()
    valid_ids = {str(u.id) for u in User.query.filter(
        User.role.in_(EMPLOYEE_ROLES), User.tenant_id == current_user.tenant_id
    ).all()}
    db.session.add(ThreadParticipant(thread_id=t.id, user_id=current_user.id))
    for uid in request.form.getlist('participant_ids'):
        if uid in valid_ids:
            db.session.add(ThreadParticipant(thread_id=t.id, user_id=int(uid)))
    initial_msg = request.form.get('initial_message', '').strip()
    if initial_msg:
        db.session.add(Message(thread_id=t.id,
            sender_id=session['user_id'], content=initial_msg))
    db.session.commit()
    flash('Conversa criada!', 'success')
    return redirect(url_for('mensagens.mensagens', thread=t.id))

@bp.route('/mensagens/<int:thread_id>/enviar', methods=['POST'])
@login_required
@module_required('mensagens')
def mensagem_enviar(thread_id):
    current_user = get_current_user()
    thread = _thread_for_user(thread_id, current_user)
    content = request.form.get('content', '').strip()
    if not content:
        flash('Mensagem não pode ser vazia.', 'warning')
        return redirect(url_for('mensagens.mensagens', thread=thread_id))
    m = Message(thread_id=thread.id, sender_id=current_user.id, content=content)
    db.session.add(m)
    thread.updated_at = datetime.utcnow()
    db.session.commit()
    return redirect(url_for('mensagens.mensagens', thread=thread_id))

@bp.route('/mensagens/<int:thread_id>/mensagem/<int:msg_id>/editar', methods=['POST'])
@login_required
@module_required('mensagens')
def mensagem_editar(thread_id, msg_id):
    current_user = get_current_user()
    _thread_for_user(thread_id, current_user)
    msg = Message.query.filter_by(
        id=msg_id, thread_id=thread_id, sender_id=current_user.id
    ).first_or_404()
    content = request.form.get('content', '').strip()
    if not content:
        flash('O conteúdo não pode ser vazio.', 'warning')
        return redirect(url_for('mensagens.mensagens', thread=thread_id))
    msg.content   = content
    msg.edited_at = datetime.utcnow()
    db.session.commit()
    flash('Mensagem editada.', 'success')
    return redirect(url_for('mensagens.mensagens', thread=thread_id))

@bp.route('/mensagens/<int:thread_id>/mensagem/<int:msg_id>/excluir', methods=['POST'])
@login_required
@module_required('mensagens')
def mensagem_excluir(thread_id, msg_id):
    current_user = get_current_user()
    _thread_for_user(thread_id, current_user)
    msg = Message.query.filter_by(
        id=msg_id, thread_id=thread_id, sender_id=current_user.id
    ).first_or_404()
    db.session.delete(msg)
    db.session.commit()
    flash('Mensagem excluída.', 'success')
    return redirect(url_for('mensagens.mensagens', thread=thread_id))

@bp.route('/mensagens/<int:thread_id>/excluir', methods=['POST'])
@login_required
@role_required('admin', 'manager')
def thread_excluir(thread_id):
    current_user = get_current_user()
    thread = _thread_for_user(thread_id, current_user, require_participant=False)
    ThreadParticipant.query.filter_by(thread_id=thread_id).delete()
    Message.query.filter_by(thread_id=thread_id).delete()
    db.session.delete(thread)
    db.session.commit()
    flash('Conversa excluída.', 'success')
    return redirect(url_for('mensagens.mensagens'))
