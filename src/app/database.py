__author__ = 'Yifu Huang'

from src.app import app
from src.app.functions import *
from flask.ext.sqlalchemy import SQLAlchemy
from datetime import datetime

app.config["SQLALCHEMY_DATABASE_URI"]= safe_get_config("mysql/connection", "mysql://root:root@localhost/azureautodeploy")
db = SQLAlchemy(app)


class UserInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    email = db.Column(db.String(100))
    create_time = db.Column(db.DateTime)
    last_login_time = db.Column(db.DateTime)

    def __init__(self, name, email, create_time=None, last_login_time=None):
        if create_time is None:
            create_time = datetime.utcnow()
        if last_login_time is None:
            last_login_time = datetime.utcnow()
        self.name = name
        self.email = email
        self.create_time = create_time
        self.last_login_time = last_login_time


class UserKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cert_url = db.Column(db.String(100))
    pem_url = db.Column(db.String(100))
    subscription_id = db.Column(db.String(100))
    management_host = db.Column(db.String(100))
    create_time = db.Column(db.DateTime)
    last_modify_time = db.Column(db.DateTime)
    user_info_id = db.Column(db.Integer, db.ForeignKey('user_info.id'))
    user_info = db.relationship('UserInfo', backref=db.backref('user_key', lazy='dynamic'))

    def __init__(self, user_info, cert_url, pem_url, subscription_id, management_host, create_time=None,
                 last_modify_time=None):
        if create_time is None:
            create_time = datetime.utcnow()
        if last_modify_time is None:
            last_modify_time = datetime.utcnow()
        self.user_info = user_info
        self.cert_url = cert_url
        self.pem_url = pem_url
        self.subscription_id = subscription_id
        self.management_host = management_host
        self.create_time = create_time
        self.last_modify_time = last_modify_time


class Template(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(100))
    type = db.Column(db.String(50))
    create_time = db.Column(db.DateTime)
    last_modify_time = db.Column(db.DateTime)

    def __init__(self, url, type, create_time=None, last_modify_time=None):
        if create_time is None:
            create_time = datetime.utcnow()
        if last_modify_time is None:
            last_modify_time = datetime.utcnow()
        self.url = url
        self.type = type
        self.create_time = create_time
        self.last_modify_time = last_modify_time


class UserTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    create_time = db.Column(db.DateTime)
    last_modify_time = db.Column(db.DateTime)
    user_info_id = db.Column(db.Integer, db.ForeignKey('user_info.id'))
    user_info = db.relationship('UserInfo', backref=db.backref('user_template', lazy='dynamic'))
    template_id = db.Column(db.Integer, db.ForeignKey('template.id'))
    template = db.relationship('Template', backref=db.backref('user_template', lazy='dynamic'))

    def __init__(self, user_info, template, create_time=None, last_modify_time=None):
        if create_time is None:
            create_time = datetime.utcnow()
        if last_modify_time is None:
            last_modify_time = datetime.utcnow()
        self.user_info = user_info
        self.template = template
        self.create_time = create_time
        self.last_modify_time = last_modify_time


class UserOperation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    operation = db.Column(db.String(50))
    status = db.Column(db.String(50))
    note = db.Column(db.String(500))
    exec_time = db.Column(db.DateTime)
    user_template_id = db.Column(db.Integer, db.ForeignKey('user_template.id'))
    user_template = db.relationship('UserTemplate', backref=db.backref('user_operation', lazy='dynamic'))

    def __init__(self, user_template, operation, status, note=None, exec_time=None):
        if exec_time is None:
            exec_time = datetime.utcnow()
        self.user_template = user_template
        self.operation = operation
        self.status = status
        self.note = note
        self.exec_time = exec_time


class UserResource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50))
    name = db.Column(db.String(50))
    status = db.Column(db.String(50))
    create_time = db.Column(db.DateTime)
    last_modify_time = db.Column(db.DateTime)
    user_template_id = db.Column(db.Integer, db.ForeignKey('user_template.id'))
    user_template = db.relationship('UserTemplate', backref=db.backref('user_resource1', lazy='dynamic'))
    cloud_service_id = db.Column(db.Integer, db.ForeignKey('user_resource.id'))
    cloud_service = db.relationship('UserResource')

    def __init__(self, user_template, type, name, status, cloud_service=None, create_time=None, last_modify_time=None):
        if create_time is None:
            create_time = datetime.utcnow()
        if last_modify_time is None:
            last_modify_time = datetime.utcnow()
        self.user_template = user_template
        self.type = type
        self.name = name
        self.status = status
        self.cloud_service = cloud_service
        self.create_time = create_time
        self.last_modify_time = last_modify_time


class VMEndpoint(db.Model):
    __tablename__ = 'vm_endpoint'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    protocol = db.Column(db.String(50))
    public_port = db.Column(db.Integer)
    private_port = db.Column(db.Integer)
    create_time = db.Column(db.DateTime)
    last_modify_time = db.Column(db.DateTime)
    cloud_service_id = db.Column(db.Integer, db.ForeignKey('user_resource.id'))
    cloud_service = db.relationship('UserResource', foreign_keys=[cloud_service_id],
                                    backref=db.backref('vm_endpoint1', lazy='dynamic'))
    virtual_machine_id = db.Column(db.Integer, db.ForeignKey('user_resource.id'))
    virtual_machine = db.relationship('UserResource', foreign_keys=[virtual_machine_id],
                                      backref=db.backref('vm_endpoint2', lazy='dynamic'))

    def __init__(self, name, protocol, public_port, private_port, cloud_service, virtual_machine=None,
                 create_time=None, last_modify_time=None):
        if create_time is None:
            create_time = datetime.utcnow()
        if last_modify_time is None:
            last_modify_time = datetime.utcnow()
        self.cloud_service = cloud_service
        self.virtual_machine = virtual_machine
        self.name = name
        self.protocol = protocol
        self.public_port = public_port
        self.private_port = private_port
        self.create_time = create_time
        self.last_modify_time = last_modify_time


class VMConfig(db.Model):
    __tablename__ = 'vm_config'
    id = db.Column(db.Integer, primary_key=True)
    dns = db.Column(db.String(50))
    public_ip = db.Column(db.String(50))
    private_ip = db.Column(db.String(50))
    create_time = db.Column(db.DateTime)
    last_modify_time = db.Column(db.DateTime)
    virtual_machine_id = db.Column(db.Integer, db.ForeignKey('user_resource.id'))
    virtual_machine = db.relationship('UserResource', backref=db.backref('vm_config', lazy='dynamic'))

    def __init__(self, virtual_machine, dns, public_ip, private_ip, create_time=None, last_modify_time=None):
        if create_time is None:
            create_time = datetime.utcnow()
        if last_modify_time is None:
            last_modify_time = datetime.utcnow()
        self.virtual_machine = virtual_machine
        self.dns = dns
        self.public_ip = public_ip
        self.private_ip = private_ip
        self.create_time = create_time
        self.last_modify_time = last_modify_time