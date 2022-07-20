from . import settings
from django import forms
from django.core.exceptions import ValidationError
from django_registration.forms import RegistrationFormUniqueEmail
from . import models
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.shortcuts import render
from django.db.models import Field
from guardian.shortcuts import get_perms
from django.template.response import SimpleTemplateResponse, TemplateResponse
from django.template import Engine, Template, RequestContext

if settings.USE_LDAP:
    import ldap
    from ldap import modlist

    
# class TabbedMixin(object):
#     def __init__(self, *argv, user=None, **argd):
#         super(TabbedMixin, self).__init__(*argv, **argd)
#         self.user = user

#     @property
#     def tab_names(self):
#         return self.tab_names

#     def render_tab(self, name):
#         return name
    
#     class Meta:
#         abstract = True

#     def __str__(self, *argv, **argd):
#         if len(self.tab_names) > 0 and self.instance.id:
#             lines = []
#             lines.append("""<ul class="nav nav-tabs" id="{0}_tabnav" role="tablist">""".format(self.prefix))
#             for i, name in enumerate(self.tab_names):
#                 active, selected = ("active", "true") if i == 0 else ("", "false")
#                 lines.append("""<li class="nav-item" role="presentation"><button class="nav-link cdh-tab-button {3}" id="{2}_{1}_navitem" data-bs-toggle="tab" data-bs-target="#{2}_{1}_contentitem" type="button" role="tab" aria-controls="{2}_{1}_contentitem" aria-selected="{4}">{0}</button></li>""".format(name, i, self.prefix, active, selected))
#             lines.append("""</ul>""")
#             lines.append("""<div class="tab-content" id="{0}_content">""".format(self.prefix))
#             for i, name in enumerate(self.tab_names):
#                 show, active = ("show", "active") if i == 0 else ("", "")
#                 lines.append("""
#                 <div class="tab-pane fade {3} {4}" id="{2}_{1}_contentitem" role="tabpanel" aria-labelledby="{2}_{1}_navitem">
#                 {0}
#                 </div>
#                 """.format(self.render_tab(name), i, self.prefix, show, active))
#             lines.append("""</div>""")
#             return "".join(lines)
#         else:
#             return super().render(*argv, **argd)
    

# class AccordionFormSet(forms.BaseFormSet):

#     action_lookup = {
#         "change" : "Save",
#         "delete" : "Delete",
#     }
    
#     def __init__(self, instance, request, post_data=None, file_data=None, *argv, **argd):
#         """
#         The "hierarchy" corresponds to the nested accordion structure, where each location is described as a
#         recursive dictionary.  The dictionary fields, if present, must have the types described below.  In
#         general, each dictionary should probably have either the "children" field, or both the "form" and
#         "object" fields (or all three).

#         The field types and their interpretations are:

#           "children" should be a list of dictionaries describing the items that will exist under this one

#           "form" should be a ModelForm-derived class that will be used to present objects of this item's *children*

#           "object" should be an object of the type associated with this item's *parent* form

#           "description" should be a string that will appear in this item when expanded, before its object or children        
#         """
#         super(AccordionFormSet, self).__init__(*argv, **argd)
#         self.is_bound = True
#         self.renderer = forms.renderers.get_default_renderer()
#         #self.min_num = 0
#         self.extra = 0
#         #self.max_num = 1000
#         self.instance = instance
#         self.user = request.user
#         self.request = request
        
#     def render(self, position, form=None, depth=0, extra_prefix=[]):
#         con = RequestContext(self.request, {})
#         csrf = Template("{% csrf_token %}").render(con)
#         title = position.get("title", str(position.get("object")) if "object" in position else None)
#         if not title and "child_form" in position:
#             if hasattr(position["child_form"], "_meta"):
#                 title = position["child_form"]._meta.model._meta.verbose_name_plural.title()
#             else:
#                 title = position["child_form"].model_class._meta.verbose_name_plural.title()
#         children = [
#             self.render(
#                 c,
#                 form=position.get("child_form"),
#                 depth=depth + 1,
#                 extra_prefix=extra_prefix + [(c["object"].id if "object" in c else i)]
#             ) for i, c in enumerate(position.get("children", []))]
        
#         strings = []
#         if depth == 0:
#             # If at depth 0, we are *not* in an accordion: at most, render a title and, if there are children, an accordion

