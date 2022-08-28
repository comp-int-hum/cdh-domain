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
from django.forms import FileField, ModelForm
from guardian.shortcuts import assign_perm, get_anonymous_user
from django.template.engine import Engine
from django.template import Context

template_engine = Engine.get_default()

if settings.USE_LDAP:
    import ldap
    from ldap import modlist


class CdhFileField(FileField):
    pass    


class PublicUserForm(forms.ModelForm):
    def __init__(self, *argv, **argd):
        return super(PublicUserForm, self).__init__(*argv, **argd)
    def __str__(self):
        for name, field in self.fields.items():            
            if field.widget.attrs.get("readonly", "false") != "true":
                return super(PublicUserForm, self).__str__()        
        content = template_engine.get_template("cdh/snippets/person.html").render(
            Context(
                {name : getattr(self.instance, name) for name in ["first_name", "last_name", "photo", "description", "title", "homepage"]}
            )
        )
        return mark_safe(content)


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
        user.save()
        assign_perm("cdh.view_user", get_anonymous_user(), user)
        assign_perm("cdh.change_user", user, user)
        
        # this second save seems necessary to prevent populating the password field in SQL?
        user.save()
        return user
