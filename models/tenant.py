from core.extensions import db
from core.model_base import TimestampMixin

class Tenant(TimestampMixin, db.Model):
    __tablename__ = 'tenants'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    slug = db.Column(db.Text, unique=True, index=True)
    status = db.Column(db.Text, nullable=False, default='active')
    plan = db.Column(db.Text, nullable=False, default='basic')
    billing_status = db.Column(db.Text, nullable=False, default='trial')
    trial_ends_at = db.Column(db.DateTime)
    subscription_started_at = db.Column(db.DateTime)
    subscription_ends_at = db.Column(db.DateTime)
    payment_method = db.Column(db.Text)
    billing_cycle = db.Column(db.Text, nullable=False, default='monthly')
    next_invoice_at = db.Column(db.DateTime)
    last_payment_at = db.Column(db.DateTime)
    cancel_at_period_end = db.Column(db.Boolean, nullable=False, default=False)
    billing_email = db.Column(db.Text)
