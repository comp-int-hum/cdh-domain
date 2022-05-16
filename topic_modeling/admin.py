from cdh.admin import CDHModelAdmin, site
import os
from .models import TopicModel, Collection, Lexicon, Output
from django.db.models import JSONField
from .forms import CollectionForm, LexiconForm, OutputForm
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
            'fields': ('minimum_count', 'maximum_proportion', 'chunk_size', 'passes', 'update_every', 'alpha', 'eta', 'iterations', 'random_seed', 'split_pattern', 'token_pattern_in', 'token_pattern_out', 'state'),
        }),
    )
    readonly_fields = ["state"]

    def has_change_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        res = super().save_model(request, obj, form, change)
        train_model.delay(obj.id)
        
    def delete_model(self, request, obj):
        try:
            for f in [obj.disk_serialized, obj.disk_serialized_param, obj.disk_serialized_dict, obj.disk_serialized_state]:
                os.remove(f.path)
        except:
            pass
        super().delete_model(request, obj)
        
    def delete_queryset(self, request, queryset):
        for obj in queryset:
            self.delete_model(request, obj)


class CollectionAdmin(CDHModelAdmin):
    form = CollectionForm
    readonly_fields = ["state"]    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        obj = Collection.objects.get(id=obj.id)
        with open(obj.disk_serialized.path, "rb") as ifd:
            obj.db_serialized = ifd.read()
        obj.save()
        extract_documents.delay(obj.id)
        
    def delete_model(self, request, obj):
        fname_a = obj.disk_serialized.path
        fname_b = obj.disk_serialized_processed.path
        super().delete_model(request, obj)
        os.remove(fname_a)
        os.remove(fname_b)
        
    def delete_queryset(self, request, queryset):
        for obj in queryset:
            self.delete_model(request, obj)


class LexiconAdmin(CDHModelAdmin):
    form = LexiconForm
    formfield_overrides = {
        JSONField: {'widget': JSONEditorWidget},
    }


class OutputAdmin(CDHModelAdmin):
    form = OutputForm
    readonly_fields = ["state"]        
    def save_model(self, request, obj, form, change):
        if obj.model and obj.lexicon:
            raise Exception("Can't have both a model and a lexicon!")
        if not obj.collection:
            raise Exception("Must choose a collection to apply the model to!")
        res = super().save_model(request, obj, form, change)
        apply_model.delay(obj.id)

    def delete_model(self, request, obj):
        try:
            os.remove(obj.disk_serialized.path)
        except:
            pass
        super().delete_model(request, obj)
        
    def delete_queryset(self, request, queryset):
        for obj in queryset:
            self.delete_model(request, obj)
        
            
site.register(TopicModel, TopicModelAdmin)
site.register(Collection, CollectionAdmin)
site.register(Lexicon, LexiconAdmin)
site.register(Output, OutputAdmin)
