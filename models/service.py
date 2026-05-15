from core.extensions import db
from core.model_base import TimestampMixin, TenantMixin

class Service(TenantMixin, TimestampMixin, db.Model):
    __tablename__ = 'services'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'))
    responsible_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    status = db.Column(db.Text, nullable=False, default='pending')
    priority = db.Column(db.Text, nullable=False, default='medium')
    value = db.Column(db.Numeric(12, 2))
    due_date = db.Column(db.DateTime)
    client = db.relationship('Client', backref='services', foreign_keys=[client_id])
    responsible = db.relationship('User', backref='services', foreign_keys=[responsible_id])
