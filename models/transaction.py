from core.extensions import db
from core.model_base import TimestampMixin, TenantMixin

class Transaction(TenantMixin, TimestampMixin, db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text, nullable=False)
    type = db.Column(db.Text, nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    category = db.Column(db.Text)
    status = db.Column(db.Text, nullable=False, default='pending')
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'))
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'))
    due_date = db.Column(db.DateTime)
    paid_at = db.Column(db.DateTime)
    client = db.relationship('Client', backref='transactions', foreign_keys=[client_id])
    service = db.relationship('Service', backref='transactions', foreign_keys=[service_id])
