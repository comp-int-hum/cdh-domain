import logging
from collections import OrderedDict, defaultdict
from rest_framework.serializers import ModelSerializer, BaseSerializer, HyperlinkedModelSerializer, HiddenField, HyperlinkedIdentityField, ReadOnlyField, CurrentUserDefault, HyperlinkedRelatedField, PrimaryKeyRelatedField, CharField, IntegerField
from django.contrib.auth.hashers import make_password
from django.contrib.contenttypes.models import ContentType
from .models import User, Slide, ResearchArtifact, Documentation, Event, Calendar, Rule
from django.db.models.fields.related import ForeignKey
from rest_framework.decorators import action
from rest_framework.fields import empty, set_value
from django.core.exceptions import ValidationError
from cdh.fields import MonacoEditorField, ViewEditField, MarkdownEditorField


logger = logging.getLogger(__name__)


class CdhSerializer(ModelSerializer):

    def __init__(self, *argv, **argd):
        for field in self.Meta.model._meta.fields:
            if isinstance(field, ForeignKey):
                self.fields[field.name] = HyperlinkedRelatedField(
                    view_name="api:{}-detail".format(field.related_model._meta.model_name),
                    queryset=field.related_model.objects.all()
                )            
        retval = super(CdhSerializer, self).__init__(*argv, **argd)
        self.fields["url"] = HyperlinkedIdentityField(
            view_name="api:{}-detail".format(self.Meta.model._meta.model_name),
            lookup_field="id",
            lookup_url_kwarg="pk"
        )
        self.fields["created_by"] = HiddenField(
            default=CurrentUserDefault()
        )
        return retval


class UserSerializer(CdhSerializer):
    description = MarkdownEditorField(language="markdown", property_field="description", allow_blank=True, required=False, endpoint="markdown")
    class Meta:
        model = User
        fields = ["first_name", "last_name", "homepage", "title", "photo", "description", "url", "id", "password", "email", "username", "created_by"]
        view_fields = ["description"]
        edit_fields = ["first_name", "last_name", "homepage", "title", "photo", "description", "url", "id"]
        create_fields = ["first_name", "last_name", "homepage", "title", "photo", "description", "url", "id", "password", "email", "username", "created_by"]
        extra_kwargs = dict(
            [
                ("password", {"write_only" : True, "required" : False}),
                ("email", {"write_only" : True, "required" : False}),
                ("username", {"write_only" : True, "required" : False}),
            ] + [(f, {"required" : False}) for f in edit_fields]
        )
        
    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data.get('password'))
        return super(UserSerializer, self).create(validated_data)

    
class SlideSerializer(CdhSerializer):
    article = MarkdownEditorField(language="markdown", property_field="article", allow_blank=True, required=False, endpoint="markdown")
    class Meta:
        model = Slide
        fields = [f.name for f in Slide._meta.fields if not isinstance(f, ForeignKey)] + ["url", "created_by"]
        view_fields = ["url", "image", "article", "id"]
        edit_fields = ["name", "url", "image", "article", "id"]
        create_fields = ["name", "url", "image", "article", "id"]


class EventSerializer(CdhSerializer):
    url = HyperlinkedIdentityField(
        view_name="api:event-detail",
        lookup_field="id",
        lookup_url_kwarg="pk"
    )
    created_by = HiddenField(
        default=CurrentUserDefault()
    )
    class Meta:
        model = Event
        fields = ["title", "start", "end", "calendar", "description", "created_by", "url", "id"]

    def to_internal_value(self, data):
        ret = OrderedDict()
        for field in self._writable_fields:
            if field.field_name in ["event_ptr", "creator", "rule"]:
                continue
            value = field.get_value(data)
            validated_value = field.run_validation(value)
            set_value(ret, field.source_attrs, validated_value)
        return ret
    
    def is_valid(self, raise_exception=False):
        assert hasattr(self, 'initial_data'), (
            'Cannot call `.is_valid()` as no `data=` keyword argument was '
            'passed when instantiating the serializer instance.'
        )
        if not hasattr(self, '_validated_data'):
            try:
                self._validated_data = self.run_validation(self.initial_data)
            except ValidationError as exc:
                self._validated_data = {}
                self._errors = exc.detail
            else:
                self._errors = {}
        return True
    
    def save(self):
        self.validated_data["name"] = self.validated_data["title"]
        self.validated_data["creator"] = self.validated_data["created_by"]
        self.instance = Event.objects.create(**self.validated_data)
        return self.instance


