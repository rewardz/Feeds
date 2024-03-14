from __future__ import division, print_function, unicode_literals

import datetime
import time
from json import loads
from django.conf import settings
from django.db import transaction
from django.db.models import Case, IntegerField, Q, Count, When
from django.http import Http404
from django.utils.module_loading import import_string
from django.utils.translation import ugettext as _

from rest_framework import permissions, viewsets, serializers, status, views, filters
from rest_framework.decorators import api_view, detail_route, list_route, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from feeds.constants import SHARED_WITH
from .filters import PostFilter, PostFilterBase
from .constants import POST_TYPE, SHARED_WITH
from .models import (
    Comment, Documents, ECard, ECardCategory,
    Post, PostLiked, PollsAnswer, Images, CommentLiked,
)
from .paginator import FeedsResultsSetPagination, FeedsCommentsSetPagination
from .permissions import IsOptionsOrAuthenticated
from .serializers import (
    CommentDetailSerializer, CommentSerializer, CommentCreateSerializer,
    DocumentsSerializer, ECardCategorySerializer, ECardSerializer,
    FlagPostSerializer, PostLikedSerializer, PostSerializer,
    PostDetailSerializer, PollsAnswerSerializer, ImagesSerializer,
    UserInfoSerializer, VideosSerializer, PostFeedSerializer, GreetingSerializer, OrganizationRecognitionSerializer
)
from .utils import (
    accessible_posts_by_user, extract_tagged_users, get_user_name, notify_new_comment,
    notify_new_post_poll_created, notify_flagged_post, push_notification, tag_users_to_comment,
    tag_users_to_post, user_can_delete, user_can_edit, get_date_range, since_last_appreciation,
    get_current_month_end_date, get_absolute_url, posts_not_visible_to_user,
    posts_shared_with_org_department, get_job_families, get_related_objects_qs,
)

CustomUser = import_string(settings.CUSTOM_USER_MODEL)
DEPARTMENT_MODEL = import_string(settings.DEPARTMENT_MODEL)
NOTIFICATION_OBJECT_TYPE = import_string(settings.POST_NOTIFICATION_OBJECT_TYPE).Posts
UserStrength = import_string(settings.USER_STRENGTH_MODEL)
NOMINATION_STATUS = import_string(settings.NOMINATION_STATUS)
ORGANIZATION_SETTINGS_MODEL = import_string(settings.ORGANIZATION_SETTINGS_MODEL)
MULTI_ORG_POST_ENABLE_FLAG = settings.MULTI_ORG_POST_ENABLE_FLAG
Organization = import_string(settings.ORGANIZATION_MODEL)
Transaction = import_string(settings.TRANSACTION_MODEL)
PointsTable = import_string(settings.POINTS_TABLE)
POINT_SOURCE = import_string(settings.POINT_SOURCE)
REPEATED_EVENT_TYPES = import_string(settings.REPEATED_EVENT_TYPES_CHOICE)

# InspireMe API wrapper
InspireMeAPI = import_string(settings.API_WRAPPER_CLASS)
InspireMe = InspireMeAPI()


def is_appreciation_post(post_id):
    """
    Returns True if post is user created appreciation
    """
    try:
        Post.objects.get(post_type=POST_TYPE.USER_CREATED_APPRECIATION, id=post_id)
        return True
    except Post.DoesNotExist:
        return False


