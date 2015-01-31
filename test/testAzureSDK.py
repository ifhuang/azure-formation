__author__ = 'Yifu Huang'

from azure.servicemanagement import *
from src.azureautodeploy import credentials
from src.azureautodeploy.database import *
from src.azureautodeploy.database.models import *


def image_name():
    sms = ServiceManagementService(credentials.SUBSCRIPTION_ID,
                                   credentials.PEM_CERTIFICATE,
                                   credentials.MANAGEMENT_HOST)
    for image in sms.list_os_images():
        print image.name


def vm_endpoint_update():
    cs = db_adapter.get_object(UserResource, 2)
    vm = db_adapter.get_object(UserResource, 4)
    vm_endpoints = db_adapter.find_all_objects(VMEndpoint, cloud_service=cs, virtual_machine=None)
    for vm_endpoint in vm_endpoints:
        vm_endpoint.virtual_machine = vm
    db_adapter.commit()


def vm_endpoint_delete():
    cs = db_adapter.get_object(UserResource, 2)
    vm = db_adapter.get_object(UserResource, 4)
    db_adapter.delete_all_objects(VMEndpoint, cloud_service=cs, virtual_machine=vm)
    db_adapter.commit()


def old_endpoints():
    old_points = db_adapter.find_all_objects(VMEndpoint, virtual_machine=None)
    db_adapter.add_object_kwargs(VMEndpoint, name='1', protocol='1', public_port=1, private_port=1, cloud_service=None)
    db_adapter.commit()
    print old_points


def cascade_delete():
    db_adapter.delete_all_objects(UserResource, type='cloud service')
    db_adapter.commit()


def like():
    db_adapter.add_object_kwargs(UserInfo, name='Paoshen', email='paoshen@a.com')
    db_adapter.add_object_kwargs(UserInfo, name='Feizhan', email='feizhan@b.com')
    db_adapter.commit()
    ui = db_adapter.find_all_objects_like(UserInfo, email='%a.com')
    print ui

like()