from __future__ import division, print_function, unicode_literals

from django.conf import settings
from django.utils.module_loading import import_string
from django.utils.translation import ugettext as _

from rest_framework import exceptions, serializers

from .constants import POST_TYPE
from .models import (
    Comment, Documents, Post, PostLiked, PollsAnswer, Images, Videos, Voter,
)
from .utils import get_departments, get_profile_image, validate_priority


DEPARTMENT_MODEL = import_string(settings.DEPARTMENT_MODEL)
UserModel = import_string(settings.CUSTOM_USER_MODEL)


class DepartmentDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = DEPARTMENT_MODEL
        fields = (
            "name",
        )


class UserInfoSerializer(serializers.ModelSerializer):
    departments = serializers.SerializerMethodField()
    profile_img = serializers.SerializerMethodField()

    class Meta:
        model = UserModel
        fields = (
            "email", "first_name", "last_name", "departments", "profile_img",
        )

    def get_departments(self, instance):
        departments = get_departments(instance)
        return DepartmentDetailSerializer(departments, many=True, read_only=True).data

    def get_profile_img(self, instance):
        profile_image_url = get_profile_image(instance)
        return profile_image_url


class ImagesSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = Images
        fields = (
            'id', 'post', 'name', 'image', 'thumbnail_img_url', 'display_img_url',
            'large_img_url'
        )

    def get_name(self, instance):
        return instance.image.name


class DocumentsSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = Documents
        fields = (
            'id', 'post', 'name', 'document'
        )

    def get_name(self, instance):
        return instance.document.name


class VideosSerializer(serializers.ModelSerializer):

    class Meta:
        model = Videos
        fields = (
            'post', 'video',
        )


class PollSerializer(serializers.ModelSerializer):
    question = serializers.SerializerMethodField()
    answers = serializers.SerializerMethodField()
    user_has_voted = serializers.SerializerMethodField()
    total_votes = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = (
            'id', 'question', 'answers', 'is_poll_active', 'poll_remaining_time',
            'user_has_voted', 'total_votes', 'active_days',)

    def get_question(self, instance):
        return instance.title

    def get_answers(self, instance):
        request = self.context.get('request')
        serializer_context = {'request': request }
        user = request.user
        result = instance.related_answers()
        if not instance.is_poll_active:
            return SubmittedPollsAnswerSerializer(
                result, many=True, read_only=True,
                context=serializer_context).data
        if instance.user_has_voted(user):
            serializer = SubmittedPollsAnswerSerializer(
                result, many=True, read_only=True, context=serializer_context)
        else:
            serializer = PollsAnswerSerializer(
                result, many=True, read_only=True, context=serializer_context)
        return serializer.data

    def get_user_has_voted(self, instance):
        request = self.context.get('request')
        user = request.user
        return instance.user_has_voted(user)

    def get_total_votes(self, instance):
        return instance.total_votes()


class PostSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()
    videos = serializers.SerializerMethodField()
    created_by_user_info = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()
    has_appreciated = serializers.SerializerMethodField()
    appreciation_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    poll_info = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = (
            "id", "created_by", "created_on", "organization", "created_by_user_info",
            "title", "description", "post_type", "poll_info", "active_days",
            "priority", "prior_till",
            "shared_with", "images", "documents", "videos",
            "is_owner", "has_appreciated", "appreciation_count", "comments_count",
        )

    def get_poll_info(self, instance):
        if not instance.post_type == POST_TYPE.USER_CREATED_POLL:
            return None
        request = self.context.get('request')
        serializer_context = {'request': request }
        return PollSerializer(
            instance, read_only=True, context=serializer_context
        ).data

    def get_images(self, instance):
        if instance.post_type == POST_TYPE.USER_CREATED_POLL:
            return None
        post_id = instance.id
        images = Images.objects.filter(post=post_id)
        return ImagesSerializer(images, many=True, read_only=True).data

    def get_documents(self, instance):
        if instance.post_type == POST_TYPE.USER_CREATED_POLL:
            return None
        post_id = instance.id
        documents = Documents.objects.filter(post=post_id)
        return DocumentsSerializer(documents, many=True, read_only=True).data

    def get_videos(self, instance):
        if instance.post_type == POST_TYPE.USER_CREATED_POLL:
            return None
        post_id = instance.id
        videos = Videos.objects.filter(post=post_id)
        return VideosSerializer(videos, many=True, read_only=True).data

    def get_created_by_user_info(self, instance):
        created_by = instance.created_by
        user_detail = UserModel.objects.get(pk=created_by.id)
        return UserInfoSerializer(user_detail).data

    def get_is_owner(self, instance):
        request = self.context['request']
        return instance.created_by.pk == request.user.pk

    def get_has_appreciated(self, instance):
        request = self.context['request']
        user = request.user
        return PostLiked.objects.filter(post=instance, created_by=user).exists()

    def get_appreciation_count(self, instance):
        return PostLiked.objects.filter(post=instance).count()

    def get_comments_count(self, instance):
        return Comment.objects.filter(post=instance).count()

    def create(self, validated_data):
        validate_priority(validated_data)
        return super(PostSerializer, self).create(validated_data)


