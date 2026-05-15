from core.extensions import db
from core.model_base import TimestampMixin, TenantMixin

class Event(TenantMixin, TimestampMixin, db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime)
    type = db.Column(db.Text, nullable=False, default='other')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'))
    location = db.Column(db.Text)
    user = db.relationship('User', backref='events', foreign_keys=[user_id])
