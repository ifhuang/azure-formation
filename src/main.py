__author__ = 'Yifu Huang'

from subprocess import Popen
import sys
import time

from src.azureformation import credentials
from src.azureformation.azureImpl import AzureImpl
from src.azureformation.azureoperation.azureUtil import *
from src.azureformation.database import *
from src.azureformation.database.models import *
from src.azureformation.log import *


# this is how client execute

a = AzureImpl()
# create user info and key
user_info = a.register(credentials.USER_NAME,
                       credentials.USER_EMAIL,
                       credentials.SUBSCRIPTION_ID,
                       credentials.MANAGEMENT_HOST)
# after key generation, cer should be uploaded to user's azure portal

# user choose template
templates = db_adapter.find_all_objects(Template)
# make sure public templates exist
if len(templates) == 0:
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

"""
connected = a.connect(user_info)
log.debug('connect: %s' % connected)
create_async_result = a.create_async(user_template)
log.debug('create_async: %s' % create_async_result)
update_template = db_adapter.get_object(UserTemplate, 2)
update_async_result = a.update_async(user_template, update_template)
log.debug('update_async_result: %s' % update_async_result)
delete_async_result = a.delete_async(user_template)
log.debug('delete_async_result: %s' % delete_async_result)
shutdown_async_result = a.shutdown_async(user_template)
log.debug('shutdown_async_result: %s' % shutdown_async_result)
"""
user_template = db_adapter.get_object(UserTemplate, 1)
command = ['python', 'azureautodeploy/createAsync.py', '1', '1']
p = Popen(command)
print hex(id(db))
uo_id = 0
ur_id = 0
while True:
    print p.poll()
    time.sleep(1)
while True:
    log.debug('operation_status loop, uo_id[%d], ur_id[%d]' % (uo_id, ur_id))
    uo = query_user_operation(user_template, DELETE, uo_id)
    if len(uo) > 0:
        uo_id = uo[-1].id
        for u in uo:
            log.debug(u)
    db_adapter.commit()
    ur = query_user_resource(user_template, ur_id)
    if len(ur) > 0:
        ur_id = ur[-1].id
        for u in ur:
            log.debug(u)
    time.sleep(30)
"""
while True:
    log.debug('greeting from main')
    time.sleep(60)
"""