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
# make sure public templates are exist
if templates is None:
    log.error("no public templates")
    sys.exit(1)
for template in templates:
    user_template = UserTemplate.query.filter_by(user_info=user_info, template=template).first()
    # avoid duplicate user template
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
created = a.create(user_template)
log.debug('create: %s' % created)

user_template = UserTemplate.query.filter_by(id=2).first()
# update virtual machine
updated = a.update(user_template)
log.debug('update: %s' % updated)

user_template = UserTemplate.query.filter_by(id=1).first()
# delete virtual machine
deleted = a.delete(user_template)
log.debug('delete: %s' % deleted)
