from core.extensions import db
from core.model_base import TimestampMixin, TenantMixin

class Task(TenantMixin, TimestampMixin, db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.Text, nullable=False, default='todo')
    priority = db.Column(db.Text, nullable=False, default='medium')
    assignee_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'))
    due_date = db.Column(db.DateTime)
    assignee = db.relationship('User', backref='tasks', foreign_keys=[assignee_id])
    service = db.relationship('Service', backref='tasks', foreign_keys=[service_id])
