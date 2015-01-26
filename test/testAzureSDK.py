__author__ = 'Yifu Huang'

from azure.servicemanagement import *
from src.app import credentials
from src.app.database import *


def image_name():
    sms = ServiceManagementService(credentials.SUBSCRIPTION_ID, credentials.PEM_CERTIFICATE, credentials.MANAGEMENT_HOST)
    for image in sms.list_os_images():
        print image.name


def vm_endpoint_update():
    cs = UserResource.query.filter_by(id=2).first()
    vm = UserResource.query.filter_by(id=4).first()
    vm_endpoints = VMEndpoint.query.filter_by(cloud_service=cs, virtual_machine=None).all()
    for vm_endpoint in vm_endpoints:
        vm_endpoint.virtual_machine = vm
    db.session.commit()


def vm_endpoint_delete():
    cs = UserResource.query.filter_by(id=2).first()
    vm = UserResource.query.filter_by(id=4).first()
    VMEndpoint.query.filter_by(cloud_service=cs, virtual_machine=vm).delete()
    db.session.commit()


def old_endpoints():
    old_points = VMEndpoint.query.filter_by(virtual_machine=None).all()
    vme = VMEndpoint('1', '1', 1, 1, None)
    db.session.add(vme)
    db.session.commit()
    print old_points


def list_like():
    user_template = UserTemplate.query.filter_by(id=1).first()
    user_resource = UserResource(user_template, 'test', 'test', 'test', [])
    db.session.add(user_resource)
    db.session.commit()


def cascade_delete():
    UserResource.query.filter_by(type='cloud service').delete()
    db.session.commit()


cascade_delete()