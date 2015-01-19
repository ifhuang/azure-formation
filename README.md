# Azure Auto Deploy

Azure Auto Deploy offers Open Hackathon users an automated way to manage related Azure resources, including cloud
service, storage, deployment and virtual machine. Users can use public or private templates to describe Azure
resources. Azure Auto Deploy creates, updates or deletes Azure resources in templates according to users' requests.

# Archive

#### Azure Documentation

- Cloud Service: http://azure.microsoft.com/en-us/documentation/services/cloud-services/
- Virtual Machines: http://azure.microsoft.com/en-us/documentation/services/virtual-machines/

#### Azure Service Management SDK for Python

- Source Code: https://github.com/Azure/azure-sdk-for-python/blob/master/azure/servicemanagement/servicemanagementservice.py
- Test Code: https://github.com/Azure/azure-sdk-for-python/blob/master/tests/test_servicemanagementservice.py
- Documentation: http://azure.microsoft.com/en-us/documentation/articles/cloud-services-python-how-to-use-service-management/

# Usage

#### Preconditions

- credentials.py: define necessary constants

#### Configure Logs

```
sudo mkdir /var/log/azure-auto-deploy
sudo chown $USER:$USER /var/log/azure-auto-deploy
```

#### MySQL

```
drop database azureautodeploy;
create database azureautodeploy;
create User 'azureautodeploy'@'localhost' IDENTIFIED by 'azureautodeploy';
GRANT ALL on azureautodeploy.* TO 'azureautodeploy'@'localhost';
```

#### Commands

```
sudo pip install -r requirement.txt
sudo python setup_db.py
sudo python create_test_data.py
sudo python main.py
sudo python run.py
```
