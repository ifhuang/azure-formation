__author__ = 'Yifu Huang'

from src.azureformation.database import (
    db
)
from src.azureformation.log import (
    log
)
from datetime import (
    datetime
)
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


class DBBase(db.Model):
    """
    DB model base class, providing basic functions
    """
    __abstract__ = True

    def __init__(self, **kwargs):
        super(DBBase, self).__init__(**kwargs)

    def json(self):
        return to_json(self, self.__class__)

    def __repr__(self):
        return '%s: %s' % (self.__class__.__name__, self.json())


class User(DBBase):
    """
    Just a placeholder of user
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))


class Hackathon(DBBase):
    """
    Just a placeholder of hackathon
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))


class AzureKey(DBBase):
    """
    Azure certificate information of user/hackathon
    """
    id = db.Column(db.Integer, primary_key=True)
    # cert file should be uploaded to azure portal
    cert_url = db.Column(db.String(200))
    # pem file should be saved in where this program run
    pem_url = db.Column(db.String(200))
    subscription_id = db.Column(db.String(100))
    management_host = db.Column(db.String(100))
    # AKOwner in enum.py
    owner = db.Column(db.Integer)
    # None if owner is hackathon
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    user = db.relationship('User', backref=db.backref('azure_key_u', lazy='dynamic'))
    # None if owner is user
    hackathon_id = db.Column(db.Integer, db.ForeignKey('hackathon.id', ondelete='CASCADE'))
    hackathon = db.relationship('Hackathon', backref=db.backref('azure_key_h', lazy='dynamic'))
    create_time = db.Column(db.DateTime)
    last_modify_time = db.Column(db.DateTime)

    def __init__(self, **kwargs):
        super(AzureKey, self).__init__(**kwargs)
        if self.create_time is None:
            self.create_time = datetime.utcnow()
        if self.last_modify_time is None:
            self.last_modify_time = datetime.utcnow()


class Template(DBBase):
    """
    Just a placeholder of template
    """
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(200))


class Experiment(DBBase):
    """
    Experiment is launched once template is used:
    1. user use template directly (user manage his own azure resources through template)
    2. hackathon use template directly (hackathon manage its own azure resources through template)
    3. user use template via hackathon (online)
    """
    id = db.Column(db.Integer, primary_key=True)
    # EStatus in enum.py
    status = db.Column(db.Integer)
    template_id = db.Column(db.Integer, db.ForeignKey('template.id', ondelete='CASCADE'))
    template = db.relationship('Template', backref=db.backref('experiment_t', lazy='dynamic'))
    # None if hackathon use template directly
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    user = db.relationship('User', backref=db.backref('experiment_u', lazy='dynamic'))
    # None if user use template directly
    hackathon_id = db.Column(db.Integer, db.ForeignKey('hackathon.id', ondelete='CASCADE'))
    hackathon = db.relationship('Hackathon', backref=db.backref('experiment_h', lazy='dynamic'))
    create_time = db.Column(db.DateTime)
    last_heart_beat_time = db.Column(db.DateTime)

    def __init__(self, **kwargs):
        super(Experiment, self).__init__(**kwargs)
        if self.create_time is None:
            self.create_time = datetime.utcnow()
        if self.last_heart_beat_time is None:
            self.last_heart_beat_time = datetime.utcnow()


class VirtualEnvironment(DBBase):
    """
    Virtual environment is abstraction of smallest environment unit in template
    """
    id = db.Column(db.Integer, primary_key=True)
    # VEProvider in enum.py
    provider = db.Column(db.Integer)
    name = db.Column(db.String(100))
    image = db.Column(db.String(200))
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


class AzureLog(DBBase):
    """
    Azure operation log for every experiment
    """
    id = db.Column(db.Integer, primary_key=True)
    # ALOperation in enum.py
    operation = db.Column(db.String(50))
    # ALStatus in enum.py
    status = db.Column(db.String(50))
    # Note if no info and error
    note = db.Column(db.String(500))
    # None if no error
    code = db.Column(db.Integer)
    experiment_id = db.Column(db.Integer, db.ForeignKey('experiment.id', ondelete='CASCADE'))
    experiment = db.relationship('Experiment', backref=db.backref('azure_log', lazy='dynamic'))
    exec_time = db.Column(db.DateTime)

    def __init__(self, **kwargs):
        super(AzureLog, self).__init__(**kwargs)
        if self.exec_time is None:
            self.exec_time = datetime.utcnow()


