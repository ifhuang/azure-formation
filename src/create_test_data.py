__author__ = 'Yifu Huang'

import os
from app.database import *

# add public templates to database
template_url = os.path.abspath('app/resources/webserver.js')
template = Template(template_url, 'public')
db.session.add(template)
db.session.commit()