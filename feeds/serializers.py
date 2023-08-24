from __future__ import division, print_function, unicode_literals

from django.conf import settings
from django.utils.module_loading import import_string
from django.db.models import Count

from rest_framework import serializers

from .constants import POST_TYPE, SHARED_WITH
from .models import (
    Comment, CommentLiked, Documents, ECard, ECardCategory, FlagPost,
    Post, PostLiked, PollsAnswer, Images, Videos, Voter,
)
from .utils import (
    extract_tagged_users, get_departments, get_profile_image, tag_users_to_comment,
    validate_priority, user_can_delete, user_can_edit, get_absolute_url
)

DEPARTMENT_MODEL = import_string(settings.DEPARTMENT_MODEL)
Organization = import_string(settings.ORGANIZATION_MODEL)
UserModel = import_string(settings.CUSTOM_USER_MODEL)
Nominations = import_string(settings.NOMINATIONS_MODEL)
TrophyBadge = import_string(settings.TROPHY_BADGE_MODEL)
UserStrength = import_string(settings.USER_STRENGTH_MODEL)
NOMINATION_STATUS_COLOR_CODE = import_string(settings.NOMINATION_STATUS_COLOR_CODE)
ORGANIZATION_SETTINGS_MODEL = import_string(settings.ORGANIZATION_SETTINGS_MODEL)
MULTI_ORG_POST_ENABLE_FLAG = settings.MULTI_ORG_POST_ENABLE_FLAG
RepeatedEventSerializer = import_string(settings.REPEATED_EVENT_SERIALIZER)


def get_user_detail(user_id):
    return getattr(UserModel, settings.ALL_USER_OBJECT).filter(pk=user_id).first()


def get_user_detail_with_org(post, context):
    user = post.user
    user_details = UserInfoSerializer(instance=user, read_only=True, context=context).data
    if post.greeting:
        user_details.update({
            "organization_name": user.organization.name,
            "organization_logo": (
                get_absolute_url(user.organization.display_img_url) if user.organization.display_img_url else ""
            )
        })
    return user_details


def get_info_for_greeting_post(post):
    """
    Returns greeting details if it is public post then we are passing ORG setting which decides to show name of DEPT
    :params: post: Post
    :returns: dict: RepeatedEventSerializer
    """
    context = {}
    if post.title == "greeting_post":
        context.update(
            {"show_greeting_department": post.user.organization.has_setting_to_show_greeting_department})
    return RepeatedEventSerializer(post.greeting, context=context).data


class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop('fields', None)
        self.show_repr = kwargs.pop('show_repr', True)

        # Instantiate the superclass normally
        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)

        request = self.context.get("request")
        if not fields:
            if request:
                fields = request.query_params.get('fields')
                fields = tuple(fields.split(",")) if fields else None

        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class DepartmentDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = DEPARTMENT_MODEL
        fields = (
            "name",
        )


class UserInfoSerializer(DynamicFieldsModelSerializer):
    departments = serializers.SerializerMethodField()
    profile_img = serializers.SerializerMethodField()

    class Meta:
        model = UserModel
        fields = (
            "pk", "email", "first_name", "last_name", "departments", "profile_img", "full_name"
        )

    def get_departments(self, instance):
        departments = get_departments(instance)
        return DepartmentDetailSerializer(departments, many=True, read_only=True).data

    def get_profile_img(self, instance):
        request = self.context.get('request')
        if request and request.version >= 12 and not instance.img:
            return None
        profile_image_url = get_profile_image(instance)
        return profile_image_url


class ImagesSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = Images
        fields = (
            'id', 'post', 'name', 'image', 'thumbnail_img_url', 'display_img_url',
            'large_img_url', 'comment'
        )

    def get_name(self, instance):
        return instance.image.name


class DocumentsSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = Documents
        fields = (
            'id', 'post', 'name', 'document', 'comment'
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
    award_points = serializers.SerializerMethodField()

    class Meta:
        model = TrophyBadge
        fields = ("id",
                  "name",
                  "description",
                  "background_color",
                  "icon",
                  "points",
                  "award_points")

    @staticmethod
    def get_award_points(instance):
        points = instance.points
        if points:
            points = int(points) if points - int(points) == 0 else float(points)
        return str(points)


class UserStrengthSerializer(serializers.ModelSerializer):
    award_points = serializers.SerializerMethodField()

    class Meta:
        model = UserStrength
        fields = ('id', 'name', 'illustration', 'background_color', 'message', 'icon', 'points', 'award_points',
                  'background_color_lite')

    @staticmethod
    def get_award_points(instance):
        points = instance.points
        if points - int(points) == 0:
            points = int(points)
        else:
            points = float(points)
        return str(points)


class ECardSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    tags = serializers.SerializerMethodField()

    class Meta:
        model = ECard
        fields = ('pk', 'name', 'image', 'tags', 'category', 'category_name', 'thumbnail_img_url', 'display_img_url',
                  'large_img_url')

    def get_tags(self, obj):
        return list(obj.tags.values_list("name", flat=True))


class NominationsSerializer(DynamicFieldsModelSerializer):
    nomination_icon = serializers.SerializerMethodField()
    review_level = serializers.SerializerMethodField()
    nominator_name = serializers.SerializerMethodField()
    badges = serializers.SerializerMethodField()
    badge = TrophyBadgeSerializer(read_only=True)
    user_strength = UserStrengthSerializer()
    strength = serializers.SerializerMethodField()
    nominated_team_member = UserInfoSerializer()
    nom_status = serializers.SerializerMethodField()
    nom_status_color = serializers.SerializerMethodField()

    class Meta:
        model = Nominations
        fields = ("id",
                  "category",
                  "nomination_icon",
                  "review_level",
                  "nominator_name",
                  "comment",
                  "created",
                  "badges",
                  "badge",
                  "user_strength",
                  "nominated_team_member",
                  "message_to_reviewer",
                  "strength",
                  "nom_status",
                  "nom_status_color")

    @staticmethod
    def get_review_level(instance):
        return instance.badge.reviewer_level if instance.badge else instance.category.reviewer_level

    def get_nominator_name(self, instance):
        return instance.nominator.full_name

    def get_nomination_icon(self, instance):
        question_obj = instance.question.first()
        try:
            return question_obj.icon.url
        except (ValueError, AttributeError):
            return ""

    def get_badges(self, instance):
        # ToDo : once app updated, remove it
        if instance.badge:
            return TrophyBadgeSerializer(instance=instance.badge).data
        return None

    @staticmethod
    def get_strength(instance):
        return instance.user_strength.name if instance.user_strength else ""

    @staticmethod
    def get_nom_status(instance):
        if instance.nom_status == 4:
            return "Rejected"
        elif instance.nom_status == 3:
            return "Approved"
        return "Pending"

    @staticmethod
    def get_nom_status_color(instance):
        return NOMINATION_STATUS_COLOR_CODE.get(instance.nom_status)


class PostSerializer(DynamicFieldsModelSerializer):
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
    departments = serializers.PrimaryKeyRelatedField(
        many=True, queryset=DEPARTMENT_MODEL.objects.all(),
        required=False, allow_null=True
    )
    organizations = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Organization.objects.all(),
        required=False, allow_null=True
    )
    nomination = serializers.SerializerMethodField()
    feed_type = serializers.SerializerMethodField()
    user_strength = serializers.SerializerMethodField()
    reaction_type = serializers.SerializerMethodField()
    user_reaction_type = serializers.SerializerMethodField()
    points = serializers.SerializerMethodField()
    time_left = serializers.SerializerMethodField()
    images_with_ecard = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()
    department = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = (
            "id", "created_by", "created_on", "modified_by", "modified_on",
            "organizations", "created_by_user_info",
            "title", "description", "post_type", "poll_info", "active_days",
            "priority", "prior_till",
            "shared_with", "images", "documents", "videos",
            "is_owner", "can_edit", "can_delete", "has_appreciated",
            "appreciation_count", "comments_count", "tagged_users", "is_admin", "tags", "reaction_type", "nomination",
            "feed_type", "user_strength", "user", "user_reaction_type", "gif", "ecard", "points", "time_left",
            "images_with_ecard", "departments", "organization", "department"
        )

    def get_organization(self, instance):
        organization = instance.organizations.first()
        return organization.id if organization else organization

    def get_department(self, instance):
        department = instance.departments.first()
        return department.id if department else department

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
        request = self.context.get('request')
        created_by = instance.created_by
        user_detail = get_user_detail(created_by.id)
        return UserInfoSerializer(user_detail, context={'request': request}).data

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
        return Comment.objects.filter(post=instance, mark_delete=False).count()

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
        request = self.context.get('request', None)
        validate_priority(validated_data)
        organizations = validated_data.pop('organizations', None)
        if not organizations:
            organization = self.initial_data.pop('organization', None)
            organizations = [organization] if organization else organization

        user = request.user

        if not organizations and not ORGANIZATION_SETTINGS_MODEL.objects.get_value(MULTI_ORG_POST_ENABLE_FLAG, user.organization):
            organizations = [user.organization]

        departments = validated_data.pop('departments', None)
        if not departments and not organizations:
            shared_with = self.initial_data.pop('shared_with', None)
            if shared_with:
                if int(shared_with) == SHARED_WITH.SELF_DEPARTMENT:
                    departments = user.departments.all()
                elif int(shared_with) == SHARED_WITH.ALL_DEPARTMENTS:
                    organizations = [user.organization]

        post = Post.objects.create(**validated_data)

        if post:
            if organizations:
                post.organizations.add(*organizations)
            if departments:
                post.departments.add(*departments)
        return post

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
        elif instance.nomination and instance.nomination.user_strength:
            return UserStrengthSerializer(instance=instance.nomination.user_strength).data
        return None

    def get_reaction_type(self, instance):
        post_likes = PostLiked.objects.filter(post=instance)
        if post_likes.exists():
            return post_likes.values('reaction_type').annotate(
                reaction_count=Count('reaction_type')).order_by('-reaction_count')[:2]
        return list()

    def get_user_reaction_type(self, instance):
        request = self.context['request']
        user = request.user
        post_likes = PostLiked.objects.filter(post=instance, created_by=user)
        if post_likes.exists():
            return post_likes.first().reaction_type
        return None

    def get_nomination(self, instance):
        return NominationsSerializer(instance=instance.nomination, fields=self.context.get('nomination_fields')).data

    @staticmethod
    def get_points(instance):
        points = 0
        if instance.transaction:
            points = instance.transaction.points
            if points - int(points) == 0:
                points = int(points)
            else:
                points = float(points)
        return str(points)

    @staticmethod
    def get_time_left(instance):
        if instance.nomination:
            time_left_in_hours = instance.nomination.time_left_for_auto_action
            if time_left_in_hours is None:
                return ""
            if time_left_in_hours < 1:
                return "{}m Left".format(int(time_left_in_hours * 60))
            else:
                return "{}h Left".format(int(time_left_in_hours))
        return ""

    @staticmethod
    def get_images_with_ecard(instance):
        all_images = list()
        if not instance.post_type == POST_TYPE.USER_CREATED_POLL:
            images = Images.objects.filter(post=instance.id)
            all_images = ImagesSerializer(images, many=True, read_only=True).data
        if instance.ecard:
            all_images.insert(0, ECardSerializer(instance.ecard).data)
        return all_images


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


