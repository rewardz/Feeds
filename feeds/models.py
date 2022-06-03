import logging

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Sum
from django.utils import timezone
from django.utils.module_loading import import_string
from django.utils.translation import ugettext as _

from rest_framework.exceptions import ValidationError

from cropimg.fields import CIImageField, CIThumbnailField
from easy_thumbnails.exceptions import InvalidImageFormatError
from easy_thumbnails.files import get_thumbnailer
from model_helpers import upload_to
from taggit.managers import TaggableManager

from .constants import POST_TYPE, SHARED_WITH

logger = logging.getLogger(__name__)

CustomUser = settings.AUTH_USER_MODEL
Organization = import_string(settings.ORGANIZATION_MODEL)
Department = import_string(settings.DEPARTMENT_MODEL)


def post_upload_to_path(instance, filename):
    now = timezone.now()
    fmt = '%Y/%m/%d'
    dc = now.strftime(fmt)
    inst_verbose = instance._meta.verbose_name
    inst_id = str(instance.post.pk)
    return 'post/{inst_name}/{dc}/{id}/{name}'.format(
        inst_name=inst_verbose, dc=dc, id=inst_id, name=filename
    )


class UserInfo(models.Model):
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class Post(UserInfo):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    title = models.CharField(max_length=200, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    published_date = models.DateTimeField(blank=True, null=True)
    priority = models.BooleanField(default=False)
    prior_till = models.DateTimeField(blank=True, null=True)
    shared_with = models.SmallIntegerField(
        choices=SHARED_WITH(),
        default=SHARED_WITH.SELF_DEPARTMENT
    )
    post_type = models.SmallIntegerField(
        choices=POST_TYPE(),
        default=POST_TYPE.USER_CREATED_POST
    )
    active_days = models.SmallIntegerField(
        default=1, validators=[MinValueValidator(1), MaxValueValidator(30)]
    )
    departments = models.ManyToManyField(Department, related_name="posts")
    modified_by = models.ForeignKey(CustomUser, related_name="post_modifier", null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True, blank=True)
    mark_delete = models.BooleanField(default=False)
    tagged_users = models.ManyToManyField(
        CustomUser, related_name="tagged_users",
        through="PostTaggedUsers", blank=True
    )
    tags = TaggableManager()

    @property
    def is_poll(self):
        return self.post_type == POST_TYPE.USER_CREATED_POLL

    @property
    def is_poll_active(self):
        if not self.is_poll:
            return False
        active_till = self.created_on + timezone.timedelta(days=self.active_days)
        return active_till > timezone.now()

    @property
    def poll_remaining_time(self):
        if not self.is_poll_active:
            return None
        active_till = self.created_on + timezone.timedelta(days=self.active_days)
        remaining_time = active_till - timezone.now()
        remaining_days = remaining_time.days
        remaining_time_sec = remaining_time.total_seconds()
        hours = remaining_time_sec // 3600
        hours = int(hours)
        if remaining_days >= 1:
            if remaining_days == 1:
                if hours > 24:
                    hours = hours - 24
                return "{days} day and {hours} hour(s)". \
                    format(days=remaining_days, hours=hours)
            return "{days} days".format(days=remaining_days)
        if hours > 1:
            return "{hours} hours".format(hours=hours)
        minutes = (remaining_time_sec % 3600) // 60
        return "{minutes} minutes".format(minutes=int(minutes))

    def user_has_voted(self, user):
        if not self.is_poll:
            return False
        return Voter.objects.filter(user=user, question=self).exists()

    def vote(self, user, answer_id):
        if not self.is_poll_active:
            raise ValidationError(_('Sorry! the poll is no longer active.'))
        answer = PollsAnswer.objects.get(pk=answer_id, question=self)
        if self.user_has_voted(user):
            raise ValidationError(_('You have already voted for this question'))
        Voter.objects.create(answer=answer, user=user, question=self)
        answer.votes = answer.votes + 1
        answer.save()

    def tag_user(self, user):
        PostTaggedUsers.objects.create(post=self, user=user)

    def untag_user(self, user):
        ptu = PostTaggedUsers.objects.filter(post=self, user=user)
        if ptu:
            for u in ptu:
                u.delete()

    def related_answers(self):
        return PollsAnswer.objects.filter(question=self)

    def total_votes(self):
        total_votes = None
        if self.is_poll:
            total_votes = self.related_answers().aggregate(
                total=Sum('votes')).get('total')
        return total_votes if total_votes else 0

    def mark_as_delete(self, user):
        try:
            self.mark_delete = True
            self.modified_by = user
            self.save()
        except Post.DoesNotExist:
            raise ValidationError(_("Post does not exist"))

    def pinned(self, user, prior_till=None):
        is_admin = user.is_staff
        if is_admin:
            earlier_pinned = Post.objects.filter(organization=user.organization, priority=True)
            if prior_till:
                try:
                    prior_till = int(prior_till)
                    prior_till = timezone.now() + timezone.timedelta(days=prior_till)
                except ValueError:
                    raise ValidationError(_("Improper prior till"))
            earlier_pinned.update(priority=False)
            self.priority = True
            self.prior_till = prior_till
            self.save()

    def __unicode__(self):
        return self.title if self.title else str(self.pk)

    class Meta:
        ordering = ("-pk",)


class Images(models.Model):
    IMAGE_SIZES = {
        "thumbnail": (150, 150),
        "display": (960, 720),
        "large": (1024, 2048)
    }
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    image = CIImageField(upload_to=post_upload_to_path, blank=True, null=True)
    img_large = CIThumbnailField('image', (1, 1), blank=True, null=True)
    img_display = CIThumbnailField('image', (1, 1), blank=True, null=True)
    img_thumbnail = CIThumbnailField('image', (1, 1), blank=True, null=True)

    def __init__(self, *args, **kwargs):
        for key in self.IMAGE_SIZES:
            field = self._meta.get_field('img_%s' % key)
            field.size = self.IMAGE_SIZES[key]
        super(Images, self).__init__(*args, **kwargs)

    def get_thumbnail(self, size_name, default_url=""):
        if not self.image:
            return default_url
        try:
            return get_thumbnailer(self.image).get_thumbnail({
                'size': self.IMAGE_SIZES[size_name],
                'ci_box': getattr(self, "img_%s" % size_name),
            }).url
        except InvalidImageFormatError as ex:
            logger.error("Error generating thumbnail for %s (pk=%d) :  %s", self, self.pk, ex)
            return default_url

    @property
    def thumbnail_img_url(self):
        try:
            thumbnail_img_url = self.get_thumbnail("thumbnail")
            return thumbnail_img_url
        except ValueError as ex:
            logger.error("Error generating thumbnail for %s (pk=%d) :  %s", self, self.pk, ex)
            return ""

    @property
    def display_img_url(self):
        try:
            display_img_url = self.get_thumbnail("display")
            return display_img_url
        except ValueError as ex:
            logger.error("Error generating display for %s (pk=%d) :  %s", self, self.pk, ex)
            return ""

    @property
    def large_img_url(self):
        try:
            large_img_url = self.get_thumbnail("large")
            return large_img_url
        except ValueError as ex:
            logger.error("Error generating display for %s (pk=%d) :  %s", self, self.pk, ex)
            return ""


class Videos(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    video = models.FileField(upload_to=post_upload_to_path)


class Documents(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    document = models.FileField(
        upload_to=post_upload_to_path, blank=True, null=True
    )


class Comment(UserInfo):
    content = models.TextField()
    parent = models.ForeignKey('self', blank=True, null=True, related_name="comment_response")
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    modified_by = models.ForeignKey(CustomUser, related_name="comment_modifier", null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True, blank=True)
    tagged_users = models.ManyToManyField(
        CustomUser, related_name="comment_tagged_users",
        through="CommentTaggedUsers", blank=True
    )

    def tag_user(self, user):
        CommentTaggedUsers.objects.create(comment=self, user=user)

    def untag_user(self, user):
        ctu = CommentTaggedUsers.objects.filter(comment=self, user=user)
        if ctu:
            for u in ctu:
                u.delete()

    def __unicode__(self):
        return "%s" % self.content


class PostLiked(UserInfo):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)

    def __unicode__(self):
        return "%s like post %s" % (self.created_by, self.post)


class CommentLiked(UserInfo):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)

    def __unicode__(self):
        return "%s like comment %s" % (self.created_by, self.comment)


class PollsAnswer(models.Model):
    question = models.ForeignKey(Post, on_delete=models.CASCADE)
    answer_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)
    voters = models.ManyToManyField(CustomUser, through='Voter', blank=True)

    @property
    def percentage(self):
        question = self.question
        total_votes = question.total_votes()
        if total_votes > 0:
            return int(round((self.votes * 100.0) / total_votes))

    @property
    def is_winner(self):
        question = self.question
        answers = PollsAnswer.objects.filter(question=question)
        max_vote = answers.order_by('-votes').first().votes if answers else 0
        answers = answers.filter(votes=max_vote)
        if answers.count() > 1:
            return False
        else:
            return self in answers

    def get_voters(self):
        # return ",".join([str(p) for p in self.voters.all()])
        return self.voters.all().values_list('id', flat=True)

    def __unicode__(self):
        return self.answer_text

    class Meta:
        ordering = ('pk',)


class Voter(models.Model):
    answer = models.ForeignKey(PollsAnswer)
    user = models.ForeignKey(CustomUser)
    question = models.ForeignKey(Post)
    date_voted = models.DateTimeField(auto_now_add=True)


class PostTaggedUsers(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    tagged_on = models.DateTimeField(auto_now_add=True)


class CommentTaggedUsers(models.Model):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    tagged_on = models.DateTimeField(auto_now_add=True)


class FlagPost(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    flagger = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    notes = models.TextField(verbose_name='reason')
    accepted = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)
    notified = models.BooleanField(default=True)
