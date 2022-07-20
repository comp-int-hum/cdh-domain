from . import settings
#from cdh.admin import CDHModelAdmin, site
#from django.contrib import admin
from django.urls import path, reverse
from django.contrib.gis.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
from markdownfield.models import MarkdownField, RenderedMarkdownField
from markdownfield.validators import VALIDATOR_STANDARD
if settings.USE_LDAP:
    import ldap
    from ldap import modlist

class BaseModel(models.Model):
    class Meta:
        abstract = True


class AsyncMixin(models.Model):
    PROCESSING = "PR"
    ERROR = "ER"
    COMPLETE = "CO"
    STATE_CHOICES = [
        (PROCESSING, "processing"),
        (ERROR, "error"),
        (COMPLETE, "complete")
    ]
    state = models.CharField(
        max_length=2,
        choices=STATE_CHOICES,
        default=PROCESSING
    )
    message = models.TextField(null=True)
    task_id = models.CharField(max_length=200, null=True)
    class Meta:
        abstract = True


class MetadataMixin(models.Model):
    metadata = models.JSONField(
        default=dict
    )
    class Meta:
        abstract = True

        
    #def __init__(self, *argv, **argd):
    #    self.readonly_fields = ["state"]
    #    self.list_display = ("state")
    #    super(AsyncMixin, self).__init__(*argv, **argd)
    
    #@admin.display(description="Status")
    #def state_cell(self, model):
    #    print(dir(model))
    #    print(dir(model.state))
    #    return format_html(
    #        "<span class='{}'>{}</span>",
    #        model.state,
    #        model.get_state_display()
    #    )


class User(AbstractUser):
    homepage = models.URLField(blank=True)
    photo = models.ImageField(blank=True, upload_to="user_photos")
    title = models.CharField(blank=True, max_length=300)
    description = models.TextField(blank=True, max_length=1000)
    username = models.CharField(unique=True, null=True, max_length=40)
    email = models.EmailField(unique=True)
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["first_name", "last_name", "email"]
    def set_password(self, raw_password):
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
            dn = "uid={},ou=users,dc=cdh,dc=jhu,dc=edu".format(self.username)
            ld.passwd_s(dn, None, raw_password)
        else:
            super().set_password(raw_password)
    def __str__(self):
        return "{} {}".format(self.first_name, self.last_name) if self.last_name else self.username

    
class Slide(models.Model):
    class Meta:
        verbose_name_plural = "Slides"
    title = models.CharField(max_length=200, null=True)        
    article = MarkdownField(blank=True, rendered_field="rendered_article", validator=VALIDATOR_STANDARD)
    rendered_article = RenderedMarkdownField(null=True)
    image = models.ImageField(blank=True)
    active = models.BooleanField(default=False)
    def __str__(self):
        return self.title
    def get_absolute_url(self):
        return reverse("cdh:slide", args=(self.id,))


class SlidePage(models.Model):
    name = models.CharField(max_length=200, null=True)
    content = MarkdownField(blank=True, rendered_field="rendered_content", validator=VALIDATOR_STANDARD)
    rendered_content = RenderedMarkdownField(null=True)
    additional_link_prompt = models.CharField(max_length=2000, default="", null=True, blank=True)
    slides = models.ManyToManyField(Slide)
    def __str__(self):
        return self.name
    def get_absolute_url(self):
        return reverse("cdh:slide", args=(self.id,))
    
