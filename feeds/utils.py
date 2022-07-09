from __future__ import division, print_function, unicode_literals

import re

from django.conf import settings
from django.db.models import Q
from django.utils.translation import ugettext as _
from django.utils.module_loading import import_string


from rest_framework import exceptions

from .constants import POST_TYPE, SHARED_WITH
from .models import Comment, Post

DEPARTMENT_MODEL = import_string(settings.DEPARTMENT_MODEL)
ERROR_MESSAGE = "Priority post already exists for user. Set priority to false."
USERMODEL = import_string(settings.CUSTOM_USER_MODEL)
PENDING_EMAIL_MODEL = import_string(settings.PENDING_EMAIL)
PUSH_NOTIFICATION_MODEL = import_string(settings.PUSH_NOTIFICATION)
NOTIFICATION_OBJECT_TYPE = import_string(settings.POST_NOTIFICATION_OBJECT_TYPE).Posts
NOTIF_OBJECT_TYPE_FIELD_NAME = settings.NOTIF_OBJECT_TYPE_FIELD_NAME
NOTIF_OBJECT_ID_FIELD_NAME = settings.NOTIF_OBJECT_ID_FIELD_NAME


def accessible_posts_by_user(user, organization):
    if user.is_staff:
        result = Post.objects.filter(organization=organization)
        result = result.filter(mark_delete=False)
        result = result.exclude(post_type=POST_TYPE.FEEDBACK_POST)
        return result
    dept_users = []
    for dept in DEPARTMENT_MODEL.objects.filter(users=user):
        for usr in dept.users.all():
            dept_users.append(usr.id)
    if not dept_users:
        # If user does not belong to any department just show posts created by him
        result = Post.objects.filter(Q(organization=organization,
                                       created_by=user))
    else:
        result = Post.objects.filter(Q(organization=organization, \
                                    shared_with=SHARED_WITH.ALL_DEPARTMENTS) |\
                                 Q(created_by__in=dept_users))
    result = result.filter(mark_delete=False)
    result = result.exclude(post_type=POST_TYPE.FEEDBACK_POST)
    return result


def validate_priority(data):
    """
    This function checks if there are no other post accessible to the user which
    has priority set to True.
    At a single time only one post can be set as priority
    """
    user = data.get('created_by', None)
    organization = data.get('organization', None)
    priority = data.get('priority', None)
    if priority:
        accessible_posts = accessible_posts_by_user(user, organization)
        priority_posts = accessible_posts.filter(priority=True)
        if priority_posts:
            raise exceptions.ValidationError({"priority": _(ERROR_MESSAGE)})


def get_departments(user):
    """
    This function returns the department list of a user
    """
    return DEPARTMENT_MODEL.objects.filter(users=user)


def get_profile_image(user):
    """
    This function returns the profile image of the user or none
    """
    profile_image = settings.PROFILE_IMAGE_PROPERTY
    return getattr(user, profile_image, settings.NO_PROFILE_IMAGE)


def get_user_name(user):
    """
    This function returns the user name as "first_name" + "last_name"
    if first_name exists else returns the user email
    """
    first_name = settings.PROFILE_FIRST_NAME
    last_name = settings.PROFILE_LAST_NAME
    fname = getattr(user, first_name, None)
    lname = getattr(user, last_name, None)
    if not fname:
        return user.email
    else:
        return fname + " " + lname if lname else fname


def user_can_edit(user, instance):
    if instance.post_type == POST_TYPE.USER_CREATED_POLL:
        return False
    if not user.is_staff:
        if instance.post_type == POST_TYPE.SYSTEM_CREATED_POST:
            return False
        return instance.created_by.id == user.id
    return True


def user_can_delete(user, instance):
    if not user.is_staff:
        if instance.post_type in [POST_TYPE.SYSTEM_CREATED_POST]:
            return False
        return instance.created_by.id == user.id
    return True


def tag_users_to_post(post, user_list):
    existing_tagged_users = [u.id for u in post.tagged_users.all()]
    remove_user_list = list(set(existing_tagged_users).difference(user_list))
    new_users_tagged = list(set(user_list).difference(existing_tagged_users))
    object_type = NOTIFICATION_OBJECT_TYPE
    created_by_user_name = get_user_name(post.created_by)
    post_str = post.title[:20] + "..." if post.title else ""
    if new_users_tagged:
        for user_id in new_users_tagged:
            try:
                user = USERMODEL.objects.get(id=user_id)
                post.tag_user(user)
                message = _("'%s' has mentioned you in post '%s'" % (created_by_user_name, post_str))
                push_notification(post.created_by, message, user,
                                  object_type=object_type, object_id=post.id)
            except Exception:
                continue
    if remove_user_list:
        for user_id in remove_user_list:
            try:
                user = USERMODEL.objects.get(id=user_id)
                post.untag_user(user)
            except Exception:
                continue


