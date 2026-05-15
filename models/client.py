from core.extensions import db
from core.model_base import TimestampMixin, TenantMixin

class Client(TenantMixin, TimestampMixin, db.Model):
    __tablename__ = 'clients'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    email = db.Column(db.Text)
    phone = db.Column(db.Text)
    company = db.Column(db.Text)
    address = db.Column(db.Text)
    city = db.Column(db.Text)
    state = db.Column(db.Text)
    status = db.Column(db.Text, nullable=False, default='active')
    notes = db.Column(db.Text)
