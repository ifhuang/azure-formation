__author__ = 'Yifu Huang'

from src.azureformation.database import (
    db_adapter,
)
from src.azureformation.database.models import (
    User,
    Hackathon,
    AzureKey,
    HackathonAzureKey,
    Template,
)
from src.azureformation.credentials import (
    CERT_CERTIFICATE,
    PEM_CERTIFICATE,
    SUBSCRIPTION_ID,
    MANAGEMENT_HOST,
    USER_NAME,
    HACKATHON_NAME,
    TEMPLATE_URL,
)

# load user
u = db_adapter.add_object_kwargs(User, name=USER_NAME)
db_adapter.commit()

# load hackathon
h = db_adapter.add_object_kwargs(Hackathon, name=HACKATHON_NAME)
db_adapter.commit()

# load azure key
a = db_adapter.add_object_kwargs(AzureKey,
                                 cert_url=CERT_CERTIFICATE,
                                 pem_url=PEM_CERTIFICATE,
                                 subscription_id=SUBSCRIPTION_ID,
                                 management_host=MANAGEMENT_HOST)
db_adapter.commit()

# associate hackathon with azure key
db_adapter.add_object_kwargs(HackathonAzureKey, hackathon=h, azure_key=a)
db_adapter.commit()

# load template
db_adapter.add_object_kwargs(Template, url=TEMPLATE_URL)
db_adapter.commit()