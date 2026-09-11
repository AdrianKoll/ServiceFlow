from core.extensions import db
from core.model_base import TimestampMixin, TenantMixin

class MessageThread(TenantMixin, TimestampMixin, db.Model):
    __tablename__ = 'message_threads'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False)
    messages = db.relationship('Message', backref='thread', lazy='dynamic', order_by='Message.created_at')

class ThreadParticipant(db.Model):
    __tablename__ = 'thread_participants'
    id = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(db.Integer, db.ForeignKey('message_threads.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

class Message(TimestampMixin, db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(db.Integer, db.ForeignKey('message_threads.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    content = db.Column(db.Text, nullable=False)
    edited_at = db.Column(db.DateTime, nullable=True)
    sender = db.relationship('User', backref='messages', foreign_keys=[sender_id])
