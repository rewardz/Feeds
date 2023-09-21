from __future__ import division, print_function, unicode_literals

import json
import re
from django.conf import settings
from django.db.models import Q
from django.utils.translation import ugettext as _
from django.utils.module_loading import import_string
from django.utils import timezone
from datetime import timedelta
import calendar

from rest_framework import exceptions, serializers

from .constants import POST_TYPE, SHARED_WITH
from .models import Comment, Post
from feeds.tasks import notify_user_via_email


DEPARTMENT_MODEL = import_string(settings.DEPARTMENT_MODEL)
ERROR_MESSAGE = "Priority post already exists for user. Set priority to false."
USERMODEL = import_string(settings.CUSTOM_USER_MODEL)
PENDING_EMAIL_MODEL = import_string(settings.PENDING_EMAIL)
PUSH_NOTIFICATION_MODEL = import_string(settings.PUSH_NOTIFICATION)
NOTIFICATION_OBJECT = import_string(settings.POST_NOTIFICATION_OBJECT_TYPE)
NOTIFICATION_OBJECT_TYPE = NOTIFICATION_OBJECT.Posts
# NOTIFICATION_FEEDBACK_OBJECT_TYPE = NOTIFICATION_OBJECT.feedback
NOTIF_OBJECT_TYPE_FIELD_NAME = settings.NOTIF_OBJECT_TYPE_FIELD_NAME
NOTIF_OBJECT_ID_FIELD_NAME = settings.NOTIF_OBJECT_ID_FIELD_NAME
USER_DEPARTMENT_RELATED_NAME = settings.USER_DEPARTMENT_RELATED_NAME
ORGANIZATION_SETTINGS_MODEL = import_string(settings.ORGANIZATION_SETTINGS_MODEL)
NOMINATION_STATUS = import_string(settings.NOMINATION_STATUS)
UserJobFamily = import_string(settings.USER_JOB_FAMILY)


def accessible_posts_by_user(user, organization, allow_feedback=False, appreciations=False, post_id=None):
    if not isinstance(organization, (list, tuple)):
        organization = [organization]

    # get the departments to which this user belongs
    user_depts = getattr(user, USER_DEPARTMENT_RELATED_NAME).all()
    query = Q(mark_delete=False) & (
            Q(organizations__in=organization) | Q(departments__in=user_depts)
        ) | Q(mark_delete=False, created_by=user)

    if appreciations:
        query.add(Q(post_type=POST_TYPE.USER_CREATED_APPRECIATION,
                    created_by__organization__in=user.get_affiliated_orgs(), mark_delete=False), Q.OR)

    # get the post belongs to organization
    result = Post.objects.filter(query)

    # filter / exclude feedback based on the allow_feedback
    if not allow_feedback:
        result = result.exclude(post_type=POST_TYPE.FEEDBACK_POST)
    else:
        result = result.filter(post_type=POST_TYPE.FEEDBACK_POST)

    # possible that result might contains duplicate posts due to OR query
    # we can not apply distinct over here since order by is used at some places
    # after calling this method
    if not user.is_staff:
        return result
    post_ids = list(set(result.values_list("id", flat=True)))

    # If the post is shared with self department and admin's department is another than creators department
    # then post org will be None so we hahve to allow that post to admin
    posts = Post.objects.filter(
        organizations=None, shared_with=SHARED_WITH.SELF_DEPARTMENT,
        created_by__organization=user.organization
    ).exclude(id__in=post_ids).values_list("id", flat=True)
    if posts:
        post_ids.extend(list(posts))

    if post_id:

        # Added this condition because we are allowing admin to see the post if that post does not belongs
        # to his department then admin can access that post
        orgs = user.get_affiliated_orgs().values_list("id", flat=True) if allow_feedback else [user.organization_id]
        if (
                post_id not in post_ids
                and Post.objects.filter(id=post_id, created_by__organization_id__in=orgs).exists()
        ):
            post_ids.append(post_id)

    return Post.objects.filter(id__in=post_ids)


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
        if hasattr(instance, "post_type") and instance.post_type in [POST_TYPE.SYSTEM_CREATED_POST]:
            return False
        return instance.created_by.id == user.id
    return True


