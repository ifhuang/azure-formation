__author__ = 'Yifu Huang'

from src.azureautodeploy import credentials
from src.azureautodeploy.azureImpl import AzureImpl
from src.azureautodeploy.database import *
from src.azureautodeploy.database.models import *
from src.azureautodeploy.log import *
import sys
import time

# this is how client execute

a = AzureImpl()
# create user info and key
user_info = a.register(credentials.USER_NAME, credentials.USER_EMAIL,
                       credentials.SUBSCRIPTION_ID, credentials.MANAGEMENT_HOST)
# after key generation, cer should be uploaded to user's azure portal

# user choose template
templates = db_adapter.find_all_objects(Template)
# make sure public templates exist
if templates is None:
    log.error("no public templates")
    sys.exit(1)
for template in templates:

    user_template = db_adapter.find_first_object(UserTemplate, user_info=user_info, template=template)
    # avoid duplicate user template
    if user_template is None:
        db_adapter.add_object_kwargs(UserTemplate, user_info=user_info, template=template)
        db_adapter.commit()
    else:
        log.debug('user template [%d] exist' % user_template.id)

# connect to azure service management
connected = a.connect(user_info)
log.debug('connect: %s' % connected)


"""
showdown_result = a.shutdown_sync(user_template)
log.debug('showdown_result: %s' % showdown_result)
"""

# create virtual machine
user_template = db_adapter.get_object(UserTemplate, 1)
create_async_result = a.create_async(user_template)
log.debug('create_async: %s' % create_async_result)
while True:
    log.debug('greeting from main')
    time.sleep(60)

"""
while operation_status(user_template, CREATE) == START:
    log.debug('operation_status loop')
    log.debug(query_user_operation(user_template, CREATE))
    log.debug(query_user_resource(user_template))
    time.sleep(30)
log.debug('operation_status: %s' % operation_status(user_template, CREATE))
log.debug('query_user_operation: %s' % query_user_operation(user_template, CREATE))
log.debug('query_user_resource: %s' % query_user_resource(user_template))
"""