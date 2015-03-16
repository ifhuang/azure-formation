__author__ = 'Yifu Huang'

from src.azureformation.database import (
    db_adapter,
)
from src.azureformation.database.models import (
    Experiment,
    Template,
    User,
    Hackathon,
    HackathonAzureKey,
    AzureKey,
)
from src.azureformation.enum import (
    EStatus,
)
from src.azureformation.azureoperation.service import (
    Service,
)
from src.azureformation.azureFormation import (
    AzureFormation,
)

# init
t = db_adapter.find_first_object(Template)
u = db_adapter.find_first_object(User)
h = db_adapter.find_first_object(Hackathon)
ha = db_adapter.find_first_object_by(HackathonAzureKey, hackathon=h)
a = db_adapter.get_object(AzureKey, ha.azure_key_id)
s = Service(a.subscription_id, a.pem_url, a.management_host)
af = AzureFormation(s)
e = db_adapter.add_object_kwargs(Experiment,
                                 status=EStatus.Init,
                                 template_id=t.id,
                                 user_id=u.id,
                                 hackathon_id=h.id)
db_adapter.commit()

# start
db_adapter.update_object_kwargs(e, status=EStatus.Starting)
db_adapter.commit()
af.create(e)