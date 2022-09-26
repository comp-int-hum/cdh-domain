import logging
from rest_framework.serializers import HyperlinkedRelatedField, IntegerField, BooleanField
from .models import AnnotationProject, AnnotationBatch
from cdh.serializers import CdhSerializer


logger = logging.getLogger(__name__)


class AnnotationProjectSerializer(CdhSerializer):
    login_required = BooleanField(required=False)
    class Meta:
        model = AnnotationProject
        fields = ["active", "allotted_assignment_time", "assignments_per_task", "html_template", "login_required", "fieldnames", "id", "url", "created_by"]
        view_fields = ["active", "allotted_assignment_time", "assignments_per_task", "html_template", "login_required", "fieldnames", "id", "url"]
        edit_fields = ["active", "allotted_assignment_time", "assignments_per_task", "html_template", "login_required", "fieldnames", "id"]
        create_fields = ["active", "allotted_assignment_time", "assignments_per_task", "html_template", "login_required", "id"]


class AnnotationBatchSerializer(CdhSerializer):
    project = HyperlinkedRelatedField(view_name="api:annotationproject-detail", queryset=AnnotationProject.objects.all())
    class Meta:
        model = AnnotationBatch
        fields = ["project", "active", "allotted_assignment_time", "assignments_per_task", "completed", "login_required", "published", "id", "url", "created_by"]
        view_fields = ["project", "active", "allotted_assignment_time", "assignments_per_task", "completed", "login_required", "published", "id"]
        edit_fields = ["project", "active", "allotted_assignment_time", "assignments_per_task", "completed", "login_required", "published", "id"]
        create_fields = ["project", "active", "allotted_assignment_time", "assignments_per_task", "completed", "login_required", "published", "id"]
