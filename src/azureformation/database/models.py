__author__ = 'Yifu Huang'

from src.azureformation.database import (
    Base,
    db_adapter,
)
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import (
    backref,
    relation,
)
from datetime import (
    datetime,
)
import json


def relationship(*arg, **kw):
    ret = relation(*arg, **kw)
    db_adapter.commit()
    return ret


def date_serializer(date):
    return long((date - datetime(1970, 1, 1)).total_seconds() * 1000)


def to_json(inst, cls):
    # add your coversions for things like datetime's
    # and what-not that aren't serializable.
    convert = dict()
    convert[DateTime] = date_serializer
    d = dict()
    for c in cls.__table__.columns:
        v = getattr(inst, c.name)
        if c.type.__class__ in convert.keys() and v is not None:
            try:
                func = convert[c.type.__class__]
                d[c.name] = func(v)
            except:
                d[c.name] = "Error:  Failed to covert using ", str(convert[c.type.__class__])
        elif v is None:
            d[c.name] = str()
        else:
            d[c.name] = v
    return json.dumps(d)


class DBBase(Base):
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
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(50))


class Hackathon(DBBase):
    """
    Just a placeholder of hackathon
    """
    __tablename__ = 'hackathon'

    id = Column(Integer, primary_key=True)
    name = Column(String(50))


class AzureKey(DBBase):
    """
    Azure certificate information of user/hackathon
    """
    __tablename__ = 'azure_key'

    id = Column(Integer, primary_key=True)
    # cert file should be uploaded to azure portal
    cert_url = Column(String(200))
    # pem file should be saved in where this program run
    pem_url = Column(String(200))
    subscription_id = Column(String(100))
    management_host = Column(String(100))
    create_time = Column(DateTime)
    last_modify_time = Column(DateTime)

    def __init__(self, **kwargs):
        super(AzureKey, self).__init__(**kwargs)
        if self.create_time is None:
            self.create_time = datetime.utcnow()
        if self.last_modify_time is None:
            self.last_modify_time = datetime.utcnow()


class UserAzureKey(DBBase):
    __tablename__ = 'user_azure_key'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id', ondelete='CASCADE'))
    user = relationship('User', backref=backref('user_azure_key_u', lazy='dynamic'))
    azure_key_id = Column(Integer, ForeignKey('azure_key.id', ondelete='CASCADE'))
    azure_key = relationship('AzureKey', backref=backref('user_azure_key_a', lazy='dynamic'))


class HackathonAzureKey(DBBase):
    __tablename__ = 'hackathon_azure_key'

    id = Column(Integer, primary_key=True)
    hackathon_id = Column(Integer, ForeignKey('hackathon.id', ondelete='CASCADE'))
    hackathon = relationship('Hackathon', backref=backref('hackathon_azure_key_h', lazy='dynamic'))
    azure_key_id = Column(Integer, ForeignKey('azure_key.id', ondelete='CASCADE'))
    azure_key = relationship('AzureKey', backref=backref('hackathon_azure_key_a', lazy='dynamic'))


class Template(DBBase):
    """
    Just a placeholder of template
    """
    __tablename__ = 'template'

    id = Column(Integer, primary_key=True)
    url = Column(String(200))


class Experiment(DBBase):
    """
    Experiment is launched once template is used:
    1. user use template directly (user manage his own azure resources through template)
    2. hackathon use template directly (hackathon manage its own azure resources through template)
    3. user use template via hackathon (online)
    """
    __tablename__ = 'experiment'

    id = Column(Integer, primary_key=True)
    # EStatus in enum.py
    status = Column(Integer)
    template_id = Column(Integer, ForeignKey('template.id', ondelete='CASCADE'))
    template = relationship('Template', backref=backref('experiment_t', lazy='dynamic'))
    # None if hackathon use template directly
    user_id = Column(Integer, ForeignKey('user.id', ondelete='CASCADE'))
    user = relationship('User', backref=backref('experiment_u', lazy='dynamic'))
    # None if user use template directly
    hackathon_id = Column(Integer, ForeignKey('hackathon.id', ondelete='CASCADE'))
    hackathon = relationship('Hackathon', backref=backref('experiment_h', lazy='dynamic'))
    create_time = Column(DateTime)
    last_heart_beat_time = Column(DateTime)

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
    __tablename__ = 'virtual_environment'

    id = Column(Integer, primary_key=True)
    # VEProvider in enum.py
    provider = Column(Integer)
    name = Column(String(100))
    image = Column(String(200))
    # VEStatus in enum.py
    status = Column(Integer)
    # VERemoteProvider in enum.py
    remote_provider = Column(Integer)
    remote_paras = Column(String(300))
    experiment_id = Column(Integer, ForeignKey('experiment.id', ondelete='CASCADE'))
    experiment = relationship('Experiment', backref=backref('virtual_environment', lazy='dynamic'))
    create_time = Column(DateTime)

    def __init__(self, **kwargs):
        super(VirtualEnvironment, self).__init__(**kwargs)
        if self.create_time is None:
            self.create_time = datetime.utcnow()


