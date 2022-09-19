import logging
from rest_framework.serializers import ModelSerializer, BaseSerializer, HyperlinkedModelSerializer, HiddenField, HyperlinkedIdentityField, ReadOnlyField, CurrentUserDefault, HyperlinkedRelatedField, PrimaryKeyRelatedField, CharField, IntegerField
from django.contrib.auth.hashers import make_password
from django.contrib.contenttypes.models import ContentType
from .models import User, Slide, ResearchArtifact, Documentation
from django.db.models.fields.related import ForeignKey
from rest_framework.decorators import action
from cdh.fields import MonacoEditorField


logger = logging.getLogger(__name__)


class CdhSerializer(ModelSerializer):
    def __init__(self, *argv, **argd):
        for field in self.Meta.model._meta.fields:
            if isinstance(field, ForeignKey):
                self.fields[field.name] = HyperlinkedRelatedField(view_name="api:{}-detail".format(field.related_model._meta.model_name), queryset=field.related_model.objects.all())
            
        super(CdhSerializer, self).__init__(*argv, **argd)
        self.fields["url"] = HyperlinkedIdentityField(
            view_name="api:{}-detail".format(self.Meta.model._meta.model_name),
            lookup_field="id",
            lookup_url_kwarg="pk"
        )
        self.fields["created_by"] = HiddenField(
            default=CurrentUserDefault()
        )


class UserSerializer(CdhSerializer):
    
    class Meta:
        model = User
        fields = ["first_name", "last_name", "homepage", "title", "photo", "description", "url", "id", "password", "email", "username", "created_by"]
        view_fields = ["first_name", "last_name", "homepage", "title", "photo", "description", "url", "id", "email", "username", "created_by"]
        edit_fields = ["first_name", "last_name", "homepage", "title", "photo", "description", "url", "id", "password", "email", "username", "created_by"]
        create_fields = ["first_name", "last_name", "homepage", "title", "photo", "description", "url", "id", "password", "email", "username", "created_by"]
        extra_kwargs = {
            "password" : {"write_only" : True},
            "email" : {"write_only" : True},
            "username" : {"write_only" : True},
        }
        
    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data.get('password'))
        return super(UserSerializer, self).create(validated_data)

    
class SlideSerializer(CdhSerializer):
    class Meta:
        model = Slide
        fields = [f.name for f in Slide._meta.fields if not isinstance(f, ForeignKey)] + ["url", "created_by"]
        view_fields = ["url", "image", "article", "id"]
        edit_fields = ["url", "image", "article", "id"]
        create_fields = ["url", "image", "article", "id"]
        

class ResearchArtifactSerializer(CdhSerializer):
    class Meta:
        model = ResearchArtifact
        fields = [f.name for f in ResearchArtifact._meta.fields if not isinstance(f, ForeignKey)] + ["url", "created_by"]
        view_fields = [f.name for f in ResearchArtifact._meta.fields if not isinstance(f, ForeignKey)] + ["url", "created_by"]
        edit_fields = [f.name for f in ResearchArtifact._meta.fields if not isinstance(f, ForeignKey)] + ["url", "created_by"]
        create_fields = [f.name for f in ResearchArtifact._meta.fields if not isinstance(f, ForeignKey)] + ["url", "created_by"]
        

class DocumentationSerializer(ModelSerializer):

    content = MonacoEditorField(language="markdown", property_field="content", allow_blank=True, required=False, endpoint="markdown")

    view_name = CharField()
    object_id = IntegerField(required=False)
    content_type = PrimaryKeyRelatedField(queryset=ContentType.objects)
    #content_type = 
    #object_id = PrimaryKeyRelatedField()
    name = CharField()
    #def __init__(self, *argv, **argd):
    #    super(DocumentationSerializer, self).__init__(*argv, **argd)
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
        #[f.name for f in Documentation._meta.fields if not isinstance(f, ForeignKey) and f.name not in ["name"]] + ["url", "created_by"]
        view_fields = ["content"] + ["url", "created_by"]
        edit_fields = ["content", "url", "created_by", "id"]
        create_fields = ["content", "url", "created_by", "id"]

    #def __init__(self, *argv, **argd):
    #    super(DocumentationSerializer, self).__init__(*argv, **argd)
