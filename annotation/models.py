import logging
from django.db import models
from turkle.models import Batch, Project
from cdh.models import CdhModel


logger = logging.getLogger(__name__)


class AnnotationBatch(Batch, CdhModel):
    pass


class AnnotationProject(Project, CdhModel):
    pass