class AzureLog(DBBase):
    """
    Azure operation log for every experiment
    """
    __tablename__ = 'azure_log'

    id = Column(Integer, primary_key=True)
    # ALOperation in enum.py
    operation = Column(String(50))
    # ALStatus in enum.py
    status = Column(String(50))
    # Note if no info and error
    note = Column(String(500))
    # None if no error
    code = Column(Integer)
    experiment_id = Column(Integer, ForeignKey('experiment.id', ondelete='CASCADE'))
    experiment = relationship('Experiment', backref=backref('azure_log', lazy='dynamic'))
    exec_time = Column(DateTime)

    def __init__(self, **kwargs):
        super(AzureLog, self).__init__(**kwargs)
        if self.exec_time is None:
            self.exec_time = datetime.utcnow()


class AzureStorageAccount(DBBase):
    """
    Azure storage account information
    """
    __tablename__ = 'azure_storage_account'

    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    description = Column(String(100))
    label = Column(String(50))
    location = Column(String(50))
    # ASAStatus in enum.py
    status = Column(String(50))
    experiment_id = Column(Integer, ForeignKey('experiment.id', ondelete='CASCADE'))
    experiment = relationship('Experiment', backref=backref('azure_storage_account', lazy='dynamic'))
    create_time = Column(DateTime)
    last_modify_time = Column(DateTime)

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
    __tablename__ = 'azure_cloud_service'

    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    label = Column(String(50))
    location = Column(String(50))
    # ACSStatus in enum.py
    status = Column(String(50))
    experiment_id = Column(Integer, ForeignKey('experiment.id', ondelete='CASCADE'))
    experiment = relationship('Experiment', backref=backref('azure_cloud_service', lazy='dynamic'))
    create_time = Column(DateTime)
    last_modify_time = Column(DateTime)

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
    __tablename__ = 'azure_deployment'

    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    slot = Column(String(50))
    # ADStatus in enum.py
    status = Column(String(50))
    cloud_service_id = Column(Integer, ForeignKey('azure_cloud_service.id', ondelete='CASCADE'))
    cloud_service = relationship('AzureCloudService', backref=backref('azure_deployment_c', lazy='dynamic'))
    experiment_id = Column(Integer, ForeignKey('experiment.id', ondelete='CASCADE'))
    experiment = relationship('Experiment', backref=backref('azure_deployment_e', lazy='dynamic'))
    create_time = Column(DateTime)
    last_modify_time = Column(DateTime)

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
    __tablename__ = 'azure_virtual_machine'

    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    label = Column(String(50))
    # AVMStatus in enum.py
    status = Column(String(50))
    dns = Column(String(50))
    public_ip = Column(String(50))
    private_ip = Column(String(50))
    deployment_id = Column(Integer, ForeignKey('azure_deployment.id', ondelete='CASCADE'))
    deployment = relationship('AzureDeployment', backref=backref('azure_virtual_machine_d', lazy='dynamic'))
    experiment_id = Column(Integer, ForeignKey('experiment.id', ondelete='CASCADE'))
    experiment = relationship('Experiment', backref=backref('azure_virtual_machine_e', lazy='dynamic'))
    virtual_environment_id = Column(Integer, ForeignKey('virtual_environment.id', ondelete='CASCADE'))
    virtual_environment = relationship('VirtualEnvironment',
                                          backref=backref('azure_virtual_machine_v', lazy='dynamic'))
    create_time = Column(DateTime)
    last_modify_time = Column(DateTime)

    def __init__(self, **kwargs):
        super(AzureVirtualMachine, self).__init__(**kwargs)
        if self.create_time is None:
            self.create_time = datetime.utcnow()
        if self.last_modify_time is None:
            self.last_modify_time = datetime.utcnow()


class AzureEndpoint(DBBase):
    """
    Input endpoint information of Azure virtual machine
    """
    __tablename__ = 'azure_endpoint'

    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    protocol = Column(String(50))
    public_port = Column(Integer)
    private_port = Column(Integer)
    virtual_machine_id = Column(Integer, ForeignKey('azure_virtual_machine.id', ondelete='CASCADE'))
    virtual_machine = relationship('AzureVirtualMachine', backref=backref('azure_endpoint', lazy='dynamic'))
    create_time = Column(DateTime)
    last_modify_time = Column(DateTime)

    def __init__(self, **kwargs):
        super(AzureEndpoint, self).__init__(**kwargs)
        if self.create_time is None:
            self.create_time = datetime.utcnow()
        if self.last_modify_time is None:
            self.last_modify_time = datetime.utcnow()