def tag_users_to_comment(comment, user_list):
    existing_tagged_users = [u.id for u in comment.tagged_users.all()]
    remove_user_list = list(set(existing_tagged_users).difference(user_list))
    new_users_tagged = list(set(user_list).difference(existing_tagged_users))
    object_type = NOTIFICATION_OBJECT_TYPE
    created_by_user_name = get_user_name(comment.created_by)
    comment_str = comment.content[:20] + "..." if comment.content else ""
    if new_users_tagged:
        for user_id in new_users_tagged:
            try:
                user = USERMODEL.objects.get(id=user_id)
                comment.tag_user(user)
                message = _("'%s' has mentioned you in comment '%s'" % (created_by_user_name, comment_str))
                push_notification(comment.created_by, message, user,
                                  object_type=object_type, object_id=comment.id)
            except Exception:
                continue
    if remove_user_list:
        for user_id in remove_user_list:
            try:
                user = USERMODEL.objects.get(id=user_id)
                comment.untag_user(user)
            except Exception:
                continue


def notify_new_comment(post, creator):
    commentator_ids = Comment.objects.filter(post=post).values_list('created_by__id', flat=True)
    # get all the commentators except the one currently commenting
    commentators = USERMODEL.objects.filter(id__in=commentator_ids).exclude(id=creator.id)
    # also exclude the creator of the post
    commentators = commentators.exclude(id=post.created_by.id)
    object_type = NOTIFICATION_OBJECT_TYPE

    comment_creator_string = get_user_name(creator)
    post_string = post.title[:20] + "..." if post.title else ""

    for usr in commentators:
        message = _("'%s' commented on the post '%s'" % (comment_creator_string, post_string))
        push_notification(
            creator, message, usr, object_type=object_type, object_id=post.id
        )

    # post creator always receives a notification when a new comment is made
    try:
        post_creator = USERMODEL.objects.get(id=post.created_by.id)
        message = _("'%s' commented on your post '%s'" % (comment_creator_string, post_string))
        push_notification(
            creator, message, post_creator, object_type=object_type, object_id=post.id
        )
    except Exception:
        pass


def notify_new_poll_created(poll):
    creator = poll.created_by
    accessible_users = []
    if poll.shared_with == SHARED_WITH.SELF_DEPARTMENT:
        for dept in DEPARTMENT_MODEL.objects.filter(users=creator):
            for usr in dept.users.all():
                accessible_users.append(usr)
    elif poll.shared_with == SHARED_WITH.ALL_DEPARTMENTS:
        for usr in USERMODEL.objects.filter(organization=creator.organization):
            accessible_users.append(usr)
    user_name = get_user_name(creator)
    message = _("'%s' started a new poll." % user_name)
    object_type = NOTIFICATION_OBJECT_TYPE
    for usr in accessible_users:
        push_notification(creator, message, usr, object_type=object_type, object_id=poll.id)


def notify_flagged_post(post, user, reason):
    admin_users = USERMODEL.objects.filter(
        organization=user.organization, is_staff=True
    )
    user_name = get_user_name(user)
    post_string = post.title[:20] if post.title else ""
    message = _("'%s' has reported the post '%s'" % (user_name, post_string))
    subject = _("Inappropriate post")
    body = _(
        "User has marked the post in-appropriate due to the following reason"
        + "\n" + str(reason)
    )
    object_type = NOTIFICATION_OBJECT_TYPE
    for usr in admin_users:
        push_notification(user, message, usr, object_type=object_type, object_id=post.id)
        add_email(usr.email, user.email, subject, body)


def add_email(to, from_user, subject, body):
    try:
        PENDING_EMAIL_MODEL.objects.create(
            to = to,
            from_user = from_user,
            subject = subject,
            body = body
        )
        return True
    except Exception:
        return False


def push_notification(sender, message, recipient, object_type=None, object_id=None):
    try:
        notification = PUSH_NOTIFICATION_MODEL.objects.create(
            sender=sender,
            message=message,
            recipient=recipient,
        )
        if object_type:
            setattr(notification, NOTIF_OBJECT_TYPE_FIELD_NAME, object_type)
        if object_id:
            setattr(notification, NOTIF_OBJECT_ID_FIELD_NAME, object_id)
        notification.save()
        return True
    except Exception:
        return False


def extract_tagged_users(match_string):
    pattern = "<tag.*?>(.*?)<\\/tag>"
    matches = []
    user_ids = []

    matches_found = re.findall(pattern, match_string)
    if matches_found:
        matches.extend(matches_found)

    if not matches:
        return user_ids

    for user_detail in matches:
        user_info = extract_user_info(user_detail)
        if not user_info:
            continue
        email = user_info['email_id']
        user_id = user_info['user_id']
        if not user_id:
            try:
                user = USERMODEL.objects.get(email=email)
                user_ids.append(user.id)
            except Exception:
                continue
        else:
            user_ids.append(user_id)
    return user_ids


def extract_user_info(user_detail):
    user_info = {}
    email_pattern = r"<email_id>(([\w.-]+)@([\w.-]+))</email_id>"
    email_detail = re.compile(email_pattern).search(user_detail)
    email_id = None
    if email_detail:
        email_id = email_detail.group(1)
    user_info['email_id'] = email_id

    user_id_pattern = r"<user_id>([0-9]+)</user_id>"
    user_id_detail = re.compile(user_id_pattern).search(user_detail)
    user_id = None
    if user_id_detail:
        user_id = user_id_detail.group(1)
    user_info['user_id'] = user_id
    return user_info