class AzureStorageAccount(DBBase):
    """
    Azure storage account information
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    description = db.Column(db.String(100))
    label = db.Column(db.String(50))
    location = db.Column(db.String(50))
    # ASAStatus in enum.py
    status = db.Column(db.String(50))
    experiment_id = db.Column(db.Integer, db.ForeignKey('experiment.id', ondelete='CASCADE'))
    experiment = db.relationship('Experiment', backref=db.backref('azure_storage_account', lazy='dynamic'))
    create_time = db.Column(db.DateTime)
    last_modify_time = db.Column(db.DateTime)

    def __init__(self, **kwargs):
        super(AzureStorageAccount, self).__init__(**kwargs)
        if self.create_time is None:
            self.create_time = datetime.utcnow()
        if self.last_modify_time is None:
            self.last_modify_time = datetime.utcnow()


class AzureCloudService(DBBase):
    """
    Azure cloud service information
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    label = db.Column(db.String(50))
    location = db.Column(db.String(50))
    # ACSStatus in enum.py
    status = db.Column(db.String(50))
    experiment_id = db.Column(db.Integer, db.ForeignKey('experiment.id', ondelete='CASCADE'))
    experiment = db.relationship('Experiment', backref=db.backref('azure_cloud_service', lazy='dynamic'))
    create_time = db.Column(db.DateTime)
    last_modify_time = db.Column(db.DateTime)

    def __init__(self, **kwargs):
        super(AzureCloudService, self).__init__(**kwargs)
        if self.create_time is None:
            self.create_time = datetime.utcnow()
        if self.last_modify_time is None:
            self.last_modify_time = datetime.utcnow()


class AzureDeployment(DBBase):
    """
    Azure deployment information
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    slot = db.Column(db.String(50))
    # ADStatus in enum.py
    status = db.Column(db.String(50))
    cloud_service_id = db.Column(db.Integer, db.ForeignKey('azure_cloud_service.id', ondelete='CASCADE'))
    cloud_service = db.relationship('AzureCloudService', backref=db.backref('azure_deployment_c', lazy='dynamic'))
    experiment_id = db.Column(db.Integer, db.ForeignKey('experiment.id', ondelete='CASCADE'))
    experiment = db.relationship('Experiment', backref=db.backref('azure_deployment_e', lazy='dynamic'))
    create_time = db.Column(db.DateTime)
    last_modify_time = db.Column(db.DateTime)

    def __init__(self, **kwargs):
        super(AzureDeployment, self).__init__(**kwargs)
        if self.create_time is None:
            self.create_time = datetime.utcnow()
        if self.last_modify_time is None:
            self.last_modify_time = datetime.utcnow()


class AzureVirtualMachine(DBBase):
    """
    Azure virtual machine information
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    label = db.Column(db.String(50))
    # AVMStatus in enum.py
    status = db.Column(db.String(50))
    dns = db.Column(db.String(50))
    public_ip = db.Column(db.String(50))
    private_ip = db.Column(db.String(50))
    deployment_id = db.Column(db.Integer, db.ForeignKey('azure_deployment.id', ondelete='CASCADE'))
    deployment = db.relationship('AzureDeployment', backref=db.backref('azure_virtual_machine_d', lazy='dynamic'))
    experiment_id = db.Column(db.Integer, db.ForeignKey('experiment.id', ondelete='CASCADE'))
    experiment = db.relationship('Experiment', backref=db.backref('azure_virtual_machine_e', lazy='dynamic'))
    create_time = db.Column(db.DateTime)
    last_modify_time = db.Column(db.DateTime)

    def __init__(self, **kwargs):
        super(AzureVirtualMachine, self).__init__(**kwargs)
        if self.create_time is None:
            self.create_time = datetime.utcnow()
        if self.last_modify_time is None:
            self.last_modify_time = datetime.utcnow()


class AzureEndPoint(DBBase):
    """
    Input endpoint information of Azure virtual machine
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    protocol = db.Column(db.String(50))
    public_port = db.Column(db.Integer)
    private_port = db.Column(db.Integer)
    virtual_machine_id = db.Column(db.Integer, db.ForeignKey('azure_virtual_machine.id', ondelete='CASCADE'))
    virtual_machine = db.relationship('AzureVirtualMachine', backref=db.backref('azure_end_point', lazy='dynamic'))
    create_time = db.Column(db.DateTime)
    last_modify_time = db.Column(db.DateTime)

    def __init__(self, **kwargs):
        super(AzureEndPoint, self).__init__(**kwargs)
        if self.create_time is None:
            self.create_time = datetime.utcnow()
        if self.last_modify_time is None:
            self.last_modify_time = datetime.utcnow()
