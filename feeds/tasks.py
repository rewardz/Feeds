from __future__ import division, print_function, unicode_literals

import logging
from django.conf import settings
from django.utils.translation import ugettext as _
from django.utils.module_loading import import_string
from celery import shared_task

from feeds.models import Comment
from feeds.utils import push_notification


check_org_email = import_string(settings.CHECK_ORG_EMAIL)
PendingEmail = import_string(settings.PENDING_EMAIL)
EMAIL_TYPE = import_string(settings.EMAIL_TYPE)
TEMPLATE_MODEL = import_string(settings.TEMPLATE_MODEL)
CustomUser = import_string(settings.CUSTOM_USER_MODEL)


logger = logging.getLogger(__name__)


@shared_task(bind=True)
def notify_user_via_email(self, comment_id):
    """
    This method will send the push notification and email to the user if staff has added the comment
    """
    comment = Comment.objects.get(id=comment_id)
    post = comment.post
    feedback_post = post.feedbackpost_set.first() if post else None
    feedback = feedback_post.feedback if feedback_post else None
    recipient = feedback.user if feedback else None
    organization = recipient.organization if recipient else None

    template = TEMPLATE_MODEL.get_feedback_new_comment_notification_template()

    if not template:
        logger.error({"error": [_('Template for Admin Feedback Comment not found')]})
        return

    subject = template.title.format(feedback_title=post.title[:20])
    email_body = template.body.format(
        org_image=organization.display_img_url if organization else "",
        org_name=organization.name if organization else "",
        user_name=comment.created_by.get_full_name(),
        admin_user_name=comment.created_by.get_full_name(),
        feedback_title=post.title[:80],
        new_comment=comment.content
    )
    from_user = check_org_email(comment.created_by.email)
    PendingEmail.objects.send_email(
        email=recipient.email,
        from_user=from_user,
        subject=subject,
        body=email_body,
        email_type=EMAIL_TYPE.html
    )


@shared_task(bind=True)
def notify_user_via_push_notification(self, creator_id, message, user_ids, object_type, poll_id, extra_context):
    creator = CustomUser.objects.get(id=creator_id)
    accessible_users = CustomUser.objects.filter(id__in=user_ids)
    for usr in accessible_users:
        push_notification(creator, message, usr, object_type=object_type, object_id=poll_id,
                          extra_context=extra_context)
