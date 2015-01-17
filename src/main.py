__author__ = 'Yifu Huang'

from src.app import credentials
from src.app.azureImpl import AzureImpl
from src.app.database import *
from src.app.log import *
import sys

# this is how client execute

a = AzureImpl()
# create user info and key
user_info = a.register(credentials.USER_NAME, credentials.USER_EMAIL, credentials.SUBSCRIPTION_ID,
                       credentials.MANAGEMENT_HOST)
# after key generation, cer should be uploaded to user's azure portal

# user choose template
templates = Template.query.all()
if templates is None:
    log.error("no public templates")
    sys.exit(1)
# avoid duplicate user template
for template in templates:
    user_template = UserTemplate.query.filter_by(user_info=user_info, template=template).first()
    if user_template is None:
        user_template = UserTemplate(user_info, template)
        db.session.add(user_template)
        db.session.commit()
    else:
        log.debug('user template [%d] is exist' % user_template.id)

# connect to azure service management
connected = a.connect(user_info)
log.debug('connect: %s' % connected)


user_template = UserTemplate.query.filter_by(id=1).first()
# create virtual machine
created = a.create_vm(user_template)
log.debug('create_vm: %s' % created)

user_template = UserTemplate.query.filter_by(id=2).first()
# update virtual machine
updated = a.update_vm(user_template)
log.debug('update_vm: %s' % updated)

user_template = UserTemplate.query.filter_by(id=1).first()
# delete virtual machine
deleted = a.delete_vm(user_template)
log.debug('delete_vm: %s' % deleted)