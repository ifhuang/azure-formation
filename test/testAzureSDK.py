__author__ = 'Yifu Huang'

from azure.servicemanagement import *
from src.app import credentials

sms = ServiceManagementService(credentials.SUBSCRIPTION_ID, credentials.PEM_CERTIFICATE, credentials.MANAGEMENT_HOST)
for image in sms.list_os_images():
    print image.name