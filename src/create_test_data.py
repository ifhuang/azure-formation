__author__ = 'Yifu Huang'

from src.app.database import *
from src.app.log import *
import os
import sys

# this is what server need to do

# add public templates to database
template_dir = os.path.abspath('app/resources')
if not os.path.isdir(template_dir):
    log.error('template dir %s is not exist' % template_dir)
    sys.exit(1)
template_files = os.listdir(template_dir)
if template_files is None:
    log.error('template dir %s is empty' % template_dir)
    sys.exit(1)
for template_file in template_files:
    template_url = os.path.abspath(template_file)
    template = Template(template_url, 'public')
    db.session.add(template)
    db.session.commit()

