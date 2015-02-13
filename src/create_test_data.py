__author__ = 'Yifu Huang'

from src.azureformation.database import *
from src.azureformation.database.models import *
from src.azureformation.log import *
import os
import sys

# this is what server need to do

# add public templates to database
template_dir = 'azureautodeploy/resources'
if not os.path.isdir(template_dir):
    log.error('template dir %s is not exist' % template_dir)
    sys.exit(1)
template_files = os.listdir(template_dir)
if template_files is None:
    log.error('template dir %s is empty' % template_dir)
    sys.exit(1)
for template_file in template_files:
    template_url = os.getcwd() + os.path.sep + template_dir + os.path.sep + template_file
    db_adapter.add_object_kwargs(Template, url=template_url, type='public')
    db_adapter.commit()