class PostViewSet(viewsets.ModelViewSet):
    parser_classes = (MultiPartParser, JSONParser, FormParser,)
    permission_classes = (IsOptionsOrAuthenticated,)
    pagination_class = FeedsResultsSetPagination
    filter_backends = (filters.DjangoFilterBackend,)

    def _create_or_update(self, request, create=False):
        payload = request.data
        current_user = self.request.user
        if not current_user:
            raise serializers.ValidationError({'created_by': _('Created by is required!')})

        if not current_user.allow_user_post_feed:
            raise serializers.ValidationError(_('You are not allowed to create post.'))

        data = {}
        for key, value in payload.items():
            if key in ["organizations", "departments", "job_families"] and isinstance(payload.get(key), unicode):
                data.update({key: loads(value)})
                continue
            data.update({key: value})

        delete_image_ids = data.get('delete_image_ids', None)
        delete_document_ids = data.get('delete_document_ids', None)

        tag_users = []
        title_str = data.get('title', None)
        if title_str:
            title_tagged = extract_tagged_users(title_str)
            if title_tagged:
                tag_users.extend(title_tagged)

        description_str = data.get('description', None)
        if description_str:
            description_tagged = extract_tagged_users(description_str)
            if description_tagged:
                tag_users.extend(description_tagged)

        if tag_users:
            data['tag_users'] = tag_users

        if delete_image_ids:
            delete_image_ids = delete_image_ids.split(",")
            try:
                delete_image_ids = list(map(int, delete_image_ids))
            except ValueError:
                raise serializers.ValidationError(
                    _("Improper values submitted for delete image ids"))
            for img_id in delete_image_ids:
                try:
                    img = Images.objects.get(id=img_id)
                    img.delete()
                except Images.DoesNotExist:
                    continue

        if delete_document_ids:
            delete_document_ids = delete_document_ids.split(",")
            try:
                delete_document_ids = list(map(int, delete_document_ids))
            except ValueError:
                raise serializers.ValidationError(
                    _("Improper values submitted for delete document ids"))
            for doc_id in delete_document_ids:
                try:
                    doc = Documents.objects.get(id=doc_id)
                    doc.delete()
                except Documents.DoesNotExist:
                    continue

        if create:
            data['created_by'] = current_user.id
        data['modified_by'] = current_user.id

        # if feedback is not enabled then save current user organization
        if not ORGANIZATION_SETTINGS_MODEL.objects.get_value(MULTI_ORG_POST_ENABLE_FLAG, current_user.organization):
            data['organization'] = current_user.organization_id

        return data

    def _upload_files(self, request, post_id):
        images = dict((request.FILES).lists()).get('images', None)
        if images:
            for img in images:
                data = {'post': post_id}
                data['image'] = img
                image_serializer = ImagesSerializer(data=data)
                if image_serializer.is_valid():
                    image_serializer.save()
                else:
                    return Response({'message': 'Image not uploaded'},
                                    status=status.HTTP_400_BAD_REQUEST)

        documents = dict((request.FILES).lists()).get('documents', None)
        if documents:
            for doc in documents:
                data = {'post': post_id}
                data['document'] = doc
                document_serializer = DocumentsSerializer(data=data)
                if document_serializer.is_valid():
                    document_serializer.save()
                else:
                    return Response({'message': 'Document not uploaded'},
                                    status=status.HTTP_400_BAD_REQUEST)

        videos = dict((request.FILES).lists()).get('videos', None)
        if videos:
            for video in videos:
                data = {'post': post_id}
                data['video'] = video
                video_serializer = VideosSerializer(data=data)
                if video_serializer.is_valid():
                    video_serializer.save()
                else:
                    return Response({'message': 'Video not uploaded'},
                                    status=status.HTTP_400_BAD_REQUEST)

    def save_custom_tags(self, tags, organization):
        try:
            org_tags = organization.post_admin_tags.values_list("name", flat=True)

            for tag in tags:
                if tag not in org_tags:
                    organization.post_user_tags.add(tag)
        except Exception as e:
            raise e

    def create(self, request, *args, **kwargs):
        data = self._create_or_update(request, create=True)
        tag_users = data.get('tag_users', None)
        tags = data.get('tags', None)
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        post_id = instance.id
        if tag_users:
            tag_users_to_post(instance, tag_users)

        if tags:
            tags = list(tags.split(","))
            self.save_custom_tags(tags, request.user.organization)
            instance.tags.set(*tags)

        if request.FILES:
            self._upload_files(request, post_id)

        notify_new_post_poll_created(instance, True)
        return Response(serializer.data)

    def update(self, request, pk=None):
        instance = self.get_object()
        user = request.user
        if not user_can_edit(user, instance):
            raise serializers.ValidationError(_("You do not have permission to edit"))
        data = self._create_or_update(request)
        tag_users = data.get('tag_users', None)
        if "job_families" in data and int(data.get("shared_with")) == SHARED_WITH.ORGANIZATION_DEPARTMENTS:
            job_families = get_job_families(user, data.get("shared_with"), data) or []
            instance.job_families.clear()
            instance.job_families.add(*job_families)
        tags = data.get('tags', None)
        data["created_by"] = instance.created_by.id
        shared_with = data.get("shared_with")
        if "organizations" in data:
            instance.organizations.clear()
            if shared_with and int(shared_with) in (SHARED_WITH.ALL_DEPARTMENTS, SHARED_WITH.SELF_JOB_FAMILY):
                data["organizations"] = [user.organization_id]
            instance.organizations.add(*data.get("organizations"))

        if "departments" in data:
            instance.departments.clear()
            if shared_with and int(shared_with) == SHARED_WITH.SELF_DEPARTMENT:
                data["departments"] = list(user.departments.values_list("id", flat=True))
            instance.departments.add(*data.get("departments"))

        if "job_families" in data:
            job_families = data.get("job_families")
            instance.job_families.clear()
            instance.job_families.add(*job_families)
        serializer = self.get_serializer(instance, data=data)
        serializer.is_valid(raise_exception=True)
        if tag_users:
            tag_users_to_post(instance, tag_users)
        if tags:
            tags = list(tags.split(","))
            self.save_custom_tags(tags, user.organization)
            instance.tags.set(*tags)
        if request.FILES:
            self._upload_files(request, instance.pk)
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user
        if not user_can_delete(user, instance):
            raise serializers.ValidationError(_("You do not have permission to delete"))
        appreciation_trxns = instance.transactions.all()
        message = "reverting transaction for appreciation post {}".format(instance.title)
        if request.data.get("revert_transaction", False):
            reason, _ = PointsTable.objects.get_or_create(
                point_source=POINT_SOURCE.revoked_feed, organization=user.organization
            )
            for appreciation_trxn in appreciation_trxns:
                txn = Transaction.objects.create(
                    user=appreciation_trxn.user, creator=appreciation_trxn.creator,
                    organization=appreciation_trxn.user.organization,
                    points=-appreciation_trxn.points, reason=reason, message=message,
                    context={"appreciation_trxn": appreciation_trxn.id, "message": message}
                )
                if appreciation_trxn.context.get("use_own_points"):
                    Transaction.objects.create(
                        user=txn.creator, creator=appreciation_trxn.user,
                        organization=appreciation_trxn.user.organization,
                        points=appreciation_trxn.points, reason=reason, message=message,
                        context={"appreciation_trxn": appreciation_trxn.id, "message": message, "use_own_points": True,
                                "transaction_against_sender": txn.id, "is_creator_transaction": True}
                    )

        instance.mark_as_delete(user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_serializer(self, *args, **kwargs):
        if "pk" in self.kwargs:
            serializer_class = PostDetailSerializer
        else:
            serializer_class = PostSerializer
        kwargs["context"] = {"request": self.request}
        return serializer_class(*args, **kwargs)

    def get_queryset(self):
        feedback = self.request.query_params.get('feedback', None)
        created_by = self.request.query_params.get('created_by', None)
        post_id = self.kwargs.get("pk", None)
        user = self.request.user
        org = user.organization
        query = Q(mark_delete=False, post_type=POST_TYPE.USER_CREATED_POST)
        result = None
        if created_by == "user_org":
            query.add(Q(organizations=org, created_by__organization=org), query.connector)
        elif created_by == "user_dept":
            departments = user.cached_departments
            query.add(Q(departments__in=departments, created_by__departments__in=departments), query.connector)
        else:
            result = accessible_posts_by_user(
                user, org, allow_feedback=feedback is not None and feedback == "true",
                appreciations=is_appreciation_post(post_id) if post_id else False,
                post_id=None, departments=user.cached_departments, version=int(self.request.version)
            )

        if created_by in ("user_org", "user_dept"):
            if user.is_staff:
                query.add(
                    Q(mark_delete=False,
                      post_type=POST_TYPE.USER_CREATED_POST, created_by__organizations__in=user.child_organizations),
                    Q.OR)
            result = get_related_objects_qs(Post.objects.filter(query)).order_by(
                '-priority', '-modified_on', '-created_on')

        result = PostFilter(self.request.GET, queryset=result).qs
        return result

    @list_route(methods=["POST"], permission_classes=(IsOptionsOrAuthenticated,))
    def create_poll(self, request, *args, **kwargs):
        context = {'request': request}
        user = self.request.user
        payload = self.request.data
        data = {k: v for k, v in payload.items()}
        question = data.get('title', None)
        if not question:
            raise ValidationError(_('Question(title) is required to create a poll'))
        answers = data.get('answers', [])
        if not answers or len(answers) < 2:
            raise ValidationError(_('Minimum two answers are required to create a poll.'))
        data['post_type'] = POST_TYPE.USER_CREATED_POLL
        data['created_by'] = user.pk
        data['modified_by'] = user.pk
        # if feedback is not enabled then save current user organization
        if not ORGANIZATION_SETTINGS_MODEL.objects.get_value(MULTI_ORG_POST_ENABLE_FLAG, user.organization):
            data['organization'] = user.organization_id
        question_serializer = PostSerializer(data=data, context=context)
        question_serializer.is_valid(raise_exception=True)
        poll = question_serializer.save()
        for answer in answers:
            data['question'] = poll.pk
            data['answer_text'] = answer
            answer_serializer = PollsAnswerSerializer(data=data)
            answer_serializer.is_valid(raise_exception=True)
            answer_serializer.save()
        result = self.get_serializer(poll)
        notify_new_post_poll_created(poll)
        return Response(result.data)

    def get_ordering_field(self, default_order):
        """
        Returns allowed_ordering_fields in asc/desc order
        :param: default_order: str
        """
        allowed_ordering_fields = ("created_on", "id")
        order_by = self.request.query_params.get("orderBy", default_order)
        if order_by.replace("-", "") not in allowed_ordering_fields:
            order_by = default_order
        return order_by

    def user_allowed_to_comment(self, accessible_posts_queryset):
        """
        Allow Owner or if user is admin
        """
        user = self.request.user
        feedback_post_creators = list(accessible_posts_queryset.values_list("created_by_id", flat=True))
        # Allow if user is creator or admin
        if user.id in feedback_post_creators or user.is_staff:
            return True

        raise ValidationError(_('You do not have access to comment on this post'))

    @detail_route(methods=["GET", "POST"], permission_classes=(IsOptionsOrAuthenticated,))
    def comments(self, request, *args, **kwargs):
        """
        List of all the comments related to the post
        """
        query_params = self.request.query_params
        feedback = query_params.get('feedback', None)
        if feedback and feedback == "true":
            allow_feedback = True
            self.pagination_class = FeedsCommentsSetPagination
        else:
            allow_feedback = False
        user = self.request.user
        post_id = self.kwargs.get("pk", None)
        if not post_id:
            raise ValidationError(_('Post ID required to retrieve all the related comments'))
        post_id = int(post_id)
        org = (
            list(user.child_organizations.values_list("id", flat=True))
            if allow_feedback and user.is_staff else user.organization
        )
        accessible_posts_queryset = accessible_posts_by_user(
            user, org, allow_feedback, is_appreciation_post(post_id), post_id, None, request.version
        ).values_list('id', flat=True)
        accessible_posts = accessible_posts_queryset.values_list('id', flat=True)
        if post_id not in accessible_posts:
            raise ValidationError(_('You do not have access to comment on this post'))
        if self.request.method == "GET":
            serializer_context = {'request': self.request}

            # prepare a query dict
            query_dict = {
                "post_id": post_id,
                "parent": None,
                "mark_delete": False
            }

            # if comment id provided then pass only comments which are created after this one
            # this is used by progressive web app to fetch the latest comments
            last_comment_id = query_params.get("comment_id", 0)
            if last_comment_id:
                query_dict.update({"pk__gt": last_comment_id})

            comments = Comment.objects.filter(**query_dict).order_by(
                self.get_ordering_field(default_order="created_on")
            )
            page = self.paginate_queryset(comments)
            if page is not None:
                serializer = CommentSerializer(
                    page, many=True, read_only=True, context=serializer_context)
                return self.get_paginated_response(serializer.data)
            serializer = CommentSerializer(
                comments, many=True, read_only=True, context=serializer_context)
            return Response(serializer.data)
        elif self.request.method == "POST":
            if allow_feedback:
                self.user_allowed_to_comment(accessible_posts_queryset=accessible_posts_queryset)

            payload = self.request.data
            data = {k: v for k, v in payload.items()}

            tag_users = []
            content = data.get('content', None)
            if content:
                tagged = extract_tagged_users(content)
                if tagged:
                    tag_users.extend(tagged)

            data['post'] = post_id
            data['created_by'] = self.request.user.id
            data['modified_by'] = self.request.user.id
            serializer = CommentCreateSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            inst = serializer.save()

            # for feedback post, we need to allow the images and documents
            if allow_feedback and request.FILES:
                attach_files = dict((request.FILES).lists())
                images = attach_files.get('images', None)
                documents = attach_files.get('documents', None)

                if images:
                    for image in images:
                        image_serializer = ImagesSerializer(data={"comment": inst.pk, 'image': image})
                        image_serializer.is_valid(raise_exception=True)
                        image_serializer.save()

                if documents:
                    for document in documents:
                        document_serializer = DocumentsSerializer(data={"comment": inst.pk, "document": document})
                        document_serializer.is_valid(raise_exception=True)
                        document_serializer.save()

            if tag_users:
                tag_users_to_comment(inst, tag_users)
            post = Post.objects.filter(id=post_id).first()
            if post:
                notify_new_comment(inst, self.request.user)
            return Response(serializer.data)

    @detail_route(methods=["POST"], permission_classes=(IsOptionsOrAuthenticated,))
    def appreciate(self, request, *args, **kwargs):
        user = self.request.user

        post_id = self.kwargs.get("pk", None)
        if not post_id:
            raise ValidationError(_('Post ID required to appreciate a post'))
        post_id = int(post_id)
        accessible_posts = accessible_posts_by_user(
            user, user.organization, False, is_appreciation_post(post_id), post_id, None, request.version
        ).values_list('id', flat=True)
        if post_id not in accessible_posts:
            raise ValidationError(_('You do not have access to this post'))
        reaction_type = self.request.data.get('type', 0)  # to handle existing workflow
        object_type = NOTIFICATION_OBJECT_TYPE
        if PostLiked.objects.filter(post_id=post_id, created_by=user).exists():
            user_reactions = PostLiked.objects.filter(post_id=post_id, created_by=user, reaction_type=reaction_type)
            if user_reactions.exists():
                user_reactions.delete()
                liked = False
                message = "Successfully Removed Reaction"
            else:
                liked = True
                message = "Successfully Added Reaction"
                PostLiked.objects.filter(post_id=post_id, created_by=user).update(reaction_type=reaction_type)
            post_object = PostLiked.objects.filter(post_id=post_id, created_by=user).first()
            response_status = status.HTTP_200_OK
        else:
            post_object = PostLiked.objects.create(post_id=post_id, created_by=user, reaction_type=reaction_type)
            message = "Successfully Added Reaction"
            liked = True
            response_status = status.HTTP_201_CREATED
            post = Post.objects.filter(id=post_id).first()
            user_name = get_user_name(user)
            if post:
                send_notification = True
                if request.version >= 12 and user == post.created_by:
                    send_notification = False
                if send_notification:
                    notif_message = _("'%s' likes your post" % (user_name))
                    push_notification(user, notif_message, post.created_by, object_type=object_type,
                                      object_id=post.id, extra_context={"reaction_type": reaction_type})
        count = PostLiked.objects.filter(post_id=post_id).count()
        user_info = UserInfoSerializer(user).data

        post_reactions = list()
        post_likes = PostLiked.objects.filter(post_id=post_id)
        if post_likes.exists():
            post_reactions = post_likes.values('reaction_type').annotate(
                reaction_count=Count('reaction_type')).order_by('-reaction_count')[:2]

        return Response({
            "message": message, "liked": liked, "count": count, "user_info": user_info,
            "reaction_type": post_object.reaction_type if post_object else None, "post_reactions": post_reactions},
            status=response_status)

    @detail_route(methods=["GET"], permission_classes=(permissions.IsAuthenticated,))
    def appreciated_by(self, request, *args, **kwargs):
        user = self.request.user
        organization = user.organization
        post_id = self.kwargs.get("pk", None)
        if not post_id:
            raise ValidationError(_('Post ID required to appreciate a post'))
        post_id = int(post_id)
        accessible_posts = accessible_posts_by_user(
            user, organization, False, False, post_id, None, request.version
        ).values_list('id', flat=True)
        if post_id not in accessible_posts:
            raise ValidationError(_('You do not have access to this post'))
        posts_liked = PostLiked.objects.filter(post_id=post_id)
        page = self.paginate_queryset(posts_liked)
        if page is not None:
            serializer = PostLikedSerializer(page, many=True, read_only=True)
            return self.get_paginated_response(serializer.data)
        serializer = PostLikedSerializer(posts_liked, many=True, read_only=True)
        return Response(serializer.data)

    @detail_route(methods=["GET", "POST"],
                  permission_classes=(permissions.IsAuthenticated,))
    def answers(self, request, *args, **kwargs):
        user = self.request.user
        organization = user.organization
        post_id = self.kwargs.get("pk", None)
        if not post_id:
            raise ValidationError(_('Post ID required to retrieve all the related answers'))
        post_id = int(post_id)
        accessible_posts = accessible_posts_by_user(
            user, organization, False, False, post_id, None, request.version
        ).values_list('id', flat=True)
        accessible_polls = accessible_posts.filter(post_type=POST_TYPE.USER_CREATED_POLL)
        if post_id not in accessible_polls:
            raise ValidationError(_('This is not a poll.'))
        if post_id not in accessible_posts:
            raise ValidationError(_('You do not have access to check the answers to this poll'))
        if request.method == 'GET':
            answers = PollsAnswer.objects.filter(question=post_id)
            serializer = PollsAnswerSerializer(answers, many=True, read_only=True)
            return Response(serializer.data)
        if request.method == 'POST':
            payload = self.request.data
            data = {k: v for k, v in payload.items()}
            data['question'] = post_id
            serializer = PollsAnswerSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

    @detail_route(methods=["POST"], permission_classes=(IsOptionsOrAuthenticated,))
    def vote(self, request, *args, **kwargs):
        user = self.request.user
        organization = user.organization
        post_id = self.kwargs.get("pk", None)
        data = self.request.data
        answer_id = data.get('answer_id', None)
        if 'answer_id' not in data:
            raise ValidationError(_('answer_id is a required parameter.'))
        if not post_id:
            raise ValidationError(_('Post ID required to vote'))
        post_id = int(post_id)
        accessible_posts = accessible_posts_by_user(
            user, organization, False, False, post_id, None, request.version
        ).values_list('id', flat=True)
        if post_id not in accessible_posts:
            raise ValidationError(_('You do not have access'))
        accessible_polls = accessible_posts.filter(
            post_type=POST_TYPE.USER_CREATED_POLL
        )
        if post_id not in accessible_polls:
            raise ValidationError(_('This is not a poll question'))
        poll = None
        try:
            poll = Post.objects.get(id=post_id)
            poll.vote(user, answer_id)
        except Post.DoesNotExist:
            raise ValidationError(_('Poll does not exist.'))
        except PollsAnswer.DoesNotExist:
            raise ValidationError(_('This is not a correct answer.'))
        serializer = self.get_serializer(poll)
        return Response(serializer.data)

    @detail_route(methods=["POST"], permission_classes=(IsOptionsOrAuthenticated,))
    def flag(self, request, *args, **kwargs):
        user = self.request.user
        post_id = self.kwargs.get("pk", None)
        if not post_id:
            raise ValidationError(_('Post ID required to vote'))
        post_id = int(post_id)
        payload = self.request.data
        data = {k: v for k, v in payload.items()}
        accessible_posts = accessible_posts_by_user(
            user, user.organization, False, is_appreciation_post(post_id), post_id, None, request.version
        ).values_list('id', flat=True)
        if post_id not in accessible_posts:
            raise ValidationError(_('You do not have access'))
        data["flagger"] = user.id
        try:
            post = Post.objects.get(id=post_id)
            data["post"] = post.pk
            serializer = FlagPostSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            notify_flagged_post(post, self.request.user, data["notes"])
            return Response(serializer.data)
        except Post.DoesNotExist:
            raise ValidationError(_('Post does not exist.'))

    @list_route(methods=["POST"], permission_classes=(IsOptionsOrAuthenticated,))
    def pinned_post(self, request, *args, **kwargs):
        user = self.request.user
        organization = user.organization
        payload = self.request.data
        prior_till = payload.get("prior_till", None)
        post_id = payload.get("post_id", None)
        if not post_id:
            raise ValidationError(_('Post ID required to set priority'))
        post_id = int(post_id)
        accessible_posts = accessible_posts_by_user(
            user, organization, False, False, post_id, None, request.version).values_list('id', flat=True)
        if post_id not in accessible_posts:
            raise ValidationError(_('You do not have access'))
        try:
            post = Post.objects.get(pk=post_id)
            if post.priority:
                post.priority = False
                post.prior_till = None
                post.save()
            else:
                post.pinned(user, prior_till=prior_till)
            return Response(self.get_serializer(post).data)
        except Post.DoesNotExist:
            raise ValidationError(_('Post does not exist.'))

    @detail_route(methods=["GET"], permission_classes=(IsOptionsOrAuthenticated,))
    def post_appreciations(self, request, *args, **kwargs):
        post_id = self.kwargs.get("pk", None)
        recent = request.query_params.get("recent", None)
        reaction_type = request.query_params.get("reaction_type", None)
        post = Post.objects.get(id=post_id)
        post_likes = post.postliked_set.all().order_by("-id")
        all_reaction_count = post_likes.count()
        if recent:
            # returns latest 5 reactions
            post_ids = post_likes.values_list('id', flat=True)[:5]
            post_likes = post_likes.filter(id__in=post_ids)
        reaction_counts = list(post_likes.values('reaction_type').order_by('reaction_type').annotate(
            reaction_count=Count('reaction_type')))
        if reaction_type:
            post_likes = post_likes.filter(reaction_type=reaction_type)
        page = self.paginate_queryset(post_likes)
        serializer = PostLikedSerializer(page, post_likes, many=True)
        serializer.is_valid()
        post_reactions = self.get_paginated_response(serializer.data)
        reaction_counts.insert(0, {"reaction_type": 7, "reaction_count": all_reaction_count})
        post_reactions.data['counts'] = reaction_counts
        return post_reactions


class ImagesView(views.APIView):
    parser_classes = (MultiPartParser,)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        post_id = request.data['post_id']
        images = dict((request.data).lists())['images']
        flag = 1
        arr = []
        for img in images:
            data = {'post': post_id}
            data['image'] = img
            image_serializer = ImagesSerializer(data=data)
            if image_serializer.is_valid():
                image_serializer.save()
                arr.append(image_serializer.data)
            else:
                flag = 0
        if flag == 1:
            return Response(arr, status=status.HTTP_201_CREATED)
        else:
            return Response(arr, status=status.HTTP_400_BAD_REQUEST)


class ImagesDetailView(views.APIView):
    """
    delete an image instance
    """

    def get_object(self, pk):
        try:
            return Images.objects.get(pk=pk)
        except Images.DoesNotExist:
            raise Http404(_("Image does not exist"))

    def delete(self, request, pk, format=None):
        img = self.get_object(pk)
        img.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class VideosView(views.APIView):
    parser_classes = (MultiPartParser,)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        post_id = request.data['post_id']
        videos = dict((request.data).lists())['videos']
        flag = 1
        arr = []
        for video in videos:
            data = {'post': post_id}
            data['video'] = video
            video_serializer = VideosSerializer(data=data)
            if video_serializer.is_valid():
                video_serializer.save()
                arr.append(video_serializer.data)
            else:
                flag = 0
        if flag == 1:
            return Response(arr, status=status.HTTP_201_CREATED)
        else:
            return Response(arr, status=status.HTTP_400_BAD_REQUEST)


class CommentViewset(viewsets.ModelViewSet):
    permission_classes = (IsOptionsOrAuthenticated,)

    def get_serializer(self, *args, **kwargs):
        if "pk" in self.kwargs:
            serializer_class = CommentDetailSerializer
        else:
            serializer_class = CommentSerializer
        kwargs["context"] = {"request": self.request}
        return serializer_class(*args, **kwargs)

    @staticmethod
    def get_post_id_from_comment(comment_id):
        post_id = 0
        if comment_id:
            comment = Comment.objects.filter(id=comment_id).first()
            post_id = comment.post_id if comment else 0
        return post_id

    def get_queryset(self):
        user = self.request.user
        post_id = self.get_post_id_from_comment(self.kwargs.get("pk", 0))
        posts = accessible_posts_by_user(
            user, user.organization, False,
            is_appreciation_post(post_id) if post_id else False, None, None, self.request.version
        )

        result = Comment.objects.filter(post__in=posts, mark_delete=False)
        return result

    @detail_route(methods=["POST"], permission_classes=(IsOptionsOrAuthenticated,))
    def like(self, request, *args, **kwargs):
        user = self.request.user
        comment_id = self.kwargs.get("pk", None)
        if not comment_id:
            raise ValidationError(_('Comment ID is required'))
        post_id = self.get_post_id_from_comment(self.kwargs.get("pk", 0))
        organization = user.organization
        posts = accessible_posts_by_user(
            user, organization, False, is_appreciation_post(post_id) if post_id else False, post_id, None,
            request.version)
        accessible_comments = Comment.objects.filter(post__in=posts) \
            .values_list('id', flat=True)

        comment_id = int(comment_id)
        if comment_id not in accessible_comments:
            raise ValidationError(_('Not allowed to like the comment'))
        response_status = status.HTTP_304_NOT_MODIFIED

        reaction_type = self.request.data.get('type', None)
        if reaction_type is None:  # to handle existing workflow
            reaction_type = 0

        if CommentLiked.objects.filter(comment_id=comment_id, created_by=user).exists():
            user_reactions = CommentLiked.objects.filter(
                comment_id=comment_id, created_by=user, reaction_type=reaction_type)
            if user_reactions.exists():
                user_reactions.delete()
                message = "Successfully Removed Reaction"
                liked = False
                response_status = status.HTTP_200_OK
            else:
                liked = True
                message = "Successfully Added Reaction"
                CommentLiked.objects.filter(comment_id=comment_id, created_by=user).update(reaction_type=reaction_type)
        else:
            CommentLiked.objects.create(comment_id=comment_id, created_by=user, reaction_type=reaction_type)
            message = "Successfully Liked"
            liked = True
            response_status = status.HTTP_200_OK
            comment = Comment.objects.filter(id=comment_id).first()
            user_name = get_user_name(user)
            if comment:
                send_notification = True
                if request.version >= 12 and user == comment.created_by:
                    send_notification = False
                if send_notification:
                    notif_message = _("'%s' likes your comment" % (user_name))
                    push_notification(user, notif_message, comment.created_by, None, None,
                                      extra_context={"reaction_type": reaction_type})
        count = CommentLiked.objects.filter(comment_id=comment_id).count()
        user_info = UserInfoSerializer(user).data
        return Response({
            "message": message, "liked": liked, "count": count, "user_info": user_info},
            status=response_status)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user
        if not user_can_delete(user, instance):
            raise serializers.ValidationError(_("You do not have permission to delete"))
        instance.mark_as_delete(user)
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes((IsOptionsOrAuthenticated,))
def search_user(request):
    """
    Search users based on the search term
    """
    search_term = request.GET.get('term', None)
    query = request.GET.get('q', 'organization')
    user = request.user
    result = CustomUser.objects.filter(organization=user.organization)

    dept_users = []

    if query == 'department':
        for dept in DEPARTMENT_MODEL.objects.filter(users=user):
            for usr in dept.users.all():
                dept_users.append(usr.id)
        result = result.filter(id__in=dept_users)
    result = result.exclude(id=user.id)
    if search_term:
        result = result.filter(Q(email__istartswith=search_term) | Q(first_name__istartswith=search_term))
    serializer = UserInfoSerializer(result, many=True)
    return Response(serializer.data)


class ECardCategoryViewSet(viewsets.ModelViewSet):
    queryset = ECardCategory.objects.none()
    serializer_class = ECardCategorySerializer
    permission_classes = [IsOptionsOrAuthenticated, ]

    def get_queryset(self):
        user = self.request.user
        query = Q(organization=user.organization) | Q(organization__isnull=True)
        if self.request.query_params.get('admin_function'):
            query =  Q(organization=user.organization)
        queryset = ECardCategory.objects.filter(query)
        queryset = queryset.annotate(custom_order=Case(When(organization=user.organization, then=0),
                                     default=1, output_field=IntegerField())).order_by('custom_order')
        return queryset


class ECardViewSet(viewsets.ModelViewSet):
    queryset = ECard.objects.none()
    serializer_class = ECardSerializer
    permission_classes = [IsOptionsOrAuthenticated, ]

    def get_queryset(self):
        user = self.request.user
        query = Q(category__organization=user.organization) | Q(category__organization__isnull=True)
        if self.request.query_params.get('admin_function'):
            query =  Q(category__organization=user.organization)
        queryset = ECard.objects.filter(query)
        queryset = queryset.annotate(custom_order=Case(When(category__organization=user.organization, then=0),
                                     default=1, output_field=IntegerField())).order_by('custom_order')
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)
        return queryset

    @transaction.atomic
    def create(self, request):
        data = request.data
        serializer = ECardSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        ecard = serializer.save()
        ecard.tags.add(*eval(data["tags"]))
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def partial_update(self, request, pk=None):
        ecard = self.get_object()
        data = request.data
        serializer = ECardSerializer(ecard, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        ecard = serializer.save()
        ecard.tags.clear()
        ecard.tags.add(*eval(data["tags"]))
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class UserFeedViewSet(viewsets.ModelViewSet):
    parser_classes = (JSONParser,)
    permission_classes = (IsOptionsOrAuthenticated,)
    serializer_class = PostFeedSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    pagination_class = FeedsResultsSetPagination

    @staticmethod
    def get_filtered_feeds_according_to_shared_with(feeds, user, post_polls):
        """
        Returns filtered queryset (same dept posts will be returned if post is shared with departments)
        (All posts will be returned if shared with within organization)
        (hide posts which has shared with is admin only)
        params: posts: QuerySet[Post]
        params: user: CustomUser
        params: post_polls: Bool
        """
        return feeds.exclude(id__in=posts_not_visible_to_user(feeds, user, post_polls))

    @staticmethod
    def get_user_by_id(user_id, requested_user):
        """Returns the user by id provided"""
        try:
            user = CustomUser.objects.get(id=user_id, is_active=True)
            if user.organization not in requested_user.get_affiliated_orgs():
                raise CustomUser.DoesNotExist
        except (CustomUser.DoesNotExist, ValueError):
            raise ValidationError("Invalid user id")
        return user

    def get_queryset(self):
        feed_flag = self.request.query_params.get("feed", None)
        search = self.request.query_params.get("search", None)
        user_id = self.request.query_params.get("user_id", None)
        requested_user = self.request.user
        receiver_user = self.request.query_params.get("receiver_user", None)
        if receiver_user:
            requested_user = self.get_user_by_id(receiver_user, requested_user)

        user = (
            self.get_user_by_id(user_id, requested_user)
            if user_id and feed_flag in ("received", "given", "post_polls") else requested_user
        )

        organization = user.organization
        posts = accessible_posts_by_user(
            user, organization, False, feed_flag != "post_polls", None, None, self.request.version
        )
        if feed_flag == "post_polls":
            feeds = posts.filter(post_type__in=[POST_TYPE.USER_CREATED_POST,
                                                POST_TYPE.USER_CREATED_POLL], created_by=user)
            feeds = feeds.exclude(id__in=posts_not_visible_to_user(feeds, self.request.user, True))
            feeds = PostFilter(self.request.GET, queryset=feeds).qs
            return feeds.distinct()
        else:
            feeds = posts.filter(post_type__in=[POST_TYPE.USER_CREATED_APPRECIATION,
                                                POST_TYPE.USER_CREATED_NOMINATION])
        filter_appreciations = self.filter_appreciations(feeds)
        feeds = PostFilter(self.request.GET, queryset=feeds, user=user).qs
        feeds = (feeds | filter_appreciations).distinct()
        feeds = get_related_objects_qs(feeds)
        if feed_flag == "received":
            # returning only approved nominations with all the received appreciations
            feeds = feeds.filter(user=user).filter(Q(nomination__nom_status=NOMINATION_STATUS.approved) | Q(
                post_type=POST_TYPE.USER_CREATED_APPRECIATION))
        elif feed_flag == "given":
            feeds = feeds.filter(Q(created_by=user, post_type=POST_TYPE.USER_CREATED_APPRECIATION) | Q(
                nomination__nominator=user, nomination__nom_status=NOMINATION_STATUS.approved))
        elif feed_flag == "approvals":
            if self.request.version >= 13:
                feeds = feeds.filter(
                    Q(nomination__assigned_reviewer=user) | Q(nomination__alternate_reviewer=user) |
                    Q(nomination__histories__reviewer=user))
            else:
                feeds = feeds.filter(
                    Q(nomination__assigned_reviewer=user) | Q(nomination__alternate_reviewer=user)).exclude(
                    post_type=POST_TYPE.USER_CREATED_NOMINATION, nomination__nom_status__in=[
                        NOMINATION_STATUS.approved, NOMINATION_STATUS.rejected])
        elif feed_flag == "my_nomination":
            feeds = feeds.filter(nomination__nominator=user)
        else:
            feeds = feeds.filter(Q(nomination__nominator=user) | Q(user=user) |
                Q(nomination__assigned_reviewer=user) | Q(nomination__alternate_reviewer=user) |
                Q(nomination__histories__reviewer=user))
        if search:
            feeds = feeds.filter(Q(user__first_name__istartswith=search) | Q(
                user__last_name__istartswith=search) | Q(created_by__first_name__istartswith=search) | Q(
                created_by__last_name__istartswith=search))

        return self.get_filtered_feeds_according_to_shared_with(feeds=feeds, user=user,
                                                                post_polls=feed_flag == "post_polls").distinct()

    def list(self, request, *args, **kwargs):
        show_approvals = False
        supervisor_remaining_budget = ""
        page = self.paginate_queryset(self.get_queryset())
        serializer = PostFeedSerializer(page, context={"request": request}, many=True)
        user_id = self.request.query_params.get("user_id", None)
        requested_user = self.request.user
        user = self.get_user_by_id(user_id, requested_user) if user_id else requested_user
        organization = user.organization
        posts = accessible_posts_by_user(user, organization, False, False, None, None, request.version)
        approvals_count = posts.filter(
            Q(nomination__assigned_reviewer=user) | Q(nomination__alternate_reviewer=user),
            post_type=POST_TYPE.USER_CREATED_NOMINATION
        ).exclude(nomination__nom_status__in=[NOMINATION_STATUS.approved, NOMINATION_STATUS.rejected]).count()
        if approvals_count > 0 or user.is_nomination_reviewer:
            show_approvals = True
        if user.supervisor_remaining_budget is not None:
            supervisor_remaining_budget = str(user.supervisor_remaining_budget)
        feeds = self.get_paginated_response(serializer.data)
        feeds.data['approvals_count'] = approvals_count
        feeds.data['show_approvals'] = show_approvals
        feeds.data['supervisor_remaining_budget'] = supervisor_remaining_budget
        return feeds

    @list_route(methods=["GET"], permission_classes=(IsOptionsOrAuthenticated,))
    def appreciated_by(self, request, *args, **kwargs):
        requested_user = request.user
        user_id = self.request.query_params.get("user_id", None)
        user = self.get_user_by_id(user_id, requested_user) if user_id else requested_user
        organization = user.organization
        strength_id = request.query_params.get("strength", None)
        badge_id = request.query_params.get("badge", None)
        if strength_id is None and badge_id is None:
            raise ValidationError(_('You need to pass either strength or badge parameter.'))
        if strength_id:
            try:
                strength_id = int(strength_id)
            except ValueError:
                raise ValidationError(_('strength should be numeric value.'))

            posts = accessible_posts_by_user(user, organization, False, True, None, None, request.version)
            user_appreciations = posts.filter(
                user=user, post_type=POST_TYPE.USER_CREATED_APPRECIATION).values(
                'transactions__context', 'transactions__creator')

            my_appreciations_user = [user_appreciation.get('transactions__creator') for user_appreciation in
                                     user_appreciations if loads(user_appreciation.get('transactions__context') or '{}').get(
                'strength_id') == strength_id]

        if badge_id:
            try:
                badge_id = int(badge_id)
            except ValueError:
                raise ValidationError(_('badge should be numeric value.'))
            my_appreciations_user = user.nominees.filter(
                badge=badge_id, nom_status=NOMINATION_STATUS.approved).values_list('nominator', flat=True)

        users = CustomUser.objects.filter(id__in=my_appreciations_user)
        serializer = UserInfoSerializer(users, many=True, fields=["pk", "email", "first_name", "last_name",
                                                                  "profile_pic_url", "profile_img"])
        return Response({"users": serializer.data})

    @list_route(methods=["GET"], permission_classes=(IsOptionsOrAuthenticated,))
    def strengths(self, request, *args, **kwargs):
        user_id = request.query_params.get("user_id", None)
        strength_id = request.query_params.get("strength", None)
        if strength_id is None:
            raise ValidationError(_('strength is a required parameter.'))
        if user_id is None:
            raise ValidationError(_('user_id is a required parameter.'))
        if strength_id:
            try:
                strength_id = int(strength_id)
            except ValueError:
                raise ValidationError(_('strength should be numeric value.'))

        queryset = self.get_queryset().filter(post_type=POST_TYPE.USER_CREATED_APPRECIATION)
        user = CustomUser.objects.filter(id=user_id)
        if user.exists():
            user = user.first()
            queryset = queryset.filter(created_by=user)
        else:
            raise ValidationError(_('User does not exist'))
        transactions = queryset.values('id', 'transactions__context')
        posts = [transaction.get('id') for transaction in transactions if loads(
            transaction.get('transactions__context') or '{}').get('strength_id') == strength_id]
        queryset = queryset.filter(id__in=posts)
        serializer = PostFeedSerializer(queryset, many=True, context={"request": request}, fields=[
            "id", "ecard", "gif", "images", "description", "points", "images_with_ecard"])
        return Response({"strengths": serializer.data})

    @list_route(methods=["GET"], permission_classes=(IsOptionsOrAuthenticated,))
    def badges(self, request, *args, **kwargs):
        user_id = request.query_params.get("user_id", None)
        badge_id = request.query_params.get("badge", None)
        if user_id is None:
            raise ValidationError(_('user_id is a required parameter.'))
        if badge_id is None:
            raise ValidationError(_('badge is a required parameter.'))
        if badge_id:
            try:
                badge_id = int(badge_id)
            except ValueError:
                raise ValidationError(_('badge should be numeric value.'))
        queryset = self.get_queryset().filter(post_type=POST_TYPE.USER_CREATED_NOMINATION,
                                              nomination__badge=badge_id,
                                              nomination__nom_status=NOMINATION_STATUS.approved)
        user = CustomUser.objects.filter(id=user_id)
        if user.exists():
            user = user.first()
            queryset = queryset.filter(created_by=user)
        else:
            raise ValidationError(_('User does not exist'))
        # ToDo : once app updated, remove it ("badges" from nomination_field)
        serializer = PostFeedSerializer(queryset, many=True, context={
            "request": request, "nomination_fields": ["badges", "badge", "strength"]}, fields=[
            "id", "description", "nomination"])
        return Response({"badges": serializer.data})

    @list_route(methods=["GET"], permission_classes=(IsOptionsOrAuthenticated,))
    def recent_recognitions(self, request, *args, **kwargs):
        show_cheer_msg, show_approvals = False, False
        user = self.request.user
        organization = user.organization
        posts = accessible_posts_by_user(user, organization, False, False, None, None, request.version)
        feeds = posts.filter(post_type=POST_TYPE.USER_CREATED_APPRECIATION, user=request.user).distinct()
        # returns latest 5 appreciations from last 30 days
        start_date, end_date = get_date_range(30)
        feeds = feeds.filter(created_on__gte=start_date, created_on__lte=end_date)[:5]
        feeds = get_related_objects_qs(feeds)
        page = self.paginate_queryset(feeds)
        serializer = PostFeedSerializer(page, context={"request": request}, many=True)
        feeds = self.get_paginated_response(serializer.data)
        user_appreciation = posts.filter(post_type=POST_TYPE.USER_CREATED_APPRECIATION,
                                                created_by=request.user).first()
        if user_appreciation:
            days_passed = since_last_appreciation(user_appreciation.created_on)
            if 3 <= days_passed <= 120:
                feeds.data['days_passed'] = days_passed
                show_cheer_msg = True

        approvals_count = posts.filter(
            Q(nomination__assigned_reviewer=user) | Q(nomination__alternate_reviewer=user),
            post_type=POST_TYPE.USER_CREATED_NOMINATION
        ).exclude(nomination__nom_status__in=[NOMINATION_STATUS.approved, NOMINATION_STATUS.rejected]).count()
        if approvals_count > 0 or user.is_nomination_reviewer:
            show_approvals = True
        feeds.data['approvals_count'] = approvals_count
        feeds.data['show_approvals'] = show_approvals
        feeds.data['show_cheer_msg'] = show_cheer_msg
        try:
            feeds.data['points_left'] = request.user.appreciation_budget_left_in_month
        except AttributeError:
            feeds.data['points_left'] = None
        feeds.data['date'] = get_current_month_end_date()
        feeds.data['notification_count'] = request.user.unviewed_notifications_count
        feeds.data['recently_recognized_count'] = Post.objects.filter(created_by=user, user__is_active=True).count()
        feeds.data['org_logo'] = get_absolute_url(organization.display_img_url)
        return feeds

    def filter_appreciations(self, feeds):
        """
        Returns filtered QS which matches user strength id in transaction
        params: feeds QuerySet[Post]
        """
        strength_id = self.request.GET.get("user_strength", 0)

        # sometimes user_strength coming as empty string,
        if strength_id == '':
            return Post.objects.none()

        strength_id = int(strength_id) if isinstance(strength_id, (str, unicode)) else strength_id
        feeds = feeds.filter(transactions__context__isnull=False, transactions__isnull=False)
        return PostFilterBase(self.request.GET, queryset=feeds.filter(id__in=[
            feed.get("id")
            for feed in feeds.values("transactions__context", "id")
            if loads(feed.get("transactions__context") or '{}').get("strength_id") == strength_id
        ])).qs

    def merge_querset(self, feeds, filter_appreciations):
        post_ids = list(feeds.values_list("id", flat=True))
        post_ids.extend(list(filter_appreciations.values_list("id", flat=True)))
        return Post.objects.filter(id__in=post_ids)

    @list_route(methods=["GET"], permission_classes=(IsOptionsOrAuthenticated,))
    def organization_recognitions(self, request, *args, **kwargs):
        user = self.request.user
        post_polls = request.query_params.get("post_polls", None)
        post_polls_filter = request.query_params.get("post_polls_filter", None)
        greeting = request.query_params.get("greeting", None)
        user_id = request.query_params.get("user", None)
        organizations = user.organization
        filter_appreciations = Post.objects.none()
        posts = accessible_posts_by_user(
            user, organizations, False, False if post_polls else True, None, None, request.version
        )
        if post_polls:
            query_post = Q(post_type=POST_TYPE.USER_CREATED_POST)
            query_poll = Q(post_type=POST_TYPE.USER_CREATED_POLL)
            if int(request.version) >= 12:
                query_post.add(
                    Q(post_type=POST_TYPE.GREETING_MESSAGE, title="greeting_post", user__is_dob_public=True,
                      greeting__event_type=REPEATED_EVENT_TYPES.event_birthday), Q.OR
                )
                query_post.add(
                    Q(post_type=POST_TYPE.GREETING_MESSAGE, title="greeting_post", user__is_anniversary_public=True,
                      greeting__event_type=REPEATED_EVENT_TYPES.event_anniversary), Q.OR
                )

            if post_polls_filter == "post":
                query = query_post
            elif post_polls_filter == "poll":
                query = query_poll
            else:
                query = query_post | query_poll
            feeds = posts.filter(query)
        elif greeting:
            feeds = posts.filter(
                post_type=POST_TYPE.GREETING_MESSAGE, title="greeting", greeting_id=greeting, user=user,
                organizations__in=[organizations], created_on__year=datetime.datetime.now().year
            )
        else:
            query = (Q(post_type=POST_TYPE.USER_CREATED_APPRECIATION) |
                     Q(nomination__nom_status=NOMINATION_STATUS.approved, organizations__in=[organizations]))

            if user_id and str(user_id).isdigit():
                query.add(Q(user_id=user_id), query.AND)

            feeds = posts.filter(query).exclude(user__hide_appreciation=True)
            if self.request.GET.get("user_strength", 0):
                filter_appreciations = self.filter_appreciations(feeds)

        feeds = PostFilter(self.request.GET, queryset=feeds).qs
        search = self.request.query_params.get("search", None)
        if filter_appreciations.exists():
            feeds = (feeds | filter_appreciations).distinct()
        # feeds = self.get_filtered_feeds_according_to_shared_with(
        #     feeds=feeds, user=user, post_polls=post_polls).order_by('-priority', '-created_on')
        if post_polls:
            feeds = (feeds | posts_shared_with_org_department(
                user, [POST_TYPE.USER_CREATED_POST, POST_TYPE.USER_CREATED_POLL],
                feeds.values_list("id", flat=True))).distinct()
        if search:
            feeds = feeds.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(created_by__first_name__icontains=search) |
                Q(created_by__last_name__icontains=search) |
                Q(user__email__icontains=search) |
                Q(created_by__email__icontains=search) |
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )

        page = self.paginate_queryset(feeds.distinct())
        serializer = GreetingSerializer if greeting else OrganizationRecognitionSerializer
        serializer = serializer(page, context={"request": request}, many=True)
        return self.get_paginated_response(serializer.data)


class InspireMeViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.none()
    serializer_class = PostSerializer
    permission_classes = [IsOptionsOrAuthenticated, ]

    @list_route(methods=["POST"], permission_classes=(IsOptionsOrAuthenticated,))
    def amplify_core_value_recognition(self, request, *args, **kwargs):
        response = InspireMe.amplify_core_value_recognition(request.data)

        return Response(response, status=status.HTTP_200_OK)

    @list_route(methods=["POST"], permission_classes=(IsOptionsOrAuthenticated,))
    def edit_tone(self, request, *args, **kwargs):
        response = InspireMe.edit_tone(request.data)

        return Response(response, status=status.HTTP_200_OK)

    @list_route(methods=["POST"], permission_classes=(IsOptionsOrAuthenticated,))
    def amplify_content_post(self, request, *args, **kwargs):
        response = InspireMe.amplify_content_post(request.data)

        return Response(response, status=status.HTTP_200_OK)

    @list_route(methods=["POST"], permission_classes=(IsOptionsOrAuthenticated,))
    def amplify_content_poll(self, request, *args, **kwargs):
        response = InspireMe.amplify_content_poll(request.data)

        return Response(response, status=status.HTTP_200_OK)

    @list_route(methods=["POST"], permission_classes=(IsOptionsOrAuthenticated,))
    def proof_read_content(self, request, *args, **kwargs):
        response = InspireMe.proof_read_content(request.data)

        return Response(response, status=status.HTTP_200_OK)