class RuleSerializer(CdhSerializer):
    # url = HyperlinkedIdentityField(
    #     view_name="api:schedulerule-detail",
    #     lookup_field="id",
    #     lookup_url_kwarg="pk"
    # )
    # created_by = HiddenField(
    #     default=CurrentUserDefault()
    # )
    class Meta:
        model = Rule
        fields = ["name", "description", "frequency", "params", "created_by", "url", "id"]
                  
    def to_internal_value(self, data):
        ret = OrderedDict()
        for field in self._writable_fields:
            if field.field_name in ["rule_ptr"]:
                continue
            print(field.field_name)
            value = field.get_value(data)
            validated_value = field.run_validation(value)
            set_value(ret, field.source_attrs, validated_value)
        print(ret)
        return ret
    
    def is_valid(self, raise_exception=False):
        assert hasattr(self, 'initial_data'), (
            'Cannot call `.is_valid()` as no `data=` keyword argument was '
            'passed when instantiating the serializer instance.'
        )
        if not hasattr(self, '_validated_data'):
            try:
                self._validated_data = self.run_validation(self.initial_data)
            except ValidationError as exc:
                self._validated_data = {}
                self._errors = exc.detail
            else:
                self._errors = {}
        return True
    
    def save(self):
        self.instance = Rule.objects.create(**self.validated_data)
        return self.instance
    

class CalendarSerializer(CdhSerializer):
    url = HyperlinkedIdentityField(
        view_name="api:calendar-detail",
        lookup_field="id",
        lookup_url_kwarg="pk"
    )
    created_by = HiddenField(
        default=CurrentUserDefault()
    )
    
    class Meta:
        model = Calendar
        fields = ["name", "slug", "created_by", "url", "id"]

    def to_internal_value(self, data):
        ret = OrderedDict()
        for field in self._writable_fields:
            print(field)
            if field.field_name == "calendar_ptr":
                continue
            value = field.get_value(data)
            validated_value = field.run_validation(value)
            set_value(ret, field.source_attrs, validated_value)
        return ret
    
    #def run_validation(self, data=empty):
    #    return data
#        return self.to_internal_value(data)
        
    def is_valid(self, raise_exception=False):
        print(1234321)
        assert hasattr(self, 'initial_data'), (
            'Cannot call `.is_valid()` as no `data=` keyword argument was '
            'passed when instantiating the serializer instance.'
        )
        if not hasattr(self, '_validated_data'):
            try:
                self._validated_data = self.run_validation(self.initial_data)
            except ValidationError as exc:
                self._validated_data = {}
                self._errors = exc.detail
            else:
                self._errors = {}
        return True
    
    def save(self):
        self.instance = Calendar.objects.create(**self.validated_data)
        return self.instance

        
class ResearchArtifactSerializer(CdhSerializer):
    description = MarkdownEditorField(language="markdown", property_field="description", allow_blank=True, required=False, endpoint="markdown")
    name = CharField(source="title", required=False)
    class Meta:
        model = ResearchArtifact
        fields = [f.name for f in ResearchArtifact._meta.fields if not isinstance(f, ForeignKey)] + ["url", "created_by"]
        view_fields = ["description"]
        edit_fields = [f.name for f in ResearchArtifact._meta.fields if not isinstance(f, ForeignKey) and not f.name in ["name"]] + ["url", "created_by"]
        create_fields = [f.name for f in ResearchArtifact._meta.fields if not isinstance(f, ForeignKey)] + ["url", "created_by"]
        extra_kwargs = dict([(f, {"required" : False}) for f in create_fields])
        

class DocumentationSerializer(ModelSerializer):
    content = MarkdownEditorField(language="markdown", property_field="content", allow_blank=True, required=False, endpoint="markdown")
    view_name = CharField()
    object_id = IntegerField(required=False)
    content_type = PrimaryKeyRelatedField(queryset=ContentType.objects, allow_null=True)
    name = CharField()
    url = HyperlinkedIdentityField(
       view_name="api:documentation-detail",
       lookup_field="id",
       lookup_url_kwarg="pk"
    )
    created_by = HiddenField(
        default=CurrentUserDefault()
    )
    
    class Meta:
        model = Documentation        
        fields = ["content", "name", "view_name", "content_type", "object_id", "url", "created_by", "id"]
        view_fields = ["content"] + ["url", "created_by"]
        edit_fields = ["content", "view_name", "content_type", "object_id", "name", "url", "created_by", "id"]
        create_fields = ["content", "view_name", "content_type", "object_id", "name", "created_by", "id"]
