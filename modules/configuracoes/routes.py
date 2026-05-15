import re
import os
from uuid import uuid4
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.utils import secure_filename
from sqlalchemy import func
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, User
from core.auth import get_current_user, login_required, role_required

bp = Blueprint('configuracoes', __name__)

INTEGRATION_CATALOG = [
    {'slug': 'whatsapp', 'name': 'WhatsApp Business', 'desc': 'Envie mensagens automáticas para clientes e acompanhe confirmações.', 'icon': '💬', 'stage': 'Em implantação'},
    {'slug': 'calendar', 'name': 'Google Calendar', 'desc': 'Sincronize agenda, reuniões e prazos com o calendário externo.', 'icon': '📅', 'stage': 'Planejado'},
    {'slug': 'payments', 'name': 'Stripe / Pagar.me', 'desc': 'Receba pagamentos online e vincule transações ao financeiro.', 'icon': '💳', 'stage': 'Em implantação'},
    {'slug': 'slack', 'name': 'Slack', 'desc': 'Receba alertas operacionais em canais internos da equipe.', 'icon': '🔔', 'stage': 'Planejado'},
    {'slug': 'zapier', 'name': 'Zapier', 'desc': 'Automatize fluxos de trabalho com ferramentas externas.', 'icon': '⚡', 'stage': 'Planejado'},
]




