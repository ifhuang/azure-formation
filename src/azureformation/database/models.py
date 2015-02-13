__author__ = 'Yifu Huang'

from src.azureformation.database import db
from src.azureformation.log import log
from datetime import datetime
import json


def to_json(inst, cls):
    # add your conversions for things like datetime
    # and what-not that aren't serializable.
    convert = dict()
    convert[db.DateTime] = str
    d = dict()
    for c in cls.__table__.columns:
        v = getattr(inst, c.name)
        if c.type.__class__ in convert.keys() and v is not None:
            try:
                func = convert[c.type.__class__]
                d[c.name] = func(v)
            except Exception as e:
                log.error(e)
                d[c.name] = "Error:  Failed to covert using ", str(convert[c.type.__class__])
        elif v is None:
            d[c.name] = str()
        else:
            d[c.name] = v
    return json.dumps(d)


class User(db.Model):
    """
    Just a placeholder of user
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))

    def __init__(self, name):
        self.name = name

    def json(self):
        return to_json(self, self.__class__)

    def __repr__(self):
        return '%s: %s' % (User.__name__, self.json())


class Hackathon(db.Model):
    """
    Just a placeholder of hackathon
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))

    def __init__(self, name):
        self.name = name

    def json(self):
        return to_json(self, self.__class__)

    def __repr__(self):
        return '%s: %s' % (Hackathon.__name__, self.json())


class AzureKey(db.Model):
    """
    Azure certificates info of User or Hackathon
    """
    id = db.Column(db.Integer, primary_key=True)
    cert_url = db.Column(db.String(200))
    pem_url = db.Column(db.String(200))
    subscription_id = db.Column(db.String(100))
    management_host = db.Column(db.String(100))
    # AKOwner in enum.py
    owner = db.Column(db.Integer)
    # None if owner is Hackathon
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    user = db.relationship('User', backref=db.backref('azure_key1', lazy='dynamic'))
    # None if owner is User
    hackathon_id = db.Column(db.Integer, db.ForeignKey('hackathon.id', ondelete='CASCADE'))
    hackathon = db.relationship('Hackathon', backref=db.backref('azure_key2', lazy='dynamic'))
    create_time = db.Column(db.DateTime)
    last_modify_time = db.Column(db.DateTime)

    def __init__(self, **kwargs):
        super(AzureKey, self).__init__(**kwargs)
        if self.create_time is None:
            self.create_time = datetime.utcnow()
        if self.last_modify_time is None:
            self.last_modify_time = datetime.utcnow()

    def json(self):
        return to_json(self, self.__class__)

    def __repr__(self):
        return '%s: %s' % (AzureKey.__name__, self.json())


class Template(db.Model):
    """
    Just a placeholder of template
    """
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(200))

    def __init__(self, url):
        self.url = url

    def json(self):
        return to_json(self, self.__class__)

    def __repr__(self):
        return '%s: %s' % (Template.__name__, self.json())


class Experiment(db.Model):
    """
    Experiment is launched once template is used:
    1. user use template directly
    2. user use template via hackathon
    """
    id = db.Column(db.Integer, primary_key=True)
    # ExperimentStatus in enum.py
    status = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    user = db.relationship('User', backref=db.backref('experiment1', lazy='dynamic'))
    template_id = db.Column(db.Integer, db.ForeignKey('template.id', ondelete='CASCADE'))
    template = db.relationship('Template', backref=db.backref('experiment2', lazy='dynamic'))
    # None if user use template directly
    hackathon_id = db.Column(db.Integer, db.ForeignKey('hackathon.id', ondelete='CASCADE'))
    hackathon = db.relationship('Hackathon', backref=db.backref('experiment3', lazy='dynamic'))
    create_time = db.Column(db.DateTime)
    last_heart_beat_time = db.Column(db.DateTime)

    def __init__(self, **kwargs):
        super(Experiment, self).__init__(**kwargs)
        if self.create_time is None:
            self.create_time = datetime.utcnow()
        if self.last_heart_beat_time is None:
            self.last_heart_beat_time = datetime.utcnow()

    def json(self):
        return to_json(self, self.__class__)

    def __repr__(self):
        return '%s: %s' % (Experiment.__name__, self.json())


