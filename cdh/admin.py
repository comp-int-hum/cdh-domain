from django.contrib import admin
from django.contrib.auth.models import Group
from .models import User, Slide, SlidePage
from .forms import AdminUserForm
from guardian.admin import GuardedModelAdmin
from guardian.shortcuts import assign_perm
from django.contrib.flatpages.admin import FlatPageAdmin
from django.contrib.flatpages.models import FlatPage
from django.contrib.sites.models import Site
from django.utils.translation import gettext_lazy as _
from turkle.admin import CustomUserAdmin as TurkleUserAdmin
from turkle.admin import CustomGroupAdmin as TurkleGroupAdmin
from wiki.models import Article
from markdownfield.models import MarkdownField, RenderedMarkdownField
from markdownfield.widgets import MDEWidget, MDEAdminWidget
#from wiki.plugins.attachments.models import Attachment

class CDHAdminSite(admin.AdminSite):
    def has_permission(self, request):
        return request.user.is_authenticated
    
site = CDHAdminSite(name="main")


class CDHModelAdmin(GuardedModelAdmin):
    def has_module_permission(self, request):
        return request.user.is_authenticated    

    def has_add_permission(self, request):
        return request.user.is_authenticated

    def has_view_permission(self, request, obj=None):
        return request.user.is_authenticated and (obj==None or (request.user.has_perm("view_{}".format(obj._meta.model_name), obj)))

    def has_change_permission(self, request, obj=None):
        return obj == None or (request.user.is_authenticated and (request.user.has_perm("change_{}".format(obj._meta.model_name), obj)))

    def has_delete_permission(self, request, obj=None):
        return obj == None or (request.user.is_authenticated and (request.user.has_perm("delete_{}".format(obj._meta.model_name), obj)))


## For now, let Turkle set this up
#
class UserAdmin(admin.ModelAdmin):
    form = AdminUserForm
    def has_module_permission(self, request):
        return request.user.is_authenticated
    def has_change_permission(self, request, obj=None):
        return obj == None or (obj == request.user and request.user.is_authenticated)
    def has_view_permission(self, request, obj=None):
        return obj == None or (obj == request.user and request.user.is_authenticated)


class CustomGroupAdmin(TurkleGroupAdmin):
    pass


class CustomUserAdmin(TurkleUserAdmin):
    def get_fieldsets(self, request, obj=None):
        if request.user.is_superuser:
            permission_fields = (
                'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions', 'photo')
        else:
            permission_fields = (
                'is_active', 'is_staff', 'groups', 'photo')

        #if not obj:
            # Adding
            #return (
                #(None, {'fields': ('username',)}),
                #('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
                #('Permissions', {'fields': permission_fields}))
        #else:
            # Changing
        return (
                #(None, {'fields': ('username', 'password')}),
                (None, {'fields': ('first_name', 'last_name', 'email', 'homepage', 'title', 'description')}),
                )
                #('Permissions', {'fields': permission_fields}),
                #('Important dates', {'fields': ('last_login', 'date_joined')}))
    pass
    
    
class SlideAdmin(GuardedModelAdmin):
    formfield_overrides = {
        MarkdownField : {"widget" : MDEWidget},
    }
    def has_module_permission(self, request):
        return request.user.is_authenticated    

    def has_add_permission(self, request):
        return request.user.is_authenticated

    def has_view_permission(self, request, obj=None):
        return request.user.is_authenticated and (obj==None or (request.user.has_perm("view_slide", obj)))

    def has_change_permission(self, request, obj=None):
        return obj == None or (request.user.is_authenticated and (request.user.has_perm("change_slide", obj)))

    def has_delete_permission(self, request, obj=None):
        return obj == None or (request.user.is_authenticated and (request.user.has_perm("delete_slide", obj)))

class SlidePageAdmin(GuardedModelAdmin):
    def has_module_permission(self, request):
        return request.user.is_authenticated    

    def has_add_permission(self, request):
        return request.user.is_authenticated

    def has_view_permission(self, request, obj=None):
        return request.user.is_authenticated and (obj==None or (request.user.has_perm("view_slide_page", obj)))

    def has_change_permission(self, request, obj=None):
        return obj == None or (request.user.is_authenticated and (request.user.has_perm("change_slide_page", obj)))

    def has_delete_permission(self, request, obj=None):
        return obj == None or (request.user.is_authenticated and (request.user.has_perm("delete_slide_page", obj)))

# class FlatPageAdmin(FlatPageAdmin):
#     fieldsets = (
#         (None, {'fields': ('url', 'title', 'content', 'sites')}),
#         (_('Advanced options'), {
#             'classes': ('collapse',),
#             'fields': (
#                 'enable_comments',
#                 'registration_required',
#                 'template_name',
#             ),
#         }),
#     )
#     def has_module_permission(self, request):
#         return request.user.is_authenticated    

#     def has_add_permission(self, request):
#         return request.user.is_authenticated

#     def has_view_permission(self, request, obj=None):
#         return request.user.is_authenticated and (obj==None or (request.user.has_perm("view_flat_page", obj)))

#     def has_change_permission(self, request, obj=None):
#         return obj == None or (request.user.is_authenticated and (request.user.has_perm("change_flat_page", obj)))

#     def has_delete_permission(self, request, obj=None):
#         return obj == None or (request.user.is_authenticated and (request.user.has_perm("delete_flat_page", obj)))

site.register(Slide, SlideAdmin)
site.register(SlidePage, SlidePageAdmin)
site.register(User, CustomUserAdmin)
site.register(Group, CustomGroupAdmin)
#site.register(Site)
#site.register(Article)
#site.register(FlatPage)
#site.register(Attachment)

#from filer.models import Image, File, Folder, Clipboard, FolderPermission, ThumbnailOption
#from filer.admin import FileAdmin, ImageAdmin, FolderAdmin, ClipboardAdmin, PermissionAdmin, ThumbnailOptionAdmin

#site.register(Folder, FolderAdmin)
#site.register(File, FileAdmin)
#site.register(Clipboard, ClipboardAdmin)
#site.register(Image, ImageAdmin)
#site.register(FolderPermission, PermissionAdmin)
#site.register(ThumbnailOption, ThumbnailOptionAdmin)
