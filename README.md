# Azure Formation

- Azure Formation offers Open Hackathon users an automated way to manage related Azure resources, including storage,
container, cloud service, deployment and virtual machine. Users can use public or private templates to describe Azure
resources. Azure Formation creates, updates or deletes Azure resources in templates according to users' requests.
- For logic: besides resources created by Azure Formation, it can reuse other storage, container, cloud service
and deployment exist in Azure (by sync them into database).
- For template: one storage account, one container, one cloud service, one deployment, multiple virtual machines
(Windows/Linux), multiple input endpoints.

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
sudo mkdir /var/log/azure-formation
sudo chown $USER:$USER /var/log/azure-formation
```

#### MySQL

```
drop database azureformation;
create database azureformation;
create User 'azureformation'@'localhost' IDENTIFIED by 'azureformation';
GRANT ALL on azureformation.* TO 'azureformation'@'localhost';
```

#### Commands

```
sudo pip install -r requirement.txt
sudo python setup_db.py
sudo python create_test_data.py
sudo python main.py
sudo python run.py
```