class VirtualEnvironment(db.Model):
    """
    Virtual environment is abstraction of smallest unit in template
    """
    id = db.Column(db.Integer, primary_key=True)
    # VEProvider in enum.py
    provider = db.Column(db.Integer)
    name = db.Column(db.String(100))
    image = db.Column(db.String(100))
    # VEStatus in enum.py
    status = db.Column(db.Integer)
    # VERemoteProvider in enum.py
    remote_provider = db.Column(db.Integer)
    remote_paras = db.Column(db.String(300))
    experiment_id = db.Column(db.Integer, db.ForeignKey('experiment.id', ondelete='CASCADE'))
    experiment = db.relationship('Experiment', backref=db.backref('virtual_environment', lazy='dynamic'))
    create_time = db.Column(db.DateTime)

    def __init__(self, **kwargs):
        super(VirtualEnvironment, self).__init__(**kwargs)
        if self.create_time is None:
            self.create_time = datetime.utcnow()

    def json(self):
        return to_json(self, self.__class__)

    def __repr__(self):
        return '%s: %s' % (VirtualEnvironment.__name__, self.json())


class AzureLog(db.Model):
    """
    Azure log for every experiment
    """
    id = db.Column(db.Integer, primary_key=True)
    operation = db.Column(db.String(50))
    status = db.Column(db.String(50))
    note = db.Column(db.String(500))
    experiment_id = db.Column(db.Integer, db.ForeignKey('experiment.id', ondelete='CASCADE'))
    experiment = db.relationship('Experiment', backref=db.backref('azure_log', lazy='dynamic'))
    exec_time = db.Column(db.DateTime)

    def __init__(self, **kwargs):
        super(AzureLog, self).__init__(**kwargs)
        if self.exec_time is None:
            self.exec_time = datetime.utcnow()

    def json(self):
        return to_json(self, self.__class__)

    def __repr__(self):
        return '%s: %s' % (AzureLog.__name__, self.json())


class AzureResource(db.Model):
    """
    For storage account, cloud service and deployment
    """
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50))
    name = db.Column(db.String(50))
    status = db.Column(db.String(50))
    experiment_id = db.Column(db.Integer, db.ForeignKey('experiment.id', ondelete='CASCADE'))
    experiment = db.relationship('Experiment', backref=db.backref('azure_resource', lazy='dynamic'))
    # for deployment
    cloud_service_id = db.Column(db.Integer, db.ForeignKey('azure_resource.id', ondelete='CASCADE'))
    create_time = db.Column(db.DateTime)
    last_modify_time = db.Column(db.DateTime)

    def __init__(self, **kwargs):
        super(AzureResource, self).__init__(**kwargs)
        if self.create_time is None:
            self.create_time = datetime.utcnow()
        if self.last_modify_time is None:
            self.last_modify_time = datetime.utcnow()

    def json(self):
        return to_json(self, self.__class__)

    def __repr__(self):
        return '%s: %s' % (AzureResource.__name__, self.json())


class AzureVM(db.Model):
    """
    For virtual machine
    """
    __tablename__ = 'azure_vm'
    id = db.Column(db.Integer, primary_key=True)
    cloud_service_name = db.Column(db.String(50))
    deployment_name = db.Column(db.String(50))
    vm_name = db.Column(db.String(50))
    status = db.Column(db.String(50))
    dns = db.Column(db.String(50))
    public_ip = db.Column(db.String(50))
    private_ip = db.Column(db.String(50))
    virtual_environment_id = db.Column(db.Integer, db.ForeignKey('virtual_environment.id', ondelete='CASCADE'))
    virtual_environment = db.relationship(VirtualEnvironment, backref=db.backref('azure_vm', lazy='dynamic'))
    create_time = db.Column(db.DateTime)
    last_modify_time = db.Column(db.DateTime)

    def __init__(self, **kwargs):
        super(AzureVM, self).__init__(**kwargs)
        if self.create_time is None:
            self.create_time = datetime.utcnow()
        if self.last_modify_time is None:
            self.last_modify_time = datetime.utcnow()

    def json(self):
        return to_json(self, self.__class__)

    def __repr__(self):
        return '%s: %s' % (AzureVM.__name__, self.json())


class AzurePort(db.Model):
    """
    For input endpoint
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    protocol = db.Column(db.String(50))
    public_port = db.Column(db.Integer)
    private_port = db.Column(db.Integer)
    virtual_environment_id = db.Column(db.Integer, db.ForeignKey('virtual_environment.id', ondelete='CASCADE'))
    virtual_environment = db.relationship(VirtualEnvironment, backref=db.backref('azure_vm', lazy='dynamic'))
    create_time = db.Column(db.DateTime)
    last_modify_time = db.Column(db.DateTime)

    def __init__(self, **kwargs):
        super(AzurePort, self).__init__(**kwargs)
        if self.create_time is None:
            self.create_time = datetime.utcnow()
        if self.last_modify_time is None:
            self.last_modify_time = datetime.utcnow()

    def json(self):
        return to_json(self, self.__class__)

    def __repr__(self):
        return '%s: %s' % (AzurePort.__name__, self.json())
