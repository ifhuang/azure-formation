__author__ = 'Yifu Huang'

import time

from src.azureformation.database import (
    db_adapter,
)
from src.azureformation.database.models import (
    Experiment,
    Template,
    User,
    Hackathon,
    HackathonAzureKey,
)
from src.azureformation.enum import (
    EStatus,
)
from src.azureformation.azureoperation.azureFormation import (
    AzureFormation,
)


# init
t = db_adapter.find_first_object(Template)
u = db_adapter.find_first_object(User)
h = db_adapter.find_first_object(Hackathon)
ha = db_adapter.find_first_object_by(HackathonAzureKey, hackathon=h)
af = AzureFormation(ha.azure_key_id)
e = db_adapter.add_object_kwargs(Experiment,
                                 status=EStatus.Init,
                                 template=t,
                                 user=u,
                                 hackathon=h)
db_adapter.commit()

# start
db_adapter.update_object(e, status=EStatus.Starting)
db_adapter.commit()
af.create(e.id)

while True:
    time.sleep(10)
    print 'callExample'

# end
db_adapter.update_object(e, status=EStatus.Running)
db_adapter.commit()