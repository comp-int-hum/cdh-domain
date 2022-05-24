from cdh import settings
import os.path
from cdh.admin import CDHModelAdmin, site
from django.contrib import admin
from django.utils.html import format_html
import os
from .models import TopicModel, Collection, Document, Lexicon, LabeledCollection, LabeledDocument
from django.db.models import JSONField
from .forms import CollectionForm, LexiconForm, LabeledCollectionForm
from guardian.admin import GuardedModelAdmin
from django_json_widget.widgets import JSONEditorWidget
from .tasks import train_model, extract_documents, apply_model


class TopicModelAdmin(CDHModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('name', 'collection', 'topic_count', 'lowercase', 'max_context_size')
        }),
        ('Advanced options', {
            #'classes': ('collapse',),
            'fields': ('maximum_documents', 'maximum_vocabulary', "minimum_occurrence", 'maximum_proportion', 'chunk_size', 'passes', 'update_every', 'alpha', 'eta', 'iterations', 'random_seed', 'split_pattern', 'token_pattern_in', 'token_pattern_out'),
        }),
    )
    #def has_change_permission(self, request, obj=None):
    #    return False

    def save_model(self, request, obj, form, change):
        res = super().save_model(request, obj, form, change)
        train_model.delay(obj.id)
        
    #def delete_model(self, request, obj):
        #try:
        #    for f in [obj.disk_serialized, obj.disk_serialized_param, obj.disk_serialized_dict, obj.disk_serialized_state]:
        #        os.remove(f.path)
        #except:
        #    pass
        #super().delete_model(request, obj)
        
    def delete_queryset(self, request, queryset):
        for obj in queryset:
            self.delete_model(request, obj)


class CollectionAdmin(CDHModelAdmin):
    form = CollectionForm
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if request.FILES.get("upload", None):
            ufname = request.FILES["upload"].name
            ext = os.path.splitext(ufname)[-1]
            path = settings.MEDIA_ROOT / "shared" / "topic_modeling" / "collections"
            if not os.path.exists(path):
                os.makedirs(path)
            ofname = path / "{}{}".format(obj.id, ext)
            with open(ofname, "wb") as ofd:
                for chunk in request.FILES["upload"].chunks():
                    ofd.write(chunk)
        extract_documents.delay(obj.id, str(ofname))


class LexiconAdmin(CDHModelAdmin):
    form = LexiconForm
    formfield_overrides = {
        JSONField: {'widget': JSONEditorWidget},
    }


class LabeledCollectionAdmin(CDHModelAdmin):
    form = LabeledCollectionForm
    def save_model(self, request, obj, form, change):
        if obj.model and obj.lexicon:
            raise Exception("Can't have both a model and a lexicon!")
        if not obj.collection:
            raise Exception("Must choose a collection to apply the model to!")
        res = super().save_model(request, obj, form, change)
        apply_model.delay(obj.id)

        
            
site.register(TopicModel, TopicModelAdmin)
site.register(Collection, CollectionAdmin)
site.register(Lexicon, LexiconAdmin)
site.register(LabeledCollection, LabeledCollectionAdmin)
