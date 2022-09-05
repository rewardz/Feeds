from __future__ import division, print_function, unicode_literals

from django.conf import settings
from django.db.models import Q
from django.http import Http404
from django.utils.module_loading import import_string
from django.utils.translation import ugettext as _

from rest_framework import permissions, viewsets, serializers, status, views
from rest_framework.decorators import api_view, detail_route, list_route, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser, FormParser, FileUploadParser, JSONParser
from rest_framework.response import Response

from .constants import POST_TYPE, SHARED_WITH
from .models import (
    Comment, Documents, ECard, ECardCategory, FlagPost,
    Post, PostLiked, PollsAnswer, Images, CommentLiked,
)
from .paginator import FeedsResultsSetPagination
from .serializers import (
    CommentDetailSerializer, CommentSerializer, CommentCreateSerializer,
    DocumentsSerializer, ECardCategorySerializer, ECardSerializer, 
    FlagPostSerializer, PostLikedSerializer, PostSerializer,
    PostDetailSerializer, PollsAnswerSerializer, ImagesSerializer,
    UserInfoSerializer, VideosSerializer,
)
from .utils import (
    accessible_posts_by_user, extract_tagged_users, get_user_name, notify_new_comment,
    notify_new_poll_created, notify_flagged_post, push_notification, tag_users_to_comment,
    tag_users_to_post, user_can_delete, user_can_edit,
)

CustomUser = import_string(settings.CUSTOM_USER_MODEL)
DEPARTMENT_MODEL = import_string(settings.DEPARTMENT_MODEL)
NOTIFICATION_OBJECT_TYPE = import_string(settings.POST_NOTIFICATION_OBJECT_TYPE).Posts
UserStrength = import_string(settings.USER_STRENGTH_MODEL)
NOMINATION_STATUS = import_string(settings.NOMINATION_STATUS)
ORGANIZATION_SETTINGS_MODEL = import_string(settings.ORGANIZATION_SETTINGS_MODEL)
MULTI_ORG_POST_ENABLE_FLAG = settings.MULTI_ORG_POST_ENABLE_FLAG


