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
    AVMStatus,
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

# # start
# e = db_adapter.add_object_kwargs(Experiment,
#                                  status=EStatus.Init,
#                                  template=t,
#                                  user=u,
#                                  hackathon=h)
# db_adapter.commit()
# db_adapter.update_object(e, status=EStatus.Starting)
# db_adapter.commit()
# af.create(e.id)

# stop
# af.stop(81, AVMStatus.STOPPED)
# af.stop(81, AVMStatus.STOPPED_DEALLOCATED)

while True:
    time.sleep(10)
    print 'callExample'
