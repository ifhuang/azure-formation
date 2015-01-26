__author__ = 'Yifu Huang'

from src.app import credentials
from src.app.azureImpl import AzureImpl
from src.app.azureUtil import *
from src.app.database import *
from src.app.log import *
import sys

# this is how client execute

a = AzureImpl()
# create user info and key
user_info = a.register(credentials.USER_NAME, credentials.USER_EMAIL,
                       credentials.SUBSCRIPTION_ID, credentials.MANAGEMENT_HOST)
# after key generation, cer should be uploaded to user's azure portal

# user choose template
templates = Template.query.all()
# make sure public templates exist
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
        log.debug('user template [%d] exist' % user_template.id)

# connect to azure service management
connected = a.connect(user_info)
log.debug('connect: %s' % connected)

user_template = UserTemplate.query.filter_by(id=1).first()
# create virtual machine
create_async_result = a.create_async(user_template)
log.debug('create_async: %s' % create_async_result)
while operation_status(user_template, CREATE) == START:
    log.debug('operation_status loop')
    log.debug(query_user_operation(user_template, CREATE))
    log.debug(query_user_resource(user_template))
    time.sleep(30)
log.debug('operation_status: %s' % operation_status(user_template, CREATE))
log.debug('query_user_operation: %s' % query_user_operation(user_template, CREATE))
log.debug('query_user_resource: %s' % query_user_resource(user_template))