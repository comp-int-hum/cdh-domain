import logging
from django.db import models
from turkle import models
from cdh.models import CdhModel


logger = logging.getLogger(__name__)


class Batch(models.Batch, CdhModel):
    pass

class Project(models.Project, CdhModel):
    pass