class PostDetailSerializer(PostSerializer):

    comments = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()
    has_appreciated = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = (
            "id", "created_by", "created_on", "organization", "created_by_user_info",
            "title", "description", "post_type", "poll_info", "active_days",
            "priority", "prior_till", "shared_with", "images", "documents", "videos",
            "is_owner", "has_appreciated", "appreciation_count",
            "comments_count", "comments",
        )

    def get_comments(self, instance):
        post_id = instance.id
        comments = Comment.objects.filter(post=post_id)
        return CommentSerializer(comments, many=True, read_only=True).data

    def get_is_owner(self, instance):
        request = self.context['request']
        return instance.created_by.pk == request.user.pk

    def get_has_appreciated(self, instance):
        request = self.context['request']
        user = request.user
        return PostLiked.objects.filter(post=instance, created_by=user).exists()

    def update(self, instance, validated_data):
        validate_priority(validated_data)
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get('description', instance.description)
        instance.shared_with = validated_data.get('shared_with', instance.shared_with)
        instance.priority = validated_data.get('priority', instance.priority)
        instance.save()
        return instance


class CommentSerializer(serializers.ModelSerializer):

    commented_by_user_info = serializers.SerializerMethodField()

    # def __init__(self, *args, **kwargs):
    #     comment_response = kwargs.pop("comment_response", False)
    #     super(CommentSerializer, self).__init__(*args, **kwargs)
    #     if not comment_response:
    #         self.fields["comment_response"] = CommentSerializer(many=True, comment_response=True)

    class Meta:
        model = Comment
        fields = ("id", "content", "created_by", "created_on",
                  "post", "commented_by_user_info")

    def get_commented_by_user_info(self, instance):
        created_by = instance.created_by
        user_detail = UserModel.objects.get(pk=created_by.id)
        return UserInfoSerializer(user_detail).data


class CommentCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Comment
        fields = ("id", "content", "created_by", "created_on",
                  "post", "parent",)
    
    def create(self, validated_data):
        return super(CommentCreateSerializer, self).create(validated_data)


class CommentDetailSerializer(CommentSerializer):

    class Meta:
        model = Comment
        fields = (
            "content",
            "created_by",
            "created_on",
            "post",
        )


class PostLikedSerializer(serializers.ModelSerializer):
    user_info = serializers.SerializerMethodField()

    class Meta:
        model = PostLiked
        fields = (
            "user_info", "created_on",
        )
    
    def get_user_info(self, instance):
        created_by = instance.created_by
        user_detail = UserModel.objects.get(pk=created_by.id)
        return UserInfoSerializer(user_detail).data


class PollsAnswerSerializer(serializers.ModelSerializer):
    voters_info = serializers.SerializerMethodField()

    class Meta:
        model = PollsAnswer
        fields = (
            "id", "question", "answer_text", "votes", "voters_info",
        )

    def get_voters_info(self, instance):
        voters = instance.get_voters()
        voters = UserModel.objects.filter(pk__in=voters)
        return UserInfoSerializer(voters, many=True, read_only=True).data


class SubmittedPollsAnswerSerializer(PollsAnswerSerializer):
    has_voted = serializers.SerializerMethodField()

    class Meta:
        model = PollsAnswer
        fields = (
            "id", "question", "answer_text", "votes", "has_voted",
            "percentage", "voters_info",
        )

    def get_has_voted(self, instance):
        request = self.context.get('request')
        user = request.user if request else None
        if user:
            return Voter.objects.filter(answer=instance, user=user).exists()
        return False
