from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import path, reverse
try:
    from django.contrib.gis.db.models import Model, FileField, CharField, ImageField, TextField, EmailField, URLField, ForeignKey, DateTimeField, PositiveIntegerField, JSONField, CASCADE, SET_NULL, Index
except:
    from django.db.models import Model, FileField, CharField, ImageField, TextField, EmailField, URLField, ForeignKey, DateTimeField, PositiveIntegerField, JSONField, CASCADE, SET_NULL, Index
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from schedule import models as schedule_models
import markdown


if settings.USE_LDAP:
    import ldap
    from ldap import modlist


class MetadataMixin(Model):
    metadata = JSONField(
        default=dict,
        editable=False
    )

    class Meta:
        abstract = True


class User(AbstractUser):
    homepage = URLField(blank=True)
    photo = ImageField(blank=True, upload_to="user_photos")
    title = CharField(blank=True, max_length=300)
    description = TextField(blank=True, max_length=1000)
    username = CharField(unique=True, null=True, max_length=40)
    email = EmailField(unique=True)    
    created_at = DateTimeField(auto_now_add=True, editable=False)
    modified_at = DateTimeField(auto_now=True, editable=False)
    created_by = ForeignKey("self", null=True, on_delete=SET_NULL, editable=False)
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

    def is_object(self):
        return isinstance(self.id, int)

    @classmethod
    def is_model(self):
        return True
    
    @classmethod
    def model_title_name(cls):
        return cls._meta.verbose_name.title().replace(" ", "")

    def get_absolute_url(self):
        return reverse("api:{}-detail".format(self._meta.model_name), args=(self.id,))

    def get_permissions_url(self):
        return reverse("permissions", args=(self._meta.app_label, self._meta.model_name, self.id))

    @classmethod
    def get_list_url(self):
        return reverse("api:{}-list".format(self._meta.model_name))

    @classmethod
    def get_add_perm(self):
        return "add_{}".format(self._meta.model_name)

    @classmethod
    def get_delete_perm(self):
        return "delete_{}".format(self._meta.model_name)

    @classmethod
    def get_change_perm(self):
        return "change_{}".format(self._meta.model_name)    

    @classmethod
    def get_view_perm(self):
        return "view_{}".format(self._meta.model_name)    

    @classmethod
    def model_title(self):
        return self._meta.verbose_name_plural.title()

    @classmethod
    def model_class(self):
        return "{}-{}".format(self._meta.app_label, self._meta.model_name)

    @property
    def object_class(self):
        return "{}-{}-{}".format(self._meta.app_label, self._meta.model_name, self.id)

        
class CdhModel(MetadataMixin, Model):
    name = CharField(max_length=2000, null=False)
    created_by = ForeignKey(User, null=True, on_delete=SET_NULL, editable=False)
    created_at = DateTimeField(auto_now_add=True, editable=False)
    modified_at = DateTimeField(auto_now=True, editable=False)

    class Meta:
        abstract = True
        
    def is_object(self):
        return isinstance(self.id, int)

    @classmethod
    def is_model(self):
        return True
    
    def __str__(self):
        return self.name    

    @classmethod
    def model_title_name(cls):
        return cls._meta.verbose_name.title().replace(" ", "")

    def get_absolute_url(self):
        return reverse("api:{}-detail".format(self._meta.model_name), args=(self.id,))

    def get_permissions_url(self):
        return reverse("permissions", args=(self._meta.app_label, self._meta.model_name, self.id))

    @classmethod
    def get_list_url(self):
        return reverse("api:{}-list".format(self._meta.model_name))

    @classmethod
    def get_add_perm(self):
        return "add_{}".format(self._meta.model_name)

    @classmethod
    def get_delete_perm(self):
        return "delete_{}".format(self._meta.model_name)

    @classmethod
    def get_change_perm(self):
        return "change_{}".format(self._meta.model_name)    

    @classmethod
    def get_view_perm(self):
        return "view_{}".format(self._meta.model_name)    

    @classmethod
    def model_title_singular(self):
        return self._meta.verbose_name.title()

    def model_title_plural(self):
        return self._meta.verbose_name_plural.title()

    @classmethod
    def model_class(self):
        return "{}-{}".format(self._meta.app_label, self._meta.model_name)

    @property
    def object_class(self):
        return "{}-{}-{}".format(self._meta.app_label, self._meta.model_name, self.id)

    
class AsyncMixin(Model):
    PROCESSING = "PR"
    ERROR = "ER"
    COMPLETE = "CO"
    STATE_CHOICES = [
        (PROCESSING, "processing"),
        (ERROR, "error"),
        (COMPLETE, "complete")
    ]
    state = CharField(
        max_length=2,
        choices=STATE_CHOICES,
        default=PROCESSING,
        editable=False
    )
    message = TextField(null=True, editable=False)
    task_id = CharField(max_length=200, null=True, editable=False)
    
    class Meta:
        abstract = True

    
class Slide(CdhModel):
    article = TextField(blank=True, null=True)
    image = ImageField(blank=True, upload_to="slides")
    
    class Meta:
        verbose_name_plural = "Slides"


