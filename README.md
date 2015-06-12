# Summary

## What
- Azure Formation offers an automated way to manage Azure resources, including storage, container, cloud service, deployment and virtual machine.
- Currently it is used in [Open Hackathon Platform](https://github.com/msopentechcn/open-hackathon) to manage Azure virtual machines.

## Why
- Azure Management Portal is used for manual operation.
- Azure REST API, Azure SDK and Azure PowerShell are used for programming.
- Azure Formation is application-oriented.

## How
- Azure Formation uses Json based templates to describe Azure resources.
  - a template consists of a list of virtual environments, and a virtual environment is a virtual machine with its storage account, container, cloud service and deployment
- It creates, updates or deletes Azure resources asynchronously in templates according to users' requests.
  - besides resources created by Azure Formation, it can reuse other storage, container, cloud service and deployment exist in Azure (by sync them into database)

# Usage

## Install MySQL
```
sudo apt-get install mysql-server libmysqlclient-dev
```
## Configure MySQL
enter MySQL Console
```
create database azureformation;
create User 'azureformation'@'localhost' IDENTIFIED by 'azureformation';
GRANT ALL on azureformation.* TO 'azureformation'@'localhost';
```
## Install Python
```
sudo apt-get install python python-dev python-setuptools
sudo easy_install pip
```
## Configure Logs
```
sudo mkdir /var/log/azure-formation
sudo chown $USER:$USER /var/log/azure-formation
```
## Install Azure Formation
```
sudo apt-get install git
git clone https://github.com/ifhuang/azure-formation.git
sudo pip install -r azure-formation/requirement.txt
sudo python azure-formation/src/setup_db.py
```
## Configure Credentials
create azure-formation/src/azureformation/credentials.py and add following constants
```
CERT_CERTIFICATE = 'local url to Azure cert file'
PEM_CERTIFICATE = 'local url to Azure pem file'
SUBSCRIPTION_ID = 'Azure subscription id'
MANAGEMENT_HOST = 'Azure management host'
USER_NAME = 'your name'
HACKATHON_NAME = 'hackathon name'
TEMPLATE_URL = 'local url to template file'
```
## Demo
```
sudo python loadExample.py
sudo python callExample.py
```
## Other
- sample template: azure-formation/src/azureformation/resources/test-template-1.js
- db schema: azure-formation/db.pdf