class PostDetailSerializer(PostSerializer):
    comments = serializers.SerializerMethodField()
    appreciated_by = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    ecard = ECardSerializer(read_only=True)
    category = serializers.CharField(read_only=True)
    category_name = serializers.CharField(read_only=True)
    sub_category = serializers.CharField(read_only=True)
    sub_category_name = serializers.CharField(read_only=True)
    organization_name = serializers.SerializerMethodField()
    display_status = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()
    can_download = serializers.SerializerMethodField()
    is_download_choice_needed = serializers.SerializerMethodField()
    greeting_info = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = (
            "id", "created_by", "created_on", "modified_by", "modified_on",
            "organizations", "created_by_user_info",
            "title", "description", "post_type", "poll_info", "active_days",
            "priority", "prior_till", "shared_with", "images", "documents", "videos",
            "is_owner", "can_edit", "can_delete", "has_appreciated",
            "appreciation_count", "appreciated_by", "comments_count", "comments",
            "tagged_users", "is_admin", "nomination", "feed_type", "user_strength", "user",
            "gif", "ecard", "points", "user_reaction_type", "images_with_ecard", "reaction_type", "category",
            "category_name", "sub_category", "sub_category_name", "organization_name", "display_status",
            "department_name", "departments", "can_download", "is_download_choice_needed", "greeting_info"
        )

    @staticmethod
    def get_is_download_choice_needed(post):
        """
        Decides if popup should be open or not to select image in frontend
        """
        is_download_choice_needed = True
        if post.certificate_records.count():
            # already we have choice selected
            is_download_choice_needed = False
        else:
            total_attached_images = post.attached_images().count()
            ecard = post.ecard
            gif = post.gif
            if gif:
                # if we have gif
                is_download_choice_needed = False
            elif total_attached_images == 1 and not ecard:
                # we have only one image and no e card
                is_download_choice_needed = False
            elif total_attached_images == 0 and ecard:
                # we have 0 image and have ecard
                is_download_choice_needed = False
            elif all([not total_attached_images, not ecard, not gif]):
                # we don't have image/ ecard/ gif
                is_download_choice_needed = False
        return is_download_choice_needed

    def get_can_download(self, instance):
        return self.context.get("request").user in (instance.user, instance.created_by)

    def get_user(self, post):
        return get_user_detail_with_org(post, {"request": self.context.get("request")})

    @staticmethod
    def get_greeting_info(post):
        return get_info_for_greeting_post(post)

    def get_organization_name(self, instance):
        return instance.feedback.organization_name if instance.feedback else ""

    def get_display_status(self, instance):
        return instance.feedback.display_status if instance.feedback else ""

    def get_department_name(self, instance):
        return instance.feedback.department_name if instance.feedback else ""

    def get_comments(self, instance):
        request = self.context.get('request')
        if request.version > 12:
            return
        serializer_context = {'request': request}
        post_id = instance.id
        comments = Comment.objects.filter(post=post_id).order_by('-created_on')[:20]
        return CommentSerializer(
            comments, many=True, read_only=True, context=serializer_context).data

    def get_appreciated_by(self, instance):
        if self.context.get('request').version > 12:
            return
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
        instance.gif = validated_data.get('gif')
        ecard_id = self.initial_data.get('ecard')
        instance.ecard = ECard.objects.filter(id=ecard_id).first() if ecard_id else None
        instance.save()
        return instance


