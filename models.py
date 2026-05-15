from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.Text, nullable=False)
    email         = db.Column(db.Text, nullable=False, unique=True)
    phone         = db.Column(db.Text)
    role          = db.Column(db.Text, nullable=False, default='technician')
    status        = db.Column(db.Text, nullable=False, default='active')
    avatar        = db.Column(db.Text)
    department    = db.Column(db.Text)
    password_hash = db.Column(db.Text)
    client_id     = db.Column(db.Integer, db.ForeignKey('clients.id'))
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at    = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    client_link   = db.relationship('Client', foreign_keys=[client_id])

class Client(db.Model):
    __tablename__ = 'clients'
    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.Text, nullable=False)
    email      = db.Column(db.Text)
    phone      = db.Column(db.Text)
    company    = db.Column(db.Text)
    address    = db.Column(db.Text)
    city       = db.Column(db.Text)
    state      = db.Column(db.Text)
    status     = db.Column(db.Text, nullable=False, default='active')
    notes      = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Service(db.Model):
    __tablename__ = 'services'
    id             = db.Column(db.Integer, primary_key=True)
    title          = db.Column(db.Text, nullable=False)
    description    = db.Column(db.Text)
    client_id      = db.Column(db.Integer, db.ForeignKey('clients.id'))
    responsible_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    status         = db.Column(db.Text, nullable=False, default='pending')
    priority       = db.Column(db.Text, nullable=False, default='medium')
    value          = db.Column(db.Numeric(12, 2))
    due_date       = db.Column(db.DateTime)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at     = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    client         = db.relationship('Client', backref='services', foreign_keys=[client_id])
    responsible    = db.relationship('User', backref='services', foreign_keys=[responsible_id])

class Task(db.Model):
    __tablename__ = 'tasks'
    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    status      = db.Column(db.Text, nullable=False, default='todo')
    priority    = db.Column(db.Text, nullable=False, default='medium')
    assignee_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    service_id  = db.Column(db.Integer, db.ForeignKey('services.id'))
    due_date    = db.Column(db.DateTime)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    assignee    = db.relationship('User', backref='tasks', foreign_keys=[assignee_id])
    service     = db.relationship('Service', backref='tasks', foreign_keys=[service_id])

class Event(db.Model):
    __tablename__ = 'events'
    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    start_date  = db.Column(db.DateTime, nullable=False)
    end_date    = db.Column(db.DateTime)
    type        = db.Column(db.Text, nullable=False, default='other')
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'))
    service_id  = db.Column(db.Integer, db.ForeignKey('services.id'))
    location    = db.Column(db.Text)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user        = db.relationship('User', backref='events', foreign_keys=[user_id])

class Transaction(db.Model):
    __tablename__ = 'transactions'
    id          = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text, nullable=False)
    type        = db.Column(db.Text, nullable=False)
    amount      = db.Column(db.Numeric(12, 2), nullable=False)
    category    = db.Column(db.Text)
    status      = db.Column(db.Text, nullable=False, default='pending')
    service_id  = db.Column(db.Integer, db.ForeignKey('services.id'))
    client_id   = db.Column(db.Integer, db.ForeignKey('clients.id'))
    due_date    = db.Column(db.DateTime)
    paid_at     = db.Column(db.DateTime)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    client      = db.relationship('Client', backref='transactions', foreign_keys=[client_id])
    service     = db.relationship('Service', backref='transactions', foreign_keys=[service_id])

class MessageThread(db.Model):
    __tablename__ = 'message_threads'
    id         = db.Column(db.Integer, primary_key=True)
    title      = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    messages   = db.relationship('Message', backref='thread', lazy='dynamic', order_by='Message.created_at')

class ThreadParticipant(db.Model):
    __tablename__ = 'thread_participants'
    id        = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(db.Integer, db.ForeignKey('message_threads.id'), nullable=False)
    user_id   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

class Message(db.Model):
    __tablename__ = 'messages'
    id        = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(db.Integer, db.ForeignKey('message_threads.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    content   = db.Column(db.Text, nullable=False)
    edited_at = db.Column(db.DateTime, nullable=True)
    created_at= db.Column(db.DateTime, default=datetime.utcnow)
    sender    = db.relationship('User', backref='messages', foreign_keys=[sender_id])

class Notification(db.Model):
    __tablename__ = 'notifications'
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'))
    title      = db.Column(db.Text, nullable=False)
    content    = db.Column(db.Text, nullable=False)
    type       = db.Column(db.Text, nullable=False, default='info')
    read       = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
