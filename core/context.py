from datetime import datetime
from .auth import get_current_user, get_notifications, get_unread_count, can_access
from .constants import ROLE_LABELS, ROLE_ABBR, ROLE_ACCESS
from .formatters import get_initials, darken_hex, hex_alpha
from services.plans import PLAN_CATALOG, get_current_plan, trial_days_left, user_has_feature, get_usage_summary, plan_features_matrix

def register_context_processors(app):
    @app.context_processor
    def inject_globals():
        current_user  = get_current_user()
        notifications = get_notifications()
        unread_count  = get_unread_count()
        from flask import session, url_for
        theme         = session.get('theme', 'dark')
        primary_color = session.get('primary_color', '#2563eb')
        font_size     = session.get('font_size', '14')
        avatar_color  = session.get('avatar_color', '#2563eb')
        avatar_url = url_for('static', filename=current_user.avatar) if current_user and current_user.avatar else None
        role          = current_user.role if current_user else 'admin'
        current_plan  = get_current_plan(current_user) if current_user else PLAN_CATALOG['basic']
        tenant        = getattr(current_user, 'tenant', None) if current_user else None
        return dict(
            current_user=current_user, notifications=notifications, unread_count=unread_count,
            theme=theme, primary_color=primary_color, primary_hover=darken_hex(primary_color),
            primary_alpha=hex_alpha(primary_color), font_size=font_size, avatar_color=avatar_color,
            user_initials=get_initials(current_user.name) if current_user else 'SF',
            user_avatar_url=avatar_url,
            user_role_label=ROLE_LABELS.get(role, role.title()),
            user_role_abbr=ROLE_ABBR.get(role, role[:2].upper()),
            can_access=can_access, ROLE_ACCESS=ROLE_ACCESS,
            current_plan=current_plan, plan_catalog=PLAN_CATALOG,
            trial_days_left=trial_days_left(tenant),
            billing_status=getattr(tenant, 'billing_status', 'trial') if tenant else 'trial',
            user_has_feature=lambda feature: user_has_feature(current_user, feature),
            usage_summary=get_usage_summary(current_user) if current_user else [],
            plan_features_matrix=plan_features_matrix,
            now=datetime.utcnow,
        )
