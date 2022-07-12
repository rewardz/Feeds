from __future__ import division, print_function, unicode_literals

from django.conf import settings
from django.utils.module_loading import import_string
from django.utils.translation import ugettext as _

from rest_framework import exceptions, serializers

from .constants import POST_TYPE
from .models import (
    Comment, CommentLiked, Documents, ECard, ECardCategory, FlagPost,
    Post, PostLiked, PollsAnswer, Images, Videos, Voter,
)
from .utils import (
    get_departments, get_profile_image, validate_priority,
    user_can_delete, user_can_edit
)

DEPARTMENT_MODEL = import_string(settings.DEPARTMENT_MODEL)
UserModel = import_string(settings.CUSTOM_USER_MODEL)
Nominations = import_string(settings.NOMINATIONS_MODEL)
TrophyBadge = import_string(settings.TROPHY_BADGE_MODEL)
UserStrength = import_string(settings.USER_STRENGTH_MODEL)



def get_user_detail(user_id):
    return getattr(UserModel, settings.ALL_USER_OBJECT).filter(pk=user_id).first()


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
            "pk", "email", "first_name", "last_name", "departments", "profile_img",
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
        serializer_context = {'request': request}
        user = request.user
        result = instance.related_answers()
        if not instance.is_poll_active:
            return FinalPollsAnswerSerializer(
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


class TrophyBadgeSerializer(serializers.ModelSerializer):

    class Meta:
        model = TrophyBadge
        fields = ("id",
                  "name",
                  "description",
                  "background_color",
                  "icon")


class UserStrengthSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserStrength
        fields = ('id', 'name', 'illustration', 'background_color', 'message', 'icon')


class EcardSerializer(serializers.ModelSerializer):

    class Meta:
        model = ECard
        fields = ('id', 'name', 'image')


class NominationsSerializer(serializers.ModelSerializer):
    nomination_icon = serializers.SerializerMethodField()
    review_level = serializers.SerializerMethodField()
    nominator_name = serializers.SerializerMethodField()
    badges = serializers.SerializerMethodField()
    user_strength = UserStrengthSerializer()

    class Meta:
        model = Nominations
        fields = ("id",
                  "nomination_icon",
                  "review_level",
                  "nominator_name",
                  "comment",
                  "created",
                  "badges",
                  "user_strength",)

    @staticmethod
    def get_review_level(instance):
        return instance.category.reviewer_levels

    def get_nominator_name(self, instance):
        return instance.nominator.full_name

    def get_nomination_icon(self, instance):
        question_obj = instance.question.first()
        try:
            return question_obj.icon.url
        except (ValueError, AttributeError):
            return ""

    def get_badges(self, instance):
        if instance.category and instance.category.badge:
            return TrophyBadgeSerializer(instance=instance.category.badge).data
        return None


class UserStrengthSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserStrength
        fields = ('id', 'name', 'illustration', 'background_color', 'message', 'icon')


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
    can_edit = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    tagged_users = serializers.SerializerMethodField()
    is_admin = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    nomination = NominationsSerializer()
    feed_type = serializers.SerializerMethodField()
    user_strength = serializers.SerializerMethodField()
    user = UserInfoSerializer()
    user_reaction_type = serializers.SerializerMethodField()
    ecard = EcardSerializer()

    class Meta:
        model = Post
        fields = (
            "id", "created_by", "created_on", "modified_by", "modified_on",
            "organization", "created_by_user_info",
            "title", "description", "post_type", "poll_info", "active_days",
            "priority", "prior_till",
            "shared_with", "images", "documents", "videos",
            "is_owner", "can_edit", "can_delete", "has_appreciated",
            "appreciation_count", "comments_count", "tagged_users", "is_admin", "tags",
            "nomination", "feed_type", "user_strength", "user", "user_reaction_type", "gif", "ecard",
        )

    def get_tags(self, obj):
        return list(obj.tags.values_list("name", flat=True))

    def get_is_admin(self, instance):
        request = self.context['request']
        user = request.user
        return user.is_staff

    def get_poll_info(self, instance):
        if not instance.post_type == POST_TYPE.USER_CREATED_POLL:
            return None
        request = self.context.get('request')
        serializer_context = {'request': request}
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
        user_detail = get_user_detail(created_by.id)
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

    def get_can_edit(self, instance):
        request = self.context['request']
        return user_can_edit(request.user, instance)

    def get_can_delete(self, instance):
        request = self.context['request']
        return user_can_delete(request.user, instance)

    def get_tagged_users(self, instance):
        result = instance.tagged_users.all()
        return UserInfoSerializer(result, many=True, read_only=True).data

    def create(self, validated_data):
        validate_priority(validated_data)
        return super(PostSerializer, self).create(validated_data)

    def to_representation(self, instance):
        representation = super(PostSerializer, self).to_representation(instance)
        representation["created_on"] = instance.created_on.strftime("%Y-%m-%d")
        representation["modified_on"] = instance.modified_on. \
            strftime("%Y-%m-%d") if instance.modified_on else None
        return representation

    def get_feed_type(self, instance):
        if instance.post_type == POST_TYPE.USER_CREATED_NOMINATION:
            return "nomination"
        elif instance.post_type == POST_TYPE.USER_CREATED_APPRECIATION:
            return "appreciation"
        return instance.post_type

    def get_user_strength(self, instance):
        if instance.transaction:
            strength_id = instance.transaction.context.get('strength_id')
            if strength_id:
                return UserStrengthSerializer(instance=UserStrength.objects.filter(id=strength_id).first()).data
        return None

    def get_user_reaction_type(self, instance):
        request = self.context['request']
        user = request.user
        if PostLiked.objects.filter(post=instance, created_by=user).exists():
            return PostLiked.objects.filter(post=instance, created_by=user).values_list('reaction_type', flat=True)
        return None


class PostDetailSerializer(PostSerializer):
    comments = serializers.SerializerMethodField()
    appreciated_by = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = (
            "id", "created_by", "created_on", "modified_by", "modified_on",
            "organization", "created_by_user_info",
            "title", "description", "post_type", "poll_info", "active_days",
            "priority", "prior_till", "shared_with", "images", "documents", "videos",
            "is_owner", "can_edit", "can_delete", "has_appreciated",
            "appreciation_count", "appreciated_by", "comments_count", "comments",
            "tagged_users", "is_admin", "nomination", "feed_type", "user_strength", "user"
        )

    def get_comments(self, instance):
        request = self.context.get('request')
        serializer_context = {'request': request}
        post_id = instance.id
        comments = Comment.objects.filter(post=post_id).order_by('-created_on')[:20]
        return CommentSerializer(
            comments, many=True, read_only=True, context=serializer_context).data

    def get_appreciated_by(self, instance):
        post_id = instance.id
        posts_liked = PostLiked.objects.filter(post_id=post_id).order_by('-created_on')
        return PostLikedSerializer(posts_liked, many=True, read_only=True).data

    def update(self, instance, validated_data):
        validate_priority(validated_data)
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get('description', instance.description)
        instance.shared_with = validated_data.get('shared_with', instance.shared_with)
        instance.priority = validated_data.get('priority', instance.priority)
        instance.modified_by = validated_data.get('modified_by', instance.modified_by)
        instance.save()
        return instance


class CommentSerializer(serializers.ModelSerializer):
    commented_by_user_info = serializers.SerializerMethodField()
    liked_count = serializers.SerializerMethodField()
    liked_by = serializers.SerializerMethodField()
    has_liked = serializers.SerializerMethodField()
    tagged_users = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ("id", "content", "created_by", "created_on", "modified_by",
                  "modified_on", "post", "commented_by_user_info",
                  "liked_count", "liked_by", "has_liked", "tagged_users",)

    def get_commented_by_user_info(self, instance):
        created_by = instance.created_by
        user_detail = get_user_detail(created_by.id)
        return UserInfoSerializer(user_detail).data

    def get_liked_count(self, instance):
        return CommentLiked.objects.filter(comment=instance).count()

    def get_liked_by(self, instance):
        result = CommentLiked.objects.filter(comment=instance).order_by('-created_on')
        return CommentsLikedSerializer(result, many=True, read_only=True).data

    def get_tagged_users(self, instance):
        result = instance.tagged_users.all()
        return UserInfoSerializer(result, many=True, read_only=True).data

    def get_has_liked(self, instance):
        request = self.context['request']
        user = request.user
        return CommentLiked.objects.filter(comment=instance, created_by=user).exists()

    def to_representation(self, instance):
        representation = super(CommentSerializer, self).to_representation(instance)
        representation["created_on"] = instance.created_on.strftime("%Y-%m-%d %H:%M:%S")
        return representation


class CommentCreateSerializer(CommentSerializer):
    count = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ("id", "count", "content", "created_by", "created_on",
                  "modified_by", "post", "commented_by_user_info",)

    def get_count(self, instance):
        return Comment.objects.filter(post=instance.post).count()

    def create(self, validated_data):
        return super(CommentCreateSerializer, self).create(validated_data)


class CommentDetailSerializer(CommentSerializer):
    class Meta:
        model = Comment
        fields = (
            "id", "content", "created_by", "created_on", "modified_by",
            "modified_on", "post", "commented_by_user_info",
            "liked_count", "liked_by", "has_liked", "tagged_users",
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
        user_detail = get_user_detail(created_by.id)
        return UserInfoSerializer(user_detail).data

    def to_representation(self, instance):
        representation = super(PostLikedSerializer, self).to_representation(instance)
        representation["created_on"] = instance.created_on.strftime("%Y-%m-%d")
        return representation


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


class FinalPollsAnswerSerializer(SubmittedPollsAnswerSerializer):
    class Meta:
        model = PollsAnswer
        fields = (
            "id", "question", "answer_text", "votes", "has_voted",
            "percentage", "voters_info", "is_winner",
        )


class CommentsLikedSerializer(serializers.ModelSerializer):
    user_info = serializers.SerializerMethodField()

    class Meta:
        model = CommentLiked
        fields = (
            "user_info", "created_on",
        )

    def get_user_info(self, instance):
        created_by = instance.created_by
        user_detail = get_user_detail(created_by.id)
        return UserInfoSerializer(user_detail).data

    def to_representation(self, instance):
        representation = super(CommentsLikedSerializer, self).to_representation(instance)
        representation["created_on"] = instance.created_on.strftime("%Y-%m-%d")
        return representation


class FlagPostSerializer(serializers.ModelSerializer):
    user_info = serializers.SerializerMethodField()

    class Meta:
        model = FlagPost
        fields = (
            "user_info", "accepted", "notified", "notes", "flagger", "post",
        )

    def get_user_info(self, instance):
        user_detail = get_user_detail(instance.flagger.id)
        return UserInfoSerializer(user_detail).data


class ECardCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = ECardCategory
        fields = ('pk', 'name', 'organization')


class ECardSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    tags = serializers.SerializerMethodField()

    class Meta:
        model = ECard
        fields = ('pk', 'name', 'image', 'tags', 'category', 'category_name')

    def get_tags(self, obj):
        return list(obj.tags.values_list("name", flat=True))
