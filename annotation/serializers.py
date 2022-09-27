import logging
from rest_framework.serializers import HyperlinkedRelatedField, IntegerField, BooleanField
from .models import Project, Batch
from cdh.serializers import CdhSerializer


logger = logging.getLogger(__name__)


class ProjectSerializer(CdhSerializer):
    login_required = BooleanField(required=False)
    class Meta:
        model = Project
        fields = ["active", "allotted_assignment_time", "assignments_per_task", "html_template", "login_required", "fieldnames", "id", "url", "created_by"]
        view_fields = ["active", "allotted_assignment_time", "assignments_per_task", "html_template", "login_required", "fieldnames", "id", "url"]
        edit_fields = ["active", "allotted_assignment_time", "assignments_per_task", "html_template", "login_required", "fieldnames", "id"]
        create_fields = ["active", "allotted_assignment_time", "assignments_per_task", "html_template", "login_required", "id"]


class BatchSerializer(CdhSerializer):
    project = HyperlinkedRelatedField(view_name="api:project-detail", queryset=Project.objects.all())
    class Meta:
        model = Batch
        fields = ["project", "active", "allotted_assignment_time", "assignments_per_task", "completed", "login_required", "published", "id", "url", "created_by"]
        view_fields = ["project", "active", "allotted_assignment_time", "assignments_per_task", "completed", "login_required", "published", "id"]
        edit_fields = ["project", "active", "allotted_assignment_time", "assignments_per_task", "completed", "login_required", "published", "id"]
        create_fields = ["project", "active", "allotted_assignment_time", "assignments_per_task", "completed", "login_required", "published", "id"]
