__author__ = 'Yifu Huang'

from src.app.azureImpl import AzureImpl
from src.app.database import *

a = AzureImpl()
user_info = a.register('name', 'email', 'subscription_id', 'management_host')

template = Template.query.filter_by(id=1).first()
user_template = UserTemplate(user_info, template)
db.session.add(user_template)
db.session.commit()

a.connect(user_info)