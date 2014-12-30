# Azure Documentation

- Cloud Service: http://azure.microsoft.com/en-us/documentation/services/cloud-services/
- Virtual Machines: http://azure.microsoft.com/en-us/documentation/services/virtual-machines/

# Azure Service Management SDK for Python

- Source Code: https://github.com/Azure/azure-sdk-for-python/blob/master/azure/servicemanagement/servicemanagementservice.py
- Test Code: https://github.com/Azure/azure-sdk-for-python/blob/master/tests/test_servicemanagementservice.py
- Documentation: http://azure.microsoft.com/en-us/documentation/articles/cloud-services-python-how-to-use-service-management/

# Preconditions
- mycert.cer: upload to azure management portal
- mycert.pem: save to local pc
- credentials.py: identify necessary constants

# Configure Logs

```
sudo mkdir /var/log/azure-auto-deploy
sudo chown $USER:$USER /var/log/azure-auto-deploy
```

# Usage

```
sudo pip install -r requirement.txt
sudo python run.py
```
