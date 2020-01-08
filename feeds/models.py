from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.module_loading import import_string
from django.utils.translation import ugettext as _

from model_helpers import upload_to

from .constants import SHARED_WITH


CustomUser = settings.AUTH_USER_MODEL
Organization = import_string(settings.ORGANIZATION_MODEL)


class Post(models.Model):
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    published_date = models.DateTimeField(blank=True, null=True)
    priority = models.BooleanField(default=False)
    prior_till = models.DateTimeField(blank=True, null=True)
    shared_with = models.SmallIntegerField(
        choices=SHARED_WITH(),
        default=SHARED_WITH.SELF_DEPARTMENT
    )
    poll = models.BooleanField(default=False)

    def vote(self, user, answer_id):
        answer = PollsAnswer.objects.get(pk=answer_id)
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
        return "%s published by %s" % (self.title, self.created_by)
    
    class Meta:
        ordering = ("-pk",)


class Images(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    image = models.ImageField(upload_to="post/images")


class Videos(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    video = models.FileField(upload_to="post/videos")


class Comment(models.Model):
    content = models.TextField()
    parent = models.ForeignKey('self', blank=True, null=True, related_name="comment_response")
    commented_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    commented_on = models.DateTimeField(auto_now_add=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)

    def __unicode__(self):
        return "%s" % self.content


class Clap(models.Model):
    clapped_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    clapped_on = models.DateTimeField(auto_now_add=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)

    def __unicode__(self):
        return "%s clapped on %s" % (self.clapped_by, self.post)


class PostLiked(models.Model):
    liked_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    liked_on = models.DateTimeField(auto_now_add=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)

    def __unicode__(self):
        return "%s like post %s" % (self.liked_by, self.post)


class CommentLiked(models.Model):
    liked_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    liked_on = models.DateTimeField(auto_now_add=True)
    post = models.ForeignKey(Comment, on_delete=models.CASCADE)

    def __unicode__(self):
        return "%s like comment %s" % (self.liked_by, self.post)


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