class Event(CdhModel, schedule_models.Event):
    pass


class Calendar(schedule_models.Calendar):
    created_by = ForeignKey(User, null=True, on_delete=SET_NULL, editable=False)
    created_at = DateTimeField(auto_now_add=True, editable=False)
    modified_at = DateTimeField(auto_now=True, editable=False)
        
    def is_object(self):
        return isinstance(self.id, int)

    @classmethod
    def is_model(self):
        return True
    
    def __str__(self):
        return self.name    

    @classmethod
    def model_title_name(cls):
        return cls._meta.verbose_name.title().replace(" ", "")

    def get_absolute_url(self):
        return reverse("api:{}-detail".format(self._meta.model_name), args=(self.id,))

    def get_permissions_url(self):
        return reverse("permissions", args=(self._meta.app_label, self._meta.model_name, self.id))

    @classmethod
    def get_list_url(self):
        return reverse("api:{}-list".format(self._meta.model_name))

    @classmethod
    def get_add_perm(self):
        return "add_{}".format(self._meta.model_name)

    @classmethod
    def get_delete_perm(self):
        return "delete_{}".format(self._meta.model_name)

    @classmethod
    def get_change_perm(self):
        return "change_{}".format(self._meta.model_name)    

    @classmethod
    def get_view_perm(self):
        return "view_{}".format(self._meta.model_name)    

    @classmethod
    def model_title_singular(self):
        return self._meta.verbose_name.title()

    def model_title_plural(self):
        return self._meta.verbose_name_plural.title()

    @classmethod
    def model_class(self):
        return "{}-{}".format(self._meta.app_label, self._meta.model_name)

    @property
    def object_class(self):
        return "{}-{}-{}".format(self._meta.app_label, self._meta.model_name, self.id)

        
class ResearchArtifact(CdhModel):
    ARTICLE = "article"
    BOOK = "book"
    BOOKLET = "booklet"
    CONFERENCE = "conference"
    INBOOK = "inbook"
    INCOLLECTION = "incollection"
    INPROCEEDINGS = "inproceedings"
    MANUAL = "manual"
    MASTERSTHESIS = "mastersthesis"
    MISC = "misc"
    PHDTHESIS = "phdthesis"
    PROCEEDINGS = "proceedings"
    TECHREPORT = "techreport"
    UNPUBLISHED = "unpublished"    
    TYPE_CHOICES = [
        (ARTICLE, "Article"),
        (BOOK, "Book"),
        (BOOKLET, "Booklet"),
        (CONFERENCE, "Conference"),
        (INBOOK, "Contribution to book"),
        (INCOLLECTION, "Contribution to collection"),
        (INPROCEEDINGS, "Contribution to conference or workshop"),
        (MANUAL, "Technical documentation"),
        (MASTERSTHESIS, "Masters thesis"),
        (MISC, "Miscellaneous"),
        (PHDTHESIS, "PhD thesis"),
        (PROCEEDINGS, "Conference or workshop proceedings"),
        (TECHREPORT, "Technical report"),
        (UNPUBLISHED, "Unpublished")
    ]    
    type = CharField(max_length=100, choices=TYPE_CHOICES, default=ARTICLE)
    title = CharField(max_length=1000, null=True)
    author = TextField(null=True)
    year = PositiveIntegerField(null=True)
    doi = CharField(max_length=1000, null=True)
    pages = CharField(max_length=1000, null=True)
    howpublished = CharField(max_length=1000, null=True)
    chapter = CharField(max_length=1000, null=True)
    organization = CharField(max_length=1000, null=True)
    booktitle = CharField(max_length=1000, null=True)
    school = CharField(max_length=1000, null=True)
    institution = CharField(max_length=1000, null=True)
    publisher = CharField(max_length=1000, null=True)
    address = CharField(max_length=1000, null=True)
    journal = CharField(max_length=1000, null=True)
    volume = CharField(max_length=1000, null=True)
    number = CharField(max_length=1000, null=True)
    series = CharField(max_length=1000, null=True)
    month = CharField(max_length=1000, null=True)
    note = CharField(max_length=1000, null=True)
    key = CharField(max_length=1000, null=True)
    editor = CharField(max_length=1000, null=True)
    edition = CharField(max_length=1000, null=True)
    biburl = URLField(max_length=1000, null=True)
    slides = FileField(upload_to="research/slides", null=True)
    document = FileField(upload_to="research/documents", null=True)
    appendix = FileField(upload_to="research/appendices", null=True)
    image = ImageField(upload_to="research/images", null=True)
    description = TextField(blank=True, null=True)

    class Meta:
        ordering = ["-year", "-month"]
        

class Documentation(CdhModel):
    content = TextField(blank=True, null=True)
    view_name = CharField(null=True, max_length=200, editable=False)
    content_type = ForeignKey(ContentType, on_delete=CASCADE, null=True, blank=True, editable=False)
    object_id = PositiveIntegerField(null=True, blank=True, editable=False)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    class Meta:
        indexes = [
            Index(fields=["content_type", "object_id"]),
        ]

    def render(self):
        return markdown.markdown(self.content)