def tag_users_to_post(post, user_list):
    existing_tagged_users = [u.id for u in post.tagged_users.all()]
    remove_user_list = list(set(existing_tagged_users).difference(user_list))
    new_users_tagged = list(set(user_list).difference(existing_tagged_users))
    object_type = NOTIFICATION_OBJECT_TYPE
    created_by_user_name = get_user_name(post.created_by)
    if new_users_tagged:
        for user_id in new_users_tagged:
            try:
                user = USERMODEL.objects.get(id=user_id)
                post.tag_user(user)
                message = _("'%s' has mentioned you in post" % (created_by_user_name))
                if post.post_type == POST_TYPE.USER_CREATED_APPRECIATION:
                    message = _("'%s' has mentioned you in appreciation" % (created_by_user_name))
                if post.post_type == POST_TYPE.USER_CREATED_NOMINATION:
                    message = _("'%s' has mentioned you in nomination" % (created_by_user_name))
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
    if new_users_tagged:
        for user_id in new_users_tagged:
            try:
                user = USERMODEL.objects.get(id=user_id)
                comment.tag_user(user)
                message = _("'%s' has mentioned you in comment" % (created_by_user_name))
                push_notification(comment.created_by, message, user,
                                  object_type=object_type, object_id=comment.post_id)
            except Exception:
                continue
    if remove_user_list:
        for user_id in remove_user_list:
            try:
                user = USERMODEL.objects.get(id=user_id)
                comment.untag_user(user)
            except Exception:
                continue


def notify_new_comment(comment, creator):
    post = comment.post
    commentator_ids = Comment.objects.filter(post=post).values_list('created_by__id', flat=True)
    # get all the commentators except the one currently commenting
    commentators = USERMODEL.objects.filter(id__in=commentator_ids).exclude(id=creator.id)
    # also exclude the creator of the post
    commentators = commentators.exclude(id=post.created_by.id)
    feedback_post_type = post.post_type == POST_TYPE.FEEDBACK_POST
    object_type = NOTIFICATION_OBJECT.feedback if feedback_post_type else NOTIFICATION_OBJECT.Posts
    comment_creator_string = get_user_name(creator)
    post_creator = USERMODEL.objects.get(id=post.created_by.id)

    # for feedback post user won't receive the notification
    if not feedback_post_type:
        for usr in commentators:
            message = _("'%s' commented on the post" % (comment_creator_string))
            push_notification(
                creator, message, usr, object_type=object_type, object_id=post.id
            )

        # post creator always receives a notification when a new comment is made
        try:
            message = _("'%s' commented on your post" % (comment_creator_string))
            push_notification(
                creator, message, post_creator, object_type=object_type, object_id=post.id
            )
        except Exception:
            pass

    # if post type is feedback post and admin has commented then notify user
    if feedback_post_type and creator.is_staff:
        # object_type = NOTIFICATION_FEEDBACK_OBJECT_TYPE
        message = _("'%s' commented on the feedback" % (comment_creator_string))
        push_notification(
            creator, message, post_creator, object_type=object_type, object_id=post.id,
            extra_context={"reaction_type": 8}  # TODO: move to reaction types
        )
        notify_user_via_email.delay(comment.id)


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
        push_notification(creator, message, usr, object_type=object_type, object_id=poll.id,
        extra_context={"redirect_screen": "Poll"})


def notify_flagged_post(post, user, reason):
    admin_users = USERMODEL.objects.filter(
        organization=user.organization, is_staff=True
    )
    user_name = get_user_name(user)
    message = _("'%s' has reported the post" % (user_name))
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


