from __future__ import division, print_function, unicode_literals

import logging

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _

from cropimg.fields import CIImageField, CIThumbnailField
from easy_thumbnails.exceptions import InvalidImageFormatError
from easy_thumbnails.files import get_thumbnailer
from model_helpers import upload_to

from.constants import NOTIFICATION_OBJECTS, NOTIFICATION_STATES, NOTIFICATION_STATUS


logger = logging.getLogger(__name__)


class Organization(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, db_index=False, blank=True)

    def __unicode__(self):
        return self.name


class CustomUserBase(AbstractBaseUser):

    email = models.EmailField(
        max_length=255, blank=False, null=False, unique=True)
    first_name = models.CharField(max_length=100, blank=True, default="")
    last_name = models.CharField(max_length=100, blank=True, default="")

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    date_of_birth = models.DateField(null=True, blank=True)
    wedding_date = models.DateField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_admin_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(
        _('superuser status'), default=False,
        help_text=_('Designates that this user has all permissions without '
                    'explicitly assigning them.'))

    class Meta:
        abstract = True

    def has_perm(self, perm, obj=None):
        """
        Returns True if the user has the specified permission. This method
        queries all available auth backends, but returns immediately if any
        backend returns True. Thus, a user who has permission from a single
        auth backend is assumed to have permission in general. If an object is
        provided, permissions for this specific object are checked.
        """
        # Active superusers have all permissions.
        if self.is_active and self.is_superuser:
            return True

        if self.is_staff and hasattr(obj, "organization_id") and perm:
            return self.organization_id == obj.organization_id

        return False

    def has_perms(self, perm_list, obj=None):
        """
        Returns True if the user has each of the specified permissions. If
        object is passed, it checks if the user has all required perms for this
        object.
        """
        for perm in perm_list:
            if not self.has_perm(perm, obj):
                return False
        return True

    def has_module_perms(self, *args, **kwargs):
        """
        Returns True if the user has any permissions in the given app label.
        Uses pretty much the same logic as has_perm, above.
        """
        # Active superusers have all permissions.
        if self.is_active and self.is_superuser:
            return True

        return False

    def get_username(self):
        return self.email

    def get_short_name(self):
        return self.first_name or self.email


class DefaultCustomUserQueryset(models.QuerySet):

    def delete(self):
        self.update(is_active=False)


class DefaultCustomUserManager(BaseUserManager):

    def get_queryset(self):
        users = DefaultCustomUserQueryset(self.model)
        return users.all()


class CustomUser(CustomUserBase):
    IMAGE_SIZES = {
        "display": (500, 500),
        "thumbnail": (150, 150)
    }

    organization = models.ForeignKey(Organization, related_name="users")
    employee_id = models.TextField(default="", editable=True, unique=True)
    is_p2p_staff = models.BooleanField(default=False, help_text="p2p staff is not limited by p2p_points_limit, but can "
                                       "recognize users in the same org only")
    img = models.ImageField(upload_to="user/images", blank=True, null=True)
    # img_large = CIThumbnailField('image', (1, 1), blank=True, null=True)
    # img_display = CIThumbnailField('image', (1, 1), blank=True, null=True)
    # img_thumbnail = CIThumbnailField('image', (1, 1), blank=True, null=True)

    objects = DefaultCustomUserManager()

    USERNAME_FIELD = 'email'

    def get_thumbnail(self, size_name, default_url=""):
        if not self.img:
            return default_url
        return get_thumbnailer(self.img).get_thumbnail({
            'size': self.IMAGE_SIZES[size_name],
            'crop': False, 'detail': True
        }).url

    @property
    def thumbnail_img_url(self):
        if self.img:
            return self.get_thumbnail("thumbnail")
        return settings.DEFAULT_PROFILE_PICTURE

    def get_departments(self):
        return ",".join([str(p) for p in self.departments.all()])

    def add_departments(self, department_list):
        # Takes a list of department name strings
        for dept in department_list:
            name = dept.strip().title()
            # pylint: disable=unused-variable
            department, created = Department.objects.get_or_create(
                organization=self.organization,
                slug=slugify(name),
                defaults={"name": name}
            )
            self.departments.add(department)

    @property
    def department(self):
        return self.departments.first()

    @property
    def full_name(self):
        return self.get_full_name()

    def get_full_name(self):
        return u" ".join((self.first_name, self.last_name)).strip() or self.email

    def send_welcome_email(self):
        pass

    def __unicode__(self):
        return self.email

    def delete(self, *args, **kwargs):
        self.is_active = False
        self.save()

    class Meta:
        verbose_name = "user"

    def save(self, *args, **kwargs):
        self.email = self.email.lower()
        if not self.employee_id:
            employee_id = self.email
            while True:
                q = CustomUser.objects.filter(employee_id=employee_id)
                if self.id:
                    q = q.exclude(pk=self.id)
                if not q.exists():
                    self.employee_id = employee_id
                    break
                else:
                    employee_id = "_" + employee_id
        super(CustomUser, self).save(*args, **kwargs)

    def set_password(self, raw_password):
        if raw_password != '':
            super(CustomUser, self).set_password(raw_password)
            # Record new password in the password history
            # The very first password will not be recorded though, Sudhanshu says its fine
            if self.pk:
                PasswordHistory.objects.add_password(self, raw_password)

    def using_default_password(self):
        """
        Default password is not recorded in PasswordHistory model, so if user has no entries in PasswordHistory
        then he must be using default password.
        """
        return not self.password_history.exists()


