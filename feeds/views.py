from __future__ import division, print_function, unicode_literals

from django.db.models import Q
from django.http import Http404
from django.utils.translation import ugettext as _

from rest_framework import permissions, viewsets, serializers, status, views
from rest_framework.decorators import detail_route, list_route
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser, FormParser, FileUploadParser, JSONParser
from rest_framework.response import Response

from .constants import POST_TYPE, SHARED_WITH
from .models import (
    Comment, Documents, Post, PostLiked, PollsAnswer, Images, CommentLiked,
)
from .paginator import FeedsResultsSetPagination
from .serializers import (
    CommentDetailSerializer, CommentSerializer, CommentCreateSerializer,
    DocumentsSerializer, PostLikedSerializer, PostSerializer, PostDetailSerializer,
    PollsAnswerSerializer, ImagesSerializer, UserInfoSerializer, VideosSerializer,
)
from .utils import accessible_posts_by_user


class PostViewSet(viewsets.ModelViewSet):
    parser_classes = (MultiPartParser, JSONParser, FormParser, )
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = FeedsResultsSetPagination

    def _create_or_update(self, request):
        payload = request.data
        # print(payload.getlist('delete_image_ids', 'Nothing'))
        created_by = self.request.user
        if not created_by:
            raise serializers.ValidationError({'created_by': _('Created by is required!')})
        data = {k: v for k, v in payload.items()}
        delete_image_ids = data.get('delete_image_ids', None)
        delete_document_ids = data.get('delete_document_ids', None)

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
                    doc = Documents.objects.get(id=img_id)
                    doc.delete()
                except Documents.DoesNotExist:
                    continue

        data['created_by'] = created_by.id
        data['organization'] = created_by.organization_id
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

    def create(self, request, *args, **kwargs):
        data = self._create_or_update(request)
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        post_id = instance.id

        if request.FILES:
            self._upload_files(request, post_id)
        return Response(serializer.data)
    
    def update(self, request, pk=None):
        instance = self.get_object()
        user = request.user
        if not user.is_superuser:
            if instance.created_by.id != request.user.id:
                raise serializers.ValidationError(
                    {"created_by": _("A post can be updated only by its creator")})
            if instance.post_type in (
                POST_TYPE.USER_CREATED_POLL, POST_TYPE.SYSTEM_CREATED_POST):
                raise serializers.ValidationError(
                    {"post_type": _("You do not have permission to perform the action.")}
            )
        data = self._create_or_update(request)
        serializer = self.get_serializer(instance, data=data)
        serializer.is_valid(raise_exception=True)
        if request.FILES:
            self._upload_files(request, instance.pk)
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user
        if not user.is_superuser:
            if instance.created_by.id != request.user.id:
                raise serializers.ValidationError(
                    {"created_by": _("A post can be deleted only by its creator")})
            if instance.post_type in (
                POST_TYPE.USER_CREATED_POLL, POST_TYPE.SYSTEM_CREATED_POST):
                raise serializers.ValidationError(
                    {"post_type": _("You do not have permission to perform the action.")}
            )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_serializer(self, *args, **kwargs):
        if "pk" in self.kwargs:
            serializer_class = PostDetailSerializer
        else:
            serializer_class = PostSerializer
        kwargs["context"] = {"request": self.request}
        return serializer_class(*args, **kwargs)

    def get_queryset(self):
        user = self.request.user
        org = self.request.user.organization
        result = accessible_posts_by_user(user, org)
        result = result.order_by('-priority', '-created_on')
        return result

    @list_route(methods=["POST"], permission_classes=(permissions.IsAuthenticated,))
    def create_poll(self, request, *args, **kwargs):
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
        data['organization'] = organization.pk
        question_serializer = PostSerializer(data=data)
        question_serializer.is_valid(raise_exception=True)
        poll = question_serializer.save()
        for answer in answers:
            data['question'] = poll.pk
            data['answer_text'] = answer
            answer_serializer = PollsAnswerSerializer(data=data)
            answer_serializer.is_valid(raise_exception=True)
            answer_serializer.save()
        result = self.get_serializer(poll)
        return Response(result.data)
    
    @detail_route(methods=["GET", "POST"], permission_classes=(permissions.IsAuthenticated,))
    def comments(self, request, *args, **kwargs):
        """
        List of all the comments related to the post
        """
        user = self.request.user
        organization = user.organization
        post_id = self.kwargs.get("pk", None)
        if not post_id:
            raise ValidationError(_('Post ID required to retrieve all the related comments'))
        post_id = int(post_id)
        accessible_posts = accessible_posts_by_user(user, organization).\
            values_list('id', flat=True)
        if post_id not in accessible_posts:
            raise ValidationError(_('You do not have access to comment on this post'))
        if self.request.method == "GET":
            comments = Comment.objects.filter(post_id=post_id, parent=None).\
                order_by('-created_on')
            page = self.paginate_queryset(comments)
            if page is not None:
                serializer = CommentSerializer(page, many=True, read_only=True)
                return self.get_paginated_response(serializer.data)
            serializer = CommentSerializer(comments, many=True, read_only=True)
            return Response(serializer.data)
        elif self.request.method == "POST":
            payload = self.request.data
            data = {k: v for k, v in payload.items()}
            data['post'] = post_id
            data['created_by'] = self.request.user.id
            serializer = CommentCreateSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
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
        count = PostLiked.objects.filter(post_id=post_id).count()
        user_info = UserInfoSerializer(user).data
        return Response({
            "message": message, "liked": liked, "count": count, "user_info":user_info},
            status=response_status)

    @detail_route(methods=["GET"], permission_classes=(permissions.IsAuthenticated,))
    def appreciated_by(self, request, *args, **kwargs):
        user = self.request.user
        organization = user.organization
        post_id = self.kwargs.get("pk", None)
        if not post_id:
            raise ValidationError(_('Post ID required to appreciate a post'))
        post_id = int(post_id)
        accessible_posts = accessible_posts_by_user(user, organization).\
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
    queryset = Comment.objects.none()

    def get_serializer(self, *args, **kwargs):
        if "pk" in self.kwargs:
            serializer_class = CommentDetailSerializer
        else:
            serializer_class = CommentSerializer
        kwargs["context"] = {"request": self.request}
        return serializer_class(*args, **kwargs)

    def get_queryset(self):
        user = self.request.user
    
    @detail_route(methods=["POST"], permission_classes=(permissions.IsAuthenticated,))
    def like(self, request, *args, **kwargs):
        user = self.request.user
        organization = user.organization
        comment_id = self.kwargs.get("pk", None)
        if not comment_id:
            raise ValidationError(_('Comment ID is required'))
        comment_id = int(comment_id)
        message = None
        liked = False
        response_status = status.HTTP_304_NOT_MODIFIED
        
        if CommentLiked.objects.filter(comment_id=comment_id, created_by=user).exists():
            CommentLiked.objects.filter(comment_id=comment_id, created_by=user).delete()
            message = "Successfully UnLiked"
            liked = False
            response_status = status.HTTP_200_OK
        else:
            data = CommentLiked.objects.create(comment_id=comment_id, created_by=user)
            message = "Successfully Liked"
            liked = True
        return Response({"message": message, "liked": liked}, status=response_status)