class PostFeedSerializer(PostSerializer):
    user = serializers.SerializerMethodField()
    ecard = ECardSerializer(read_only=True)
    greeting_info = serializers.SerializerMethodField()

    @staticmethod
    def get_greeting_info(post):
        return get_info_for_greeting_post(post)

    def get_user(self, post):
        return get_user_detail_with_org(post, {"request": self.context.get("request")})

    class Meta:
        model = Post
        fields = (
            "id", "created_by", "created_on", "modified_by", "modified_on",
            "organizations", "created_by_user_info",
            "title", "description", "post_type", "poll_info", "active_days",
            "priority", "prior_till",
            "shared_with", "images", "documents", "videos",
            "is_owner", "can_edit", "can_delete", "has_appreciated",
            "appreciation_count", "comments_count", "tagged_users", "is_admin", "tags", "reaction_type", "nomination",
            "feed_type", "user_strength", "user", "user_reaction_type", "gif", "ecard", "points", "time_left",
            "images_with_ecard", "greeting_info"
        )


class GreetingSerializer(PostFeedSerializer):

    class Meta:
        model = Post
        fields = (
            "id", "created_by", "created_on", "organizations", "created_by_user_info", "title", "description",
            "post_type", "priority", "shared_with", "is_owner", "tagged_users", "is_admin", "tags", "feed_type",
            "gif", "ecard", "images_with_ecard", "greeting_info"
        )


class CommentSerializer(serializers.ModelSerializer):
    commented_by_user_info = serializers.SerializerMethodField()
    liked_count = serializers.SerializerMethodField()
    liked_by = serializers.SerializerMethodField()
    has_liked = serializers.SerializerMethodField()
    tagged_users = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ("id", "content", "created_by", "created_on", "modified_by",
                  "modified_on", "post", "commented_by_user_info", "reaction_types",
                  "liked_count", "liked_by", "has_liked", "tagged_users", "images", "documents")

    def get_images(self, instance):
        """
        Get images for the comment instance
        """
        images = Images.objects.filter(comment=instance.id)
        return ImagesSerializer(images, many=True, read_only=True).data

    def get_documents(self, instance):
        """
        Get documents for the comment instance
        """
        documents = Documents.objects.filter(comment=instance.id)
        return DocumentsSerializer(documents, many=True, read_only=True).data

    def get_commented_by_user_info(self, instance):
        created_by = instance.created_by
        user_detail = get_user_detail(created_by.id)
        return UserInfoSerializer(user_detail, fields=["pk", "first_name", "last_name", "profile_img", "full_name",
                                                       "departments"]).data

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
                  "modified_by", "post", "commented_by_user_info", "images", "documents")

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

    def update(self, instance, validated_data):
        content = validated_data.get('content', None)
        if content:
            tag_users = extract_tagged_users(content)
            if tag_users:
                tag_users_to_comment(instance, tag_users)
        return super(CommentDetailSerializer, self).update(instance, validated_data)


class PostLikedSerializer(serializers.ModelSerializer):
    user_info = serializers.SerializerMethodField()

    class Meta:
        model = PostLiked
        fields = (
            "user_info", "created_on", "reaction_type"
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