class PostViewSet(viewsets.ModelViewSet):
    parser_classes = (MultiPartParser, JSONParser, FormParser,)
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = FeedsResultsSetPagination

    def _create_or_update(self, request, create=False):
        payload = request.data
        current_user = self.request.user
        if not current_user:
            raise serializers.ValidationError({'created_by': _('Created by is required!')})
        data = {}
        for key, value in payload.items():
            if key in ["organizations", "departments"] and isinstance(payload.get(key), unicode):
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
            self.save_custom_tags(tags, instance.organization)
            instance.tags.set(*tags)

        if request.FILES:
            self._upload_files(request, post_id)
        return Response(serializer.data)

    def update(self, request, pk=None):
        instance = self.get_object()
        user = request.user
        if not user_can_edit(user, instance):
            raise serializers.ValidationError(_("You do not have permission to edit"))
        data = self._create_or_update(request)
        tag_users = data.get('tag_users', None)
        tags = data.get('tags', None)
        data["created_by"] = instance.created_by.id
        serializer = self.get_serializer(instance, data=data)
        serializer.is_valid(raise_exception=True)
        if tag_users:
            tag_users_to_post(instance, tag_users)
        if tags:
            self.save_custom_tags(tags, instance.organization)
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
        if feedback and feedback == "true":
            allow_feedback = True
        else:
            allow_feedback = False
        user = self.request.user
        org = self.request.user.organization
        result = accessible_posts_by_user(user, org, allow_feedback=allow_feedback)
        result = result.order_by('-priority', '-modified_on', '-created_on')
        return result

    @list_route(methods=["POST"], permission_classes=(permissions.IsAuthenticated,))
    def create_poll(self, request, *args, **kwargs):
        context = {'request': request}
        user = self.request.user
        organization = user.organization
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
        data['organization'] = organization.pk
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
        notify_new_poll_created(poll)
        return Response(result.data)

    @detail_route(methods=["GET", "POST"], permission_classes=(permissions.IsAuthenticated,))
    def comments(self, request, *args, **kwargs):
        """
        List of all the comments related to the post
        """
        feedback = self.request.query_params.get('feedback', None)
        if feedback and feedback == "true":
            allow_feedback = True
        else:
            allow_feedback = False
        user = self.request.user
        organization = user.organization
        post_id = self.kwargs.get("pk", None)
        if not post_id:
            raise ValidationError(_('Post ID required to retrieve all the related comments'))
        post_id = int(post_id)
        accessible_posts = accessible_posts_by_user(
            user, organization, allow_feedback=allow_feedback).values_list('id', flat=True)
        if post_id not in accessible_posts:
            raise ValidationError(_('You do not have access to comment on this post'))
        if self.request.method == "GET":
            serializer_context = {'request': self.request}
            comments = Comment.objects.filter(post_id=post_id, parent=None). \
                order_by('-created_on')
            page = self.paginate_queryset(comments)
            if page is not None:
                serializer = CommentSerializer(
                    page, many=True, read_only=True, context=serializer_context)
                return self.get_paginated_response(serializer.data)
            serializer = CommentSerializer(
                comments, many=True, read_only=True, context=serializer_context)
            return Response(serializer.data)
        elif self.request.method == "POST":
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

    @detail_route(methods=["POST"], permission_classes=(permissions.IsAuthenticated,))
    def appreciate(self, request, *args, **kwargs):
        user = self.request.user
        organization = user.organization
        post_id = self.kwargs.get("pk", None)
        if not post_id:
            raise ValidationError(_('Post ID required to appreciate a post'))
        post_id = int(post_id)
        accessible_posts = accessible_posts_by_user(user, organization).values_list('id', flat=True)
        if post_id not in accessible_posts:
            raise ValidationError(_('You do not have access to this post'))
        apreciation_type = self.request.query_params.get("type", "like")
        message = None
        liked = False
        response_status = status.HTTP_304_NOT_MODIFIED
        object_type = NOTIFICATION_OBJECT_TYPE
        if apreciation_type.lower() == "like":
            if PostLiked.objects.filter(post_id=post_id, created_by=user).exists():
                PostLiked.objects.filter(post_id=post_id, created_by=user).delete()
                message = "Successfully unliked"
                liked = False
                response_status = status.HTTP_200_OK
            else:
                data = PostLiked.objects.create(post_id=post_id, created_by=user)
                message = "Successfully Liked"
                liked = True
                response_status = status.HTTP_201_CREATED
                post = Post.objects.filter(id=post_id).first()
                user_name = get_user_name(user)
                post_string = post.title[:20] + "..." if post.title else ""
                if post:
                    notif_message = _("'%s' likes your post %s" % (user_name, post_string))
                    push_notification(user, notif_message, post.created_by,
                                      object_type=object_type, object_id=post.id)
        count = PostLiked.objects.filter(post_id=post_id).count()
        user_info = UserInfoSerializer(user).data
        return Response({
            "message": message, "liked": liked, "count": count, "user_info": user_info},
            status=response_status)

    @detail_route(methods=["GET"], permission_classes=(permissions.IsAuthenticated,))
    def appreciated_by(self, request, *args, **kwargs):
        user = self.request.user
        organization = user.organization
        post_id = self.kwargs.get("pk", None)
        if not post_id:
            raise ValidationError(_('Post ID required to appreciate a post'))
        post_id = int(post_id)
        accessible_posts = accessible_posts_by_user(user, organization). \
            values_list('id', flat=True)
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
        accessible_posts = accessible_posts_by_user(user, organization).values_list('id', flat=True)
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

    @detail_route(methods=["POST"], permission_classes=(permissions.IsAuthenticated,))
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
        accessible_posts = accessible_posts_by_user(user, organization).values_list('id', flat=True)
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
        except Post.DoesNotExist as exp:
            raise ValidationError(_('Poll does not exist.'))
        except PollsAnswer.DoesNotExist as exp:
            raise ValidationError(_('This is not a correct answer.'))
        serializer = self.get_serializer(poll)
        return Response(serializer.data)

    @detail_route(methods=["POST"], permission_classes=(permissions.IsAuthenticated,))
    def flag(self, request, *args, **kwargs):
        user = self.request.user
        organization = user.organization
        post_id = self.kwargs.get("pk", None)
        payload = self.request.data
        data = {k: v for k, v in payload.items()}
        if not post_id:
            raise ValidationError(_('Post ID required to vote'))
        post_id = int(post_id)
        accessible_posts = accessible_posts_by_user(user, organization).values_list('id', flat=True)
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

    @list_route(methods=["POST"], permission_classes=(permissions.IsAuthenticated,))
    def pinned_post(self, request, *args, **kwargs):
        user = self.request.user
        organization = user.organization
        payload = self.request.data
        priority = payload.get("priority", True)
        prior_till = payload.get("prior_till", None)
        post_id = payload.get("post_id", None)
        if not post_id:
            raise ValidationError(_('Post ID required to set priority'))
        post_id = int(post_id)
        accessible_posts = accessible_posts_by_user(user, organization).values_list('id', flat=True)
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
        except Post.DoesNotExist as exp:
            raise ValidationError(_('Post does not exist.'))


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
    permission_classes = (permissions.IsAuthenticated,)

    def get_serializer(self, *args, **kwargs):
        if "pk" in self.kwargs:
            serializer_class = CommentDetailSerializer
        else:
            serializer_class = CommentSerializer
        kwargs["context"] = {"request": self.request}
        return serializer_class(*args, **kwargs)

    def get_queryset(self):
        user = self.request.user
        org = self.request.user.organization
        posts = accessible_posts_by_user(user, org)
        result = Comment.objects.filter(post__in=posts)
        return result

    @detail_route(methods=["POST"], permission_classes=(permissions.IsAuthenticated,))
    def like(self, request, *args, **kwargs):
        user = self.request.user
        organization = user.organization
        posts = accessible_posts_by_user(user, organization)
        accessible_comments = Comment.objects.filter(post__in=posts) \
            .values_list('id', flat=True)
        comment_id = self.kwargs.get("pk", None)
        if not comment_id:
            raise ValidationError(_('Comment ID is required'))
        comment_id = int(comment_id)
        if comment_id not in accessible_comments:
            raise ValidationError(_('Not allowed to like the comment'))
        message = None
        liked = False
        response_status = status.HTTP_304_NOT_MODIFIED

        if CommentLiked.objects.filter(comment_id=comment_id, created_by=user).exists():
            CommentLiked.objects.filter(comment_id=comment_id, created_by=user).delete()
            message = "Successfully UnLiked"
            liked = False
            response_status = status.HTTP_200_OK
        else:
            CommentLiked.objects.create(comment_id=comment_id, created_by=user)
            message = "Successfully Liked"
            liked = True
            response_status = status.HTTP_200_OK
            comment = Comment.objects.filter(id=comment_id).first()
            user_name = get_user_name(user)
            comment_string = comment.content[:20] + "..." if comment.content else ""
            if comment:
                notif_message = _("'%s' likes your comment %s" % (user_name, comment_string))
                push_notification(user, notif_message, comment.created_by)
        count = CommentLiked.objects.filter(comment_id=comment_id).count()
        user_info = UserInfoSerializer(user).data
        return Response({
            "message": message, "liked": liked, "count": count, "user_info": user_info},
            status=response_status)


@api_view(['GET'])
@permission_classes((permissions.IsAuthenticated,))
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
        result = result.filter(
            Q(email__istartswith=search_term) |
            Q(first_name__istartswith=search_term))
    serializer = UserInfoSerializer(result, many=True)
    return Response(serializer.data)


class ECardCategoryViewSet(viewsets.ModelViewSet):
    queryset = ECardCategory.objects.none()
    serializer_class = ECardCategorySerializer
    permission_classes = [permissions.IsAdminUser, ]

    def get_queryset(self):
        user = self.request.user
        queryset = ECardCategory.objects.filter(organization=user.organization)
        return queryset


class ECardViewSet(viewsets.ModelViewSet):
    queryset = ECard.objects.none()
    serializer_class = ECardSerializer
    permission_classes = [permissions.IsAdminUser, ]

    def get_queryset(self):
        user = self.request.user
        queryset = ECard.objects.filter(category__organization=user.organization)
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)
        return queryset
