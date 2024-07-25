from __future__ import division, print_function, unicode_literals

import logging
from django.conf import settings
from django.utils.translation import ugettext as _
from django.utils.module_loading import import_string
from celery import shared_task
from feeds.constants import SHARED_WITH

from feeds.models import Comment, Post

check_org_email = import_string(settings.CHECK_ORG_EMAIL)
PendingEmail = import_string(settings.PENDING_EMAIL)
EMAIL_TYPE = import_string(settings.EMAIL_TYPE)
TEMPLATE_MODEL = import_string(settings.TEMPLATE_MODEL)
CustomUser = import_string(settings.CUSTOM_USER_MODEL)
EmployeeIDStore = import_string(settings.EMPLOYEE_ID_STORE)
NOTIFICATION_OBJECT = import_string(settings.POST_NOTIFICATION_OBJECT_TYPE)
NOTIFICATION_OBJECT_TYPE = NOTIFICATION_OBJECT.Posts


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
    from_user = check_org_email(comment.created_by.email, comment.created_by.organization)
    PendingEmail.objects.send_email(
        email=recipient.email,
        from_user=from_user,
        subject=subject,
        body=email_body,
        email_type=EMAIL_TYPE.html
    )


@shared_task(bind=True)
def notify_user_via_push_notification(self, poll_id, is_post=False):
    from feeds.utils import get_user_name, push_notification

    try:
        poll = Post.objects.get(id=poll_id)
    except Post.DoesNotExist:
        return
    creator = poll.created_by
    if not creator.is_staff:
        return
    accessible_users = []
    if poll.shared_with == SHARED_WITH.SELF_DEPARTMENT:
        departments = creator.departments.all()
        for dept in departments:
            accessible_users.extend(list(dept.users.all()))

    elif poll.shared_with == SHARED_WITH.ALL_DEPARTMENTS:
        accessible_users.extend(list(creator.organization.users.all()))

    elif poll.shared_with == SHARED_WITH.SELF_JOB_FAMILY:
        try:
            employee_id_store = EmployeeIDStore.objects.filter(
                user__is_active=True, job_family=creator.employee_id_store.job_family, signed_up=True)
            for emp_id_store in employee_id_store:
                if emp_id_store.user in accessible_users:
                    continue
                accessible_users.append(emp_id_store.user)
        except Exception:
            # User does not have any job family No need to send notification
            pass

    elif poll.shared_with == SHARED_WITH.ORGANIZATION_DEPARTMENTS:
        departments = poll.departments.all()
        organizations = poll.organizations.all()
        employee_ids_store = EmployeeIDStore.objects.filter(job_family__in=poll.job_families.all())
        for department in departments:
            accessible_users.extend(list(department.users.all()))

        for organization in organizations:
            accessible_users.extend(list(organization.users.all()))

        for employee_id_store in employee_ids_store:
            user = employee_id_store.user
            if user and employee_id_store.signed_up and user not in accessible_users:
                accessible_users.append(user)

    user_name = get_user_name(creator)
    message = _("'%s' created a new post." % user_name) if is_post else _("'%s' started a new poll." % user_name)
    object_type = NOTIFICATION_OBJECT_TYPE

    for usr in accessible_users:
        push_notification(creator, message, usr, object_type=object_type, object_id=poll_id,
                          extra_context={"redirect_screen": "Poll"})
