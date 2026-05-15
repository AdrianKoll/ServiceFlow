from core.extensions import db
from core.model_base import TimestampMixin, TenantMixin

class User(TenantMixin, TimestampMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    email = db.Column(db.Text, nullable=False, unique=True)
    phone = db.Column(db.Text)
    role = db.Column(db.Text, nullable=False, default='technician')
    status = db.Column(db.Text, nullable=False, default='active')
    avatar = db.Column(db.Text)
    department = db.Column(db.Text)
    password_hash = db.Column(db.Text)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'))
    client_link = db.relationship('Client', foreign_keys=[client_id])
