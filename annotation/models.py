import logging
from turkle import models as turkle_models
from cdh.models import CdhModel


logger = logging.getLogger(__name__)


class Batch(turkle_models.Batch, CdhModel):
    pass


class Project(turkle_models.Project, CdhModel):
    pass