def push_notification(sender, message, recipient, object_type=None, object_id=None, extra_context={}):
    try:
        notification = PUSH_NOTIFICATION_MODEL.objects.create(
            sender=sender,
            message=message,
            recipient=recipient,
            extra_context=extra_context,
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


def get_date_range(days):
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    return [start_date, end_date]


def since_last_appreciation(last_appreciation_date):
    current_date = timezone.now()
    return (current_date - last_appreciation_date).days


def get_current_month_end_date():
    current_date = timezone.now()
    days = calendar.monthrange(current_date.year, current_date.month)[1]
    return "{} {}, {}".format(current_date.strftime("%B"), days, current_date.year)


def get_absolute_url(uri):
    if "://" in uri:
        return uri
    else:
        site_url = settings.SITE_URL.strip("/")
        uri = uri.lstrip("/")
        return "/".join([site_url, uri])


def posts_not_shared_with_self_department(posts, user):
    """
    Returns filtered (posts which are not shared with requested users department) queryset of Post
    if user is superuser then empty QS (no need to exclude anything)
    posts: QuerySet[Post]
    user: CustomUser
    """
    if user.is_staff:
        return Post.objects.none()

    return posts.filter(
        Q(shared_with=SHARED_WITH.SELF_DEPARTMENT) & ~Q(created_by__departments__in=user.departments.all()) &
        ~Q(user=user) & ~Q(cc_users__in=[user])
    )


def posts_not_shared_with_job_family(posts, user):
    """
    Returns the posts to exclude which is shared with my job family
    Case if I am admin then i can see the post
    posts: QuerySet[Post]
    user: CustomUser
    """
    try:
        if user.is_staff:
            return Post.objects.none()

        return posts.filter(
            Q(shared_with=SHARED_WITH.SELF_JOB_FAMILY) &
            ~Q(created_by__employee_id_store__job_family=user.employee_id_store.job_family)
        )
    except AttributeError:
        return posts.filter(Q(shared_with=SHARED_WITH.SELF_JOB_FAMILY))


def admin_feeds_to_exclude(posts, user):
    """
    Returns filtered (posts which are shared with admin) queryset to exclude
    if user is superuser then empty QS (no need to exclude anything)
    if user is neither creator of post nor in cc posts to exclude
    posts: QuerySet[Post]
    user: CustomUser
    """
    if user.is_staff:
        return Post.objects.none()
    posts = posts.filter(shared_with=SHARED_WITH.ADMIN_ONLY)
    query = Q(shared_with=SHARED_WITH.ADMIN_ONLY)
    query.add(~Q(created_by=user) & ~Q(cc_users__in=[user.id]) & ~Q(user=user), query.connector)
    return posts.filter(query)


def shared_with_all_departments_but_not_belongs_to_user_org(posts, user):
    """
    Returns filtered (posts which are shared with all departments but created by user's org
    user is superuser then empty QS (no need to exclude anything)
    does not match with user's org ) queryset to exclude
    posts: QuerySet[Post]
    user: CustomUser
    """
    if user.is_staff:
        return Post.objects.none()

    query = Q(shared_with=SHARED_WITH.ALL_DEPARTMENTS)
    query.add(~Q(created_by__organization=user.organization) &
              ~Q(created_by=user) & ~Q(user=user) & ~Q(cc_users__in=[user.id]), query.connector)
    return posts.filter(query)


def assigned_nomination_post_ids(user):
    """
    Return List of post ids of nomination which assigned to reviewer
    """
    assigned_nomination_post_ids =  Post.objects.filter(
        Q(nomination__assigned_reviewer=user) | Q(nomination__alternate_reviewer=user)
    ).exclude(post_type=POST_TYPE.USER_CREATED_NOMINATION, 
              nomination__nom_status__in=[NOMINATION_STATUS.approved, NOMINATION_STATUS.rejected]
    ).values_list("id", flat=True)
    return assigned_nomination_post_ids


def posts_not_visible_to_user(posts, user, post_polls):
    """
    Returns List of post ids to exclude
    params: posts: QuerySet[Post]
    params: user: CustomUser
    """
    posts_ids_to_exclude = list(posts_not_shared_with_self_department(posts, user).values_list("id", flat=True))
    posts_ids_to_exclude.extend(list(admin_feeds_to_exclude(posts, user).values_list("id", flat=True)))
    if post_polls:
        posts_ids_to_exclude.extend(list(shared_with_all_departments_but_not_belongs_to_user_org(
            posts, user).values_list("id", flat=True)))

    posts_ids_not_to_exclude = assigned_nomination_post_ids(user) 
    posts_ids_to_exclude = list(set(posts_ids_to_exclude) - set(posts_ids_not_to_exclude))
    return posts_ids_to_exclude


def posts_shared_with_org_department(user, post_types, excluded_ids):
    """
    Return all posts which is shared with ORG departments
    and belongs to user's department or created by user
    params: user: CustomUser
    params: post_types: List[POST_TYPE]
    params: excluded_ids: List[id]
    """
    if user.is_staff:
        query = Q(shared_with=SHARED_WITH.ORGANIZATION_DEPARTMENTS, created_by__organization=user.organization)
    else:
        try:
            job_families = [user.employee_id_store.job_family]
        except AttributeError:
            job_families = []
        query = Q(created_by=user)
        query.add(Q(departments__in=[user.department]), Q.OR)
        query.add(Q(job_families__in=job_families), Q.OR)
        query.add(Q(shared_with=SHARED_WITH.ORGANIZATION_DEPARTMENTS, post_type__in=post_types), Q.AND)

    posts = Post.objects.filter(query)
    return posts.exclude(id__in=excluded_ids)


def validate_job_families(job_families, affiliated_orgs):
    """Returns active job families of the user's affiliated org"""
    job_families_qs = UserJobFamily.objects.filter(
        id__in=job_families, organization__in=affiliated_orgs, is_active=True)
    if job_families_qs.count() != len(job_families):
        raise serializers.ValidationError(
            "Invalid Job Family {}".format(
                list(set(job_families) - set(job_families_qs.values_list("id", flat=True)))
            ))

    return job_families_qs


def get_job_families(user, shared_with, data, is_str=True):
    """Returns Job families based on the data"""
    job_families = data.get('job_families', None)
    if job_families and shared_with and int(shared_with) == SHARED_WITH.ORGANIZATION_DEPARTMENTS:
        job_families = validate_job_families(json.loads(job_families) if is_str else job_families,
                                             user.get_affiliated_orgs())
    else:
        job_families = None
    return job_families
