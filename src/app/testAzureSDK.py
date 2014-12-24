__author__ = 'Yifu Huang'

import constants
from azure import *
from azure.servicemanagement import *


def connect():
    # Connect to service management
    subscription_id = constants.SUBSCRIPTION_ID
    certificate_path = constants.PEM_CERTIFICATE
    host = constants.MANAGEMENT_HOST
    return ServiceManagementService(subscription_id, certificate_path, host)


def locations(sms):
    # List available locations
    result = sms.list_locations()
    for location in result:
        print(location.name)


def services(sms):
    # List available cloud services
    result = sms.list_hosted_services()
    for hosted_service in result:
        print('Service name: ' + hosted_service.service_name)
        print('Management URL: ' + hosted_service.url)
        print('Affinity group: ' + hosted_service.hosted_service_properties.affinity_group)
        print('Location: ' + hosted_service.hosted_service_properties.location)
        print('')


def create_service(sms):
    # Create a cloud service
    name = 'yifu-test-cloud-service'
    label = 'yifu-test-cloud-service'
    desc = 'yifu test cloud service'
    location = 'China East'
    # You can either set the location or an affinity_group
    sms.create_hosted_service(name, label, desc, location)


def delete_service(sms):
    # Delete a cloud service
    sms.delete_hosted_service('yifu-test-cloud-service')


def storage(sms):
    # List available storage
    result = sms.list_storage_accounts()
    for account in result:
        print('Service name: ' + account.service_name)
        print('Affinity group: ' + account.storage_service_properties.affinity_group)
        print('Location: ' + account.storage_service_properties.location)
        print('')


def create_storage(sms):
    # Create a storage
    name = 'yifu0test0storage'
    label = 'yifu0test0storage'
    location = 'China East'
    desc = 'yifu test storage'
    result = sms.create_storage_account(name, desc, label, location=location)
    operation_result = sms.get_operation_status(result.request_id)
    print('Operation status: ' + operation_result.status)


def delete_storage(sms):
    # Delete a storage
    sms.delete_storage_account('yifu0test0storage')


def groups(sms):
    # List available groups
    result = sms.list_affinity_groups()
    for group in result:
        print('Name: ' + group.name)
        print('Description: ' + group.description)
        print('Location: ' + group.location)
        print('')


def create_group(sms):
    # Create a group
    name = 'yifu-test-group'
    label = 'yifu-test-group'
    location = 'China East'
    desc = 'yifu test group'
    sms.create_affinity_group(name, label, location, desc)


def delete_group(sms):
    # Delete a group
    sms.delete_affinity_group('yifu-test-group')


def systems(sms):
    # List available systems
    result = sms.list_operating_systems()
    for os in result:
        print('OS: ' + os.label)
        print('Family: ' + os.family_label)
        print('Active: ' + str(os.is_active))


def images(sms):
    # List available images
    result = sms.list_os_images()
    for image in result:
        print('Name: ' + image.name)
        print('Label: ' + image.label)
        print('OS: ' + image.os)
        print('Category: ' + image.category)
        print('Description: ' + image.description)
        print('Location: ' + image.location)
        print('Affinity group: ' + image.affinity_group)
        print('Media link: ' + image.media_link)
        print('')


def create_vm(sms):
    # Create a vm
    name = 'yifu-test-vm'
    location = 'China East'
    # You can either set the location or an affinity_group
    sms.create_hosted_service(service_name=name,
        label=name,
        location=location)
    # Name of an os image as returned by list_os_images
    image_name = 'abc'
    # Destination storage account container/blob where the VM disk
    # will be created
    media_link = 'abc.vhd'
    # Linux VM configuration, you can use WindowsConfigurationSet
    # for a Windows VM instead
    linux_config = LinuxConfigurationSet('myhostname', 'myuser', 'myPassword)', True)
    os_hd = OSVirtualHardDisk(image_name, media_link)
    try:
        sms.create_virtual_machine_deployment(service_name=name,
            deployment_name=name,
            deployment_slot='production',
            label=name,
            role_name=name,
            system_config=linux_config,
            os_virtual_hard_disk=os_hd,
            role_size='Small')
    except Exception as e:
        print('AZURE ERROR: %s' % str(e))


service_management_service = connect()
#locations(service_management_service)
#services(service_management_service)
#create_service(service_management_service)
#delete_service(service_management_service)
#storage(service_management_service)
#create_storage(service_management_service)
#delete_storage(service_management_service)
#groups(service_management_service)
#create_group(service_management_service)
#delete_group(service_management_service)
#systems(service_management_service)
#images(service_management_service)
create_vm(service_management_service)
