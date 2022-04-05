from django.contrib import admin
from .models import User, Slide
from .forms import AdminUserForm
from guardian.admin import GuardedModelAdmin
from guardian.shortcuts import assign_perm
from django.contrib.flatpages.admin import FlatPageAdmin
from django.contrib.flatpages.models import FlatPage
from django.utils.translation import gettext_lazy as _

class CDHAdminSite(admin.AdminSite):
    def has_permission(self, request):
        return request.user.is_authenticated
        
site = CDHAdminSite()

# class UserAdmin(admin.ModelAdmin):
#     form = AdminUserForm
#     def has_module_permission(self, request):
#         return request.user.is_authenticated
#     def has_change_permission(self, request, obj=None):
#         return obj == None or (obj == request.user and request.user.is_authenticated)
#     def has_view_permission(self, request, obj=None):
#         return obj == None or (obj == request.user and request.user.is_authenticated)

class SlideAdmin(GuardedModelAdmin):
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

class FlatPageAdmin(FlatPageAdmin):
    fieldsets = (
        (None, {'fields': ('url', 'title', 'content', 'sites')}),
        (_('Advanced options'), {
            'classes': ('collapse',),
            'fields': (
                'enable_comments',
                'registration_required',
                'template_name',
            ),
        }),
    )
    def has_module_permission(self, request):
        return request.user.is_authenticated    

    def has_add_permission(self, request):
        return request.user.is_authenticated

    def has_view_permission(self, request, obj=None):
        return request.user.is_authenticated and (obj==None or (request.user.has_perm("view_flat_page", obj)))

    def has_change_permission(self, request, obj=None):
        return obj == None or (request.user.is_authenticated and (request.user.has_perm("change_flat_page", obj)))

    def has_delete_permission(self, request, obj=None):
        return obj == None or (request.user.is_authenticated and (request.user.has_perm("delete_flat_page", obj)))

site.register(Slide, SlideAdmin)
#site.register(User, UserAdmin)
site.register(FlatPage, FlatPageAdmin)