def _allowed_profile_image(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config.get('PROFILE_ALLOWED_EXTENSIONS', set())


def _profile_upload_dir() -> str:
    folder = current_app.config.get('PROFILE_UPLOAD_FOLDER', 'uploads/profiles')
    path = os.path.join(current_app.static_folder, folder)
    os.makedirs(path, exist_ok=True)
    return path


def _remove_profile_file(relative_path: str) -> None:
    if not relative_path or not relative_path.startswith('uploads/profiles/'):
        return
    full_path = os.path.join(current_app.static_folder, relative_path)
    try:
        if os.path.exists(full_path):
            os.remove(full_path)
    except OSError:
        pass

def _settings_redirect(tab: str):
    return redirect(url_for('configuracoes.configuracoes') + f'?tab={tab}')


@bp.route('/toggle-theme', methods=['POST'])
def toggle_theme():
    current = session.get('theme', 'dark')
    session['theme'] = 'light' if current == 'dark' else 'dark'
    return redirect(request.referrer or url_for('main.dashboard'))


@bp.route('/meu-perfil')
@login_required
def meu_perfil():
    return _settings_redirect('perfil')


@bp.route('/configuracoes')
@login_required
def configuracoes():
    connected = set(session.get('connected_integrations', []))
    integrations = [dict(item, connected=item['slug'] in connected) for item in INTEGRATION_CATALOG]
    company_settings = session.get('company_settings', {})
    notification_settings = session.get('notification_settings', {})
    return render_template(
        'configuracoes.html',
        integrations=integrations,
        company_settings=company_settings,
        notification_settings=notification_settings,
    )


@bp.route('/configuracoes/geral', methods=['POST'])
@login_required
@role_required('admin')
def salvar_geral():
    session['company_settings'] = {
        'company_name': request.form.get('company_name', '').strip() or 'ServiceFlow Pro',
        'cnpj': request.form.get('cnpj', '').strip(),
        'phone': request.form.get('phone', '').strip(),
        'address': request.form.get('address', '').strip(),
        'contact_email': request.form.get('contact_email', '').strip().lower(),
    }
    flash('Configurações gerais salvas para este ambiente de teste.', 'success')
    return _settings_redirect('geral')


@bp.route('/configuracoes/aparencia', methods=['POST'])
@login_required
def salvar_aparencia():
    color = request.form.get('primary_color', '').strip()
    size = request.form.get('font_size', '14').strip()
    if re.match(r'^#([0-9a-fA-F]{3}){1,2}$', color):
        session['primary_color'] = color
    if size in ('12', '13', '14', '15', '16', '18'):
        session['font_size'] = size
    flash('Aparência atualizada!', 'success')
    return _settings_redirect('aparencia')


@bp.route('/configuracoes/notificacoes', methods=['POST'])
@login_required
def salvar_notificacoes():
    allowed = {'service_created', 'service_completed', 'task_assigned', 'deadline_soon', 'new_messages', 'system_updates'}
    selected = set(request.form.getlist('notifications')) & allowed
    session['notification_settings'] = {key: key in selected for key in allowed}
    flash('Preferências de notificação salvas.', 'success')
    return _settings_redirect('notificacoes')


@bp.route('/configuracoes/integracoes/<slug>/alternar', methods=['POST'])
@login_required
@role_required('admin')
def alternar_integracao(slug):
    valid = {item['slug'] for item in INTEGRATION_CATALOG}
    if slug not in valid:
        flash('Integração inválida.', 'danger')
        return _settings_redirect('integracoes')

    connected = set(session.get('connected_integrations', []))
    if slug in connected:
        connected.remove(slug)
        flash('Integração desconectada no ambiente de teste.', 'info')
    else:
        connected.add(slug)
        flash('Integração marcada como conectada no ambiente de teste.', 'success')
    session['connected_integrations'] = sorted(connected)
    return _settings_redirect('integracoes')


@bp.route('/configuracoes/senha', methods=['POST'])
@login_required
def alterar_senha():
    user = get_current_user()
    senha_atual = request.form.get('senha_atual', '').strip()
    nova_senha = request.form.get('nova_senha', '').strip()
    confirmar_senha = request.form.get('confirmar_senha', '').strip()
    if not user.password_hash or not check_password_hash(user.password_hash, senha_atual):
        flash('Senha atual incorreta.', 'danger')
        return _settings_redirect('seguranca')
    if len(nova_senha) < 6:
        flash('A nova senha deve ter no mínimo 6 caracteres.', 'danger')
        return _settings_redirect('seguranca')
    if nova_senha != confirmar_senha:
        flash('As senhas não coincidem.', 'danger')
        return _settings_redirect('seguranca')
    user.password_hash = generate_password_hash(nova_senha)
    db.session.commit()
    flash('Senha alterada com sucesso!', 'success')
    return _settings_redirect('seguranca')


@bp.route('/configuracoes/perfil', methods=['POST'])
@login_required
def salvar_perfil():
    user = get_current_user()
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip().lower()
    avatar_color = request.form.get('avatar_color', '').strip()
    avatar_file = request.files.get('profile_image')

    if not name:
        flash('O nome não pode estar vazio.', 'danger')
        return _settings_redirect('perfil')
    if email and email != user.email:
        exists = User.query.filter(func.lower(User.email) == email, User.id != user.id).first()
        if exists:
            flash('Este e-mail já está em uso.', 'danger')
            return _settings_redirect('perfil')

    user.name = name
    if email:
        user.email = email
    if re.match(r'^#([0-9a-fA-F]{3}){1,2}$', avatar_color):
        session['avatar_color'] = avatar_color

    if avatar_file and avatar_file.filename:
        if not _allowed_profile_image(avatar_file.filename):
            flash('Formato de imagem inválido. Use PNG, JPG, JPEG, WEBP ou GIF.', 'danger')
            return _settings_redirect('perfil')
        filename = secure_filename(avatar_file.filename)
        ext = filename.rsplit('.', 1)[1].lower()
        new_filename = f'user_{user.id}_{uuid4().hex[:12]}.{ext}'
        upload_dir = _profile_upload_dir()
        avatar_file.save(os.path.join(upload_dir, new_filename))
        _remove_profile_file(user.avatar)
        user.avatar = f"uploads/profiles/{new_filename}"

    db.session.commit()
    flash('Perfil atualizado com sucesso!', 'success')
    return _settings_redirect('perfil')


@bp.route('/configuracoes/perfil/remover-imagem', methods=['POST'])
@login_required
def remover_imagem_perfil():
    user = get_current_user()
    _remove_profile_file(user.avatar)
    user.avatar = None
    db.session.commit()
    flash('Imagem de perfil removida.', 'info')
    return _settings_redirect('perfil')