#             # We're at the top, so the prefix is already unique
#             actual_prefix = self.prefix
#             #if title:
#             #    strings.append("""<h1 id="{0}_title">{1}</h1>""".format(actual_prefix, title))
                
#             if len(children) > 0:
#                 # There are children, so place them in an accordion
#                 strings.append("""<div class="accordion" id="{0}_accordion" aria-labelledby="{0}_title">""".format(actual_prefix))
#                 strings += children
#                 strings.append("""</div>""")
#         else:
#             # if at non-zero depth, we *are* in an accordion, so this needs to be an accordion item, potentially with its own (sub)-accordion
#             actual_prefix = "{0}_{1}".format(self.prefix, "_".join([str(x) for x in extra_prefix]))
#             h_tag = "h{}".format(depth + 1)
#             strings.append("""<div class="accordion-item" id="{0}_item">""".format(actual_prefix))
#             strings.append("""<{0} class="accordion-header" id="{1}_header">""".format(h_tag, actual_prefix))

#             strings.append("""<button class="accordion-button cdh-accordion-button collapsed" data-bs-toggle="collapse" type="button" aria-expanded="false" data-bs-target="#{0}_content" id="{0}_button" aria-controls="{0}_content">{1}</button>""".format(actual_prefix, title))
#             strings.append("""</{0}>""".format(h_tag))
#             strings.append("""<div class="accordion-collapse collapse w-95 ps-4" id="{0}_content" aria-labelledby="{0}_header">""".format(actual_prefix))
#             if "object" in position:

#                 strings.append("""<form method="post">
#                 {}
#                 """.format(csrf))
#                 perms = get_perms(self.user, position["object"])
#                 actions = set([x.split("_")[0] for x in perms])
#                 strings.append("""<div class="btn-group" label="actions" aria-label="actions" id="{0}_action_group">""".format(actual_prefix))
#                 if "change" in actions:
#                     strings.append("""<button class="btn btn-primary" name="action" value="change {}">Save</button>""".format(actual_prefix))
#                 if "delete" in actions:
#                     strings.append("""<button class="btn btn-danger" name="action" value="delete {}">Delete</button>""".format(actual_prefix))
#                 strings.append("""</div>""")
#                 try:
#                     strings.append(str(form(user=self.user, instance=position["object"], prefix=actual_prefix)))
#                 except:
#                     strings.append(str(form(instance=position["object"], prefix=actual_prefix)))
#                 strings.append("""</form>""")
#             if len(children) > 0:
#                 strings.append("""<div class="accordion" id="{}_accordion">""".format(actual_prefix))
#                 strings += children
#                 perms = get_perms(self.user, position["children"][0]["object"])
#                 actions = set([x.split("_")[0] for x in perms])
#                 if "child_form" in position and "add" in actions:
#                     strings.append("""<form method="post">
#                     {}
#                     """.format(csrf))
#                     try:
#                         strings.append("""
#                         <div class="accordion-item" id="{1}_item_blank">
#                         <{0} class="accordion-header" id="{1}_header_blank">
#                         <button "accordion-button cdh-accordion-button collapsed" data-bs-toggle="collapse" type="button" aria-expanded="false" data-bs-target="#{1}_content_blank" id="{1}_button_blank">+</button>
#                         </{0}>
#                         <div class="accordion-collapse collapse w-95 ps-4" id="{1}_content_blank" aria-labelledby="{1}_header_blank">
#                         <div class="btn-group" label="actions" aria-label="actions" id="{1}_action_group">
#                         <button class="btn btn-primary" name="action" value="save {1}">Save</button>
#                         </div>
#                         {2}
#                         </div>
#                         """.format(h_tag, actual_prefix, position["child_form"](user=self.user, use_required_attribute=False, prefix="{}_blank".format(actual_prefix))))
                        
#                     except:
#                         strings.append("""
#                         <div class="accordion-item" id="{1}_item_blank">
#                         <{0} class="accordion-header" id="{1}_header_blank">
#                         <button "accordion-button cdh-accordion-button collapsed" data-bs-toggle="collapse" type="button" aria-expanded="false" data-bs-target="#{1}_content_blank" id="{1}_button_blank">+</button>
#                         </{0}>
#                         <div class="accordion-collapse collapse w-75 ps-4" id="{1}_content_blank" aria-labelledby="{1}_header_blank">
#                         <div class="btn-group" label="actions" aria-label="actions" id="{1}_action_group">
#                         <button class="btn btn-primary" name="action" value="save {1}">Save</button>
#                         </div>
#                         {2}
#                         </div>
#                         """.format(h_tag, actual_prefix, position["child_form"](use_required_attribute=False, prefix="{}_blank".format(actual_prefix))))

