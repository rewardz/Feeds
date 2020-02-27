import logging

from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.module_loading import import_string
from django.utils.translation import ugettext as _

from cropimg.fields import CIImageField, CIThumbnailField
from easy_thumbnails.exceptions import InvalidImageFormatError
from easy_thumbnails.files import get_thumbnailer
from model_helpers import upload_to

from .constants import POST_TYPE, SHARED_WITH

logger = logging.getLogger(__name__)

CustomUser = settings.AUTH_USER_MODEL
Organization = import_string(settings.ORGANIZATION_MODEL)


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

    def vote(self, user, answer_id):
        answer = PollsAnswer.objects.get(pk=answer_id, question=self)
        if Voter.objects.filter(user=user, question=self).exists():
            raise ValidationError(_('You have already voted for this question'))
        Voter.objects.create(answer=answer, user=user, question=self)
        answer.votes = answer.votes + 1
        answer.save()

    def related_answers(self):
        return PollsAnswer.objects.filter(question=self)

    def total_votes(self):
        total_votes = 0
        answers = self.related_answers()
        for answer in answers:
            total_votes += answer.vote
        return total_votes

    def __unicode__(self):
        return self.title if self.title else self.pk
    
    class Meta:
        ordering = ("-pk",)


class Images(models.Model):
    
    IMAGE_SIZES = {
        "thumbnail": (150, 150),
        "display": (800, 400),
        "large": (1024, 2048)
    }
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    image = CIImageField(upload_to="post/images", blank=True, null=True)
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
    video = models.FileField(upload_to="post/videos")


class Comment(UserInfo):
    content = models.TextField()
    parent = models.ForeignKey('self', blank=True, null=True, related_name="comment_response")
    post = models.ForeignKey(Post, on_delete=models.CASCADE)

    def __unicode__(self):
        return "%s" % self.content


class PostLiked(UserInfo):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)

    def __unicode__(self):
        return "%s like post %s" % (self.created_by, self.post)


class CommentLiked(UserInfo):
    post = models.ForeignKey(Comment, on_delete=models.CASCADE)

    def __unicode__(self):
        return "%s like comment %s" % (self.created_by, self.post)


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
            return (self.votes * 100) / total_votes

    def get_voters(self):
        # return ",".join([str(p) for p in self.voters.all()])
        return [str(p) for p in self.voters.all()]

    def __unicode__(self):
        return self.answer_text


class Voter(models.Model):
    answer = models.ForeignKey(PollsAnswer)
    user = models.ForeignKey(CustomUser)
    question = models.ForeignKey(Post)
    date_voted = models.DateTimeField(auto_now_add=True)
