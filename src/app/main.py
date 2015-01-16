__author__ = 'Yifu Huang'

from src.app.azureImpl import AzureImpl
from src.app.database import *
import credentials
from src.app.log import *
import sys

a = AzureImpl()
# create user info and key
user_info = a.register(credentials.USER_NAME, credentials.USER_EMAIL, credentials.SUBSCRIPTION_ID,
                       credentials.MANAGEMENT_HOST)
# after key generation, cer should be uploaded to user's azure portal

# user choose template
template = Template.query.filter_by(id=1).first()
if template is None:
    log.error("no public template")
    sys.exit(1)
# avoid duplicate user template
user_template = UserTemplate.query.filter_by(user_info=user_info, template=template).first()
if user_template is None:
    user_template = UserTemplate(user_info, template)
    db.session.add(user_template)
    db.session.commit()
else:
    log.debug('user template [%d] is exist' % user_template.id)

# connect to azure service management
a.connect(user_info)

# create virtual machine
a.create_vm(user_template)

# update virtual machine
updated = a.update_vm(user_template)
log.debug(updated)

# delete virtual machine
deleted = a.delete_vm(user_template)
log.debug(deleted)