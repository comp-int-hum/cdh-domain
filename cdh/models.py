from django.contrib.auth import get_user_model
from . import settings
from django.urls import path, reverse
from django.contrib.gis.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
from .fields import MarkdownField


if settings.USE_LDAP:
    import ldap
    from ldap import modlist


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
    

class MetadataMixin(models.Model):
    metadata = models.JSONField(
        default=dict
    )
    class Meta:
        abstract = True


class CdhModel(MetadataMixin, models.Model):
    name = models.CharField(max_length=2000, null=False)
    created_by = models.ForeignKey(get_user_model(), null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.name    
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

    
class Slide(CdhModel):
    class Meta:
        verbose_name_plural = "Slides"
    article = MarkdownField(blank=True, null=True)
    image = models.ImageField(blank=True)
    def get_absolute_url(self):
        return reverse("cdh:slide", args=(self.id,))


# class SlidePage(CdhModel):
#     content = MarkdownField(blank=True)
#     additional_link_prompt = models.CharField(max_length=2000, default="", null=True, blank=True)
#     slides = models.ManyToManyField(Slide)
#     def get_absolute_url(self):
#         return reverse("cdh:slidepage", args=(self.id,))


class ResearchArtifact(CdhModel):
    authors = models.ManyToManyField(User, related_name="authored_by")
    author_freetext = models.TextField()
    description = MarkdownField(blank=True, null=True)
    def get_absolute_url(self):
        return reverse("cdh:researchartifact", args=(self.id,))    