#                        # TODO: add "data-bs-parent"...
#                     strings.append("""</form>""")
#                 strings.append("""</div>""")
#             strings.append("""</div>""")
#             strings.append("""</div>""")
#         return(mark_safe("".join(strings)))

        
#     def __str__(self):
#         return self.render(self.instance)
    

class AdminUserForm(forms.ModelForm):
    class Meta:
        model = models.User
        fields = "__all__"
        widgets = {
            "first_name" : forms.TextInput(attrs={}), #area(attrs={"cols" : 30, "rows" : 1})
            #"description" : MonacoEditorWidget(name="default", language="html", wordwrap=True)
        }

        
class ModifyUserForm(forms.ModelForm):
    class Meta:
        model = models.User
        fields = ["first_name", "last_name", "title", "homepage", "photo", "description"]
        widgets = {
            "first_name" : forms.TextInput(attrs={}) #area(attrs={"cols" : 30, "rows" : 1})
        }
        
class UserForm(RegistrationFormUniqueEmail):
    def clean_email(self):
        data = self.cleaned_data["email"].lower()
        if not any([data.endswith(s) for s in ["jh.edu", "jhu.edu", "jhmi.edu"]]):
            raise ValidationError("Email address must end with 'jh.edu', 'jhu.edu', or 'jhmi.edu'")
        else:
            return data
    def clean_username(self):
        name = self.cleaned_data["username"].lower()
        return name
    class Meta(RegistrationFormUniqueEmail.Meta):
        model = models.User
        fields = ["username", "email", "first_name", "last_name"]
    def save(self, *argv, **argd):
        if settings.USE_LDAP:
            ld = ldap.initialize(settings.AUTH_LDAP_SERVER_URI)
            if settings.AUTH_LDAP_START_TLS == True:
                ld.set_option(ldap.OPT_X_TLS_CACERTFILE, settings.CDH_LDAP_CERTFILE)
                ld.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_DEMAND)
                ld.set_option(ldap.OPT_X_TLS_NEWCTX, 0)
                ld.start_tls_s()
                ld.simple_bind_s(settings.AUTH_LDAP_BIND_DN, settings.AUTH_LDAP_BIND_PASSWORD)
            else:
                ld.bind_s(settings.AUTH_LDAP_BIND_DN, settings.AUTH_LDAP_BIND_PASSWORD)
            current_users = {}
            for dn, attrs in ld.search_st(
                    settings.CDH_LDAP_USER_BASE,
                    ldap.SCOPE_SUBTREE,
                    filterstr="(!(objectClass=organizationalUnit))"
            ):
                current_users[attrs["uid"][0]] = (dn, attrs)

            bf = {s : bytes(self.cleaned_data[s], "utf-8") for s in ["email", "username", "first_name", "last_name"]}
            home = bytes("/home/{}".format(self.cleaned_data["username"]), "utf-8")
            dn = "uid={},{}".format(self.cleaned_data["username"], settings.CDH_LDAP_USER_BASE)
            next_uid_number = max([2000] + [int(x[1]["uidNumber"][0]) for x in current_users.values()]) + 1
            item = {
                "objectClass" : [b"inetOrgPerson", b"posixAccount", b"shadowAccount"],
                "mail" : [bf["email"]],
                "sn" : [bf["last_name"]],
                "givenName" : [bf["first_name"]],
                "uid" : [bf["username"]],
                "cn" : [bf["username"]],
                "uidNumber" : [bytes(str(next_uid_number), "utf-8")],
                "gidNumber" : [b"100"],
                "loginShell" : [b"/bin/bash"],
                "homeDirectory" : [home],
                "gecos" : [bf["username"]],
            }
            ld.add_s(dn, modlist.addModlist(item))
            ld.passwd_s(dn, None, self.data["password1"])
            for gdn in [settings.CDH_LDAP_WEB_GROUP_DN, settings.CDH_LDAP_WORKSTATION_GROUP_DN]:
                ld.modify_s(
                    gdn,
                    [
                        (ldap.MOD_ADD, 'memberUid', [bf["username"]]),
                    ],
                )

        user = super().save(*argv, **argd)
        # this second save seems necessary to prevent populating the password field in SQL?
        user.save()
        return user

        