class Department(models.Model):
    """
    Make department codes selectable and stuff
    """
    organization = models.ForeignKey(Organization, related_name="departments")
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=200)
    users = models.ManyToManyField("CustomUser", related_name="departments", blank=True)

    def __unicode__(self):
        return "%s - %s" % (self.name, self.organization.name)

    class Meta:
        ordering = ("slug", "pk")
        unique_together = (
            ("organization", "slug"),
        )


class PasswordHistoryQueryset(models.QuerySet):

    salt = "Pas_1Hist9"

    def make_password(self, password):
        return make_password(password, self.salt)

    def add_password(self, user, password):
        password = self.make_password(password)
        inst = PasswordHistory(user=user, password=password)
        # User should only have 3 entries in password history, delete any extra entries
        while user.password_history.count() >= 3:
            user.password_history.order_by("pk").first().delete()
        inst.save()

    def password_already_used(self, user_email, password):
        password = self.make_password(password)
        return self.filter(user__email=user_email, password=password).exists()


class PasswordHistory(models.Model):
    user = models.ForeignKey("profiles.CustomUser", related_name="password_history")
    password = models.CharField(max_length=100, blank=True, null=False)
    created = models.DateTimeField(auto_now_add=True)
    objects = PasswordHistoryQueryset.as_manager()

    def __unicode__(self):
        return "Password history for {0}".format(self.user)

    class Meta:
        verbose_name = "Password history entry"
        verbose_name_plural = "Password history entries"


class PendingEmail(models.Model):
    """
    This model keeps record of all the weekly mails sent.

    Status is set to pending by default
    Once email sending process is success then this record is deleted
    If email sending process failed then status is set to error
    """
    PENDING = 0
    ERROR = 1
    SENT = 3
    SPAM = 4
    BOUNCED = 5

    EMAIL_STATUS = (
        (PENDING, 'Pending'),
        (ERROR, 'Error'),
        (SENT, 'Sent'),
        (SPAM, 'Spam'),
        (BOUNCED, 'Bounced'),
    )
    EMAIL_TYPE = ("HTML", "Text")
    to = models.EmailField(verbose_name=_("Destination Email"), max_length=255)
    from_user = models.EmailField(verbose_name=_("Sender email"), max_length=255, blank=True, null=True)
    subject = models.CharField(verbose_name=_("Email Subject"), max_length=255)
    body = models.TextField(verbose_name=_("Email Body"))
    type = models.SmallIntegerField(verbose_name=_("type"), choices=list(enumerate(EMAIL_TYPE)), default=0, blank=True)
    status = models.PositiveSmallIntegerField(verbose_name=_("status"), choices=EMAIL_STATUS, default=PENDING, db_index=True)
    remarks = models.TextField(null=True, blank=True, verbose_name=_("remarks"))
    created = models.DateTimeField(auto_now_add=True, verbose_name=_("created"))

    class Meta:
        verbose_name = _("pending email")
        verbose_name_plural = _("pending emails")

    def __unicode__(self):
        return u"%s - %s" % (self.to, self.subject)


class PushNotification(models.Model):
    IMAGE_SIZES = {
        "thumbnail": (150, 150),
        "display": (320, 251)
    }

    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    message = models.TextField(
        blank=True, null=True, max_length=255,
        help_text="You have 255 characters left."
    )
    image = CIImageField(upload_to="notifications/", blank=True, null=True)

    recipient = models.ForeignKey(
        CustomUser, related_name="recipient",
        blank=True, null=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    object_type = models.SmallIntegerField(null=False, blank=True,
                                           default=NOTIFICATION_OBJECTS.Plain,
                                           choices=NOTIFICATION_OBJECTS())

    state = models.SmallIntegerField(null=False,
                                     default=NOTIFICATION_STATES.unread,
                                     choices=NOTIFICATION_STATES())
    status = models.SmallIntegerField(null=False,
                                      default=NOTIFICATION_STATUS.unsent,
                                      choices=NOTIFICATION_STATUS())

    is_read = models.BooleanField(default=False)
    url = models.URLField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return "{sender} - {recipient}".format(sender=self.sender,
                                               recipient=self.recipient)

    def save(self, *args, **kwargs):
        if not self.image:
            self.image = self.image
        super(PushNotification, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "PushNotification"
        ordering = ("-created", )


class UserStrength(models.Model):
    name = models.CharField(max_length=100, blank=False)
    slug = models.SlugField(blank=True, unique=True, null=True)
    icon = models.ImageField(upload_to="profiles/strength/icons")
    illustration = models.ImageField(upload_to="profiles/strength/illustrations", null=True, blank=True)
    background_color = models.CharField(max_length=20, null=True, blank=True)
    background_color_lite = models.CharField(max_length=20, null=True, blank=True)
    organization = models.ForeignKey(Organization, blank=True, null=True, on_delete=models.CASCADE)


class TrophyBadge(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.ImageField(upload_to='trophy_badges/')
    background_color = models.CharField(max_length=20, blank=True, null=True)
    background_color_lite = models.CharField(max_length=20, blank=True, null=True)
    points = models.DecimalField(blank=True, null=True, max_digits=12, decimal_places=2)
