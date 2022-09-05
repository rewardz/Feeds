from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.module_loading import import_string
from django.conf import settings

from feeds.models import Comment
from feeds.constants import POST_TYPE


FEEDBACK_STATUS_OPTIONS = import_string(settings.FEEDBACK_STATUS_OPTIONS)
SEND_NOTIFICATION_TO_USER = import_string(settings.SEND_NOTIFICATION_TO_USER)


@receiver(post_save, sender=Comment)
def update_feedback_for_first_staff_comment(sender, instance, created, **kwargs):
    """
    Method to update the feedback status to UNDER_REVIEW if first comment from staff user to the feedback post
    """
    post = instance.post
    is_feedback_post = instance.post.post_type == POST_TYPE.FEEDBACK_POST
    staff_comments = post.comment_set.exclude(id=instance.id).values_list('created_by__is_staff', flat=True)
    # new instance, should be staff user, post type should be feedback post
    if created and instance.created_by.is_staff and is_feedback_post:

        # if first staff comment then change the status
        if not staff_comments:
            feedback_post = post.feedbackpost_set.all().first()

            if feedback_post:
                feedback = feedback_post.feedback
                if feedback.status == FEEDBACK_STATUS_OPTIONS.SUBMITTED:
                    feedback.status = FEEDBACK_STATUS_OPTIONS.UNDER_REVIEW
                    feedback.save()
