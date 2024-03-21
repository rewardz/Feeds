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
    validate_priority, user_can_delete, user_can_edit, get_absolute_url, get_job_families,
    get_feed_type, get_user_reaction_type
)

DEPARTMENT_MODEL = import_string(settings.DEPARTMENT_MODEL)
Organization = import_string(settings.ORGANIZATION_MODEL)
UserModel = import_string(settings.CUSTOM_USER_MODEL)
Question = import_string(settings.QUESTION_MODEL)
Answer = import_string(settings.ANSWER_MODEL)
NominationCategory = import_string(settings.NOMINATION_CATEGORY_MODEL)
Nominations = import_string(settings.NOMINATIONS_MODEL)
TrophyBadge = import_string(settings.TROPHY_BADGE_MODEL)
UserStrength = import_string(settings.USER_STRENGTH_MODEL)
NOMINATION_STATUS_COLOR_CODE = import_string(settings.NOMINATION_STATUS_COLOR_CODE)
REVIEWER_LEVEL = import_string(settings.REVIEWER_LEVEL)
ORGANIZATION_SETTINGS_MODEL = import_string(settings.ORGANIZATION_SETTINGS_MODEL)
MULTI_ORG_POST_ENABLE_FLAG = settings.MULTI_ORG_POST_ENABLE_FLAG
RepeatedEventSerializer = import_string(settings.REPEATED_EVENT_SERIALIZER)


def get_user_detail(user_id):
    try:
        return getattr(UserModel, settings.ALL_USER_OBJECT).get(pk=user_id)
    except UserModel.DoesNotExist:
        return


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


def get_images_with_ecard(post):
    """
    Returns the serialized images
    :params: post: Post
    :returns: [ImagesSerializer]
    """
    all_images = list()
    if not post.post_type == POST_TYPE.USER_CREATED_POLL:
        all_images = ImagesSerializer(post.images_set, many=True, read_only=True).data
    if post.ecard:
        all_images.insert(0, ECardSerializer(post.ecard).data)
    return all_images


def get_user_strength(instance):
    """
    Returns the serialized user strength data
    :params: instance: Post
    :returns: UserStrengthSerializer/None
    """
    transaction = instance.transactions.first()
    if transaction:
        strength_id = transaction.context.get('strength_id')
        if strength_id:
            try:
                return UserStrengthSerializer(instance=UserStrength.objects.get(id=strength_id)).data
            except UserStrength.DoesNotExist:
                return
    elif instance.nomination and instance.nomination.user_strength:
        return UserStrengthSerializer(instance=instance.nomination.user_strength).data
    return None


def get_poll_info(instance, request):
    """
    Returns the serialized user Poll data
    :params: instance: Post
    :params: request: HttpRequestObj
    :returns: PollSerializer/None
    """
    if not instance.post_type == POST_TYPE.USER_CREATED_POLL:
        return None
    serializer_context = {'request': request}
    return PollSerializer(
        instance, read_only=True, context=serializer_context
    ).data


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

    @staticmethod
    def get_departments(instance):
        return list(get_departments(instance).values("name"))

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


class AnswerSerializer(serializers.ModelSerializer):
    supporting_doc = serializers.SerializerMethodField()

    class Meta:
        model = Answer
        fields = ("id", "question", "answer", "supporting_doc")

    def get_supporting_doc(self, instance):
        try:
            doc = instance.supporting_doc.supporting_doc.url
        except (ValueError, AttributeError):
            doc = ""
        return doc


class QuestionSerializer(serializers.ModelSerializer):
    answer = serializers.SerializerMethodField(source="answer_set")

    def get_answer(self, instance):
        nomination_id = self.context.get("nomination_id")
        answers = Answer.objects.filter(question=instance, nomination_id=nomination_id)
        return AnswerSerializer(answers, many=True).data

    class Meta:
        model = Question
        fields = ("pk", "question_lable", "question_type", "answer")


class CategoriesSerializer(serializers.ModelSerializer):

    class Meta:
        model = NominationCategory
        fields = ("id", "name", "img", "is_group_nomination")


class NominationsSerializer(DynamicFieldsModelSerializer):
    category_data = CategoriesSerializer(source="category")
    nomination_icon = serializers.SerializerMethodField()
    review_level = serializers.SerializerMethodField()
    nominator_name = serializers.SerializerMethodField()
    question = serializers.SerializerMethodField()
    badges = serializers.SerializerMethodField()
    badge = TrophyBadgeSerializer(read_only=True)
    user_strength = UserStrengthSerializer()
    strength = serializers.SerializerMethodField()
    nominated_team_member = UserInfoSerializer()
    nominees = UserInfoSerializer(many=True)
    nom_status = serializers.SerializerMethodField()
    nom_status_color = serializers.SerializerMethodField()
    nom_status_approvals = serializers.SerializerMethodField()

    class Meta:
        model = Nominations
        fields = ("id",
                  "category",
                  "category_data",
                  "nomination_icon",
                  "review_level",
                  "nominator_name",
                  "question",
                  "comment",
                  "created",
                  "badges",
                  "badge",
                  "user_strength",
                  "nominated_team_member",
                  "nominees",
                  "message_to_reviewer",
                  "strength",
                  "nom_status",
                  "nom_status_color",
                  "nom_status_approvals")

    @staticmethod
    def get_review_level(instance):
        return instance.badge.reviewer_level if instance.badge else REVIEWER_LEVEL.none

    def get_nominator_name(self, instance):
        return instance.nominator.full_name

    def get_nomination_icon(self, instance):
        question_obj = instance.question.first()
        try:
            return question_obj.icon.url
        except (ValueError, AttributeError):
            return ""

    def get_question(self, instance):
        questions = instance.question.all()
        serializer = QuestionSerializer(instance=questions, many=True, context={'nomination_id': instance.id})
        return serializer.data

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
        elif instance.nom_status in [3, 6]:
            return "Approved"
        else:
            return "Pending"

    @staticmethod
    def get_nom_status_color(instance):
        return NOMINATION_STATUS_COLOR_CODE.get(instance.nom_status)

    def get_nom_status_approvals(self, instance):
        user = self.context.get("user", None)
        if not user or not user.is_nomination_reviewer:
            return ""

        history = instance.histories.filter(reviewer=user).first()
        if history and history.status == 4:
            return "Rejected"
        elif history and history.status in [3, 6]:
            return "Approved"
        else:
            return "Pending"


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
    job_families = serializers.SerializerMethodField()
    created_on = serializers.SerializerMethodField()
    modified_on = serializers.SerializerMethodField()

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
            "images_with_ecard", "departments", "organization", "department", "job_families"
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
        return self.context['request'].user.is_staff

    def get_job_families(self, instance):
        return instance.job_families.values_list("id", flat=True)

    def get_poll_info(self, instance):
        return get_poll_info(instance, self.context.get('request'))

    @staticmethod
    def get_images(instance):
        if instance.post_type == POST_TYPE.USER_CREATED_POLL:
            return None
        return ImagesSerializer(instance.images_set, many=True).data

    @staticmethod
    def get_documents(instance):
        if instance.post_type == POST_TYPE.USER_CREATED_POLL:
            return None
        return DocumentsSerializer(instance.documents_set, many=True).data

    @staticmethod
    def get_videos(instance):
        if instance.post_type == POST_TYPE.USER_CREATED_POLL:
            return None
        return VideosSerializer(instance.videos_set, many=True).data

    def get_created_by_user_info(self, instance):
        return UserInfoSerializer(instance.created_by, context={'request': self.context.get('request')}).data

    def get_is_owner(self, instance):
        return instance.created_by == self.context['request'].user

    def get_has_appreciated(self, instance):
        return instance.postliked_set.filter(created_by=self.context['request'].user).exists()

    @staticmethod
    def get_appreciation_count(instance):
        return instance.postliked_set.count()

    @staticmethod
    def get_comments_count(instance):
        return instance.comment_set.filter(mark_delete=False).count()

    def get_can_edit(self, instance):
        return user_can_edit(self.context['request'].user, instance)

    def get_can_delete(self, instance):
        return user_can_delete(self.context['request'].user, instance)

    @staticmethod
    def get_tagged_users(instance):
        return UserInfoSerializer(instance.tagged_users, many=True).data

    @staticmethod
    def get_modified_on(instance):
        if instance.modified_on:
            return instance.modified_on.strftime("%Y-%m-%d")

    @staticmethod
    def get_created_on(instance):
        return instance.created_on.strftime("%Y-%m-%d")

    def create(self, validated_data):
        request = self.context.get('request', None)
        user = request.user
        validate_priority(validated_data)
        organizations = validated_data.pop('organizations', None)
        shared_with = self.initial_data.pop('shared_with', None)
        job_families = get_job_families(user, shared_with, self.initial_data)

        if not organizations:
            organization = self.initial_data.pop('organization', None)
            organizations = [organization] if organization else organization

        if not organizations and not ORGANIZATION_SETTINGS_MODEL.objects.get_value(MULTI_ORG_POST_ENABLE_FLAG, user.organization):
            organizations = [user.organization]

        departments = validated_data.pop('departments', None)
        if not departments and not organizations:
            if shared_with:
                if int(shared_with) == SHARED_WITH.SELF_DEPARTMENT:
                    departments = user.departments.all()
                elif int(shared_with) in (SHARED_WITH.ALL_DEPARTMENTS, SHARED_WITH.SELF_JOB_FAMILY):
                    organizations = [user.organization]

        post = Post.objects.create(**validated_data)

        if post:
            if organizations:
                post.organizations.add(*organizations)
            if departments:
                post.departments.add(*departments)
            if job_families:
                post.job_families.add(*job_families)

        return post

    @staticmethod
    def get_feed_type(instance):
        return get_feed_type(instance)

    @staticmethod
    def get_user_strength(instance):
        return get_user_strength(instance)

    @staticmethod
    def get_reaction_type(instance):
        post_likes = instance.postliked_set
        if post_likes.exists():
            return post_likes.values('reaction_type').annotate(
                reaction_count=Count('reaction_type')).order_by('-reaction_count')[:2]
        return list()

    def get_user_reaction_type(self, instance):
        return get_user_reaction_type(self.context['request'].user, instance)

    def get_nomination(self, instance):
        return NominationsSerializer(instance=instance.nomination,
            context={"user": self.context['request'].user},
            fields=self.context.get('nomination_fields')).data

    def get_points(self, instance):
        return str(instance.points(self.context['request'].user))

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
        return get_images_with_ecard(instance)


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
    job_families = serializers.SerializerMethodField()

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
            "department_name", "departments", "can_download", "is_download_choice_needed", "greeting_info",
            "job_families"
        )

    @staticmethod
    def get_job_families(instance):
        return instance.job_families.values_list("id", flat=True)

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

    @staticmethod
    def get_organization_name(instance):
        return instance.feedback.organization_name if instance.feedback else ""

    @staticmethod
    def get_display_status(instance):
        return instance.feedback.display_status if instance.feedback else ""

    @staticmethod
    def get_department_name(instance):
        return instance.feedback.department_name if instance.feedback else ""

    def get_comments(self, instance):
        return CommentSerializer(
            instance.comment_set.filter(mark_delete=False).order_by('-created_on')[:20],
            many=True, context={'request': self.context.get('request')}).data

    @staticmethod
    def get_appreciated_by(instance):
        return PostLikedSerializer(instance.postliked_set.order_by('-created_on'), many=True).data

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
            "images_with_ecard", "greeting_info",  "departments", "job_families"
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


class GreetingSerializerBase(serializers.ModelSerializer):
    created_on = serializers.SerializerMethodField()
    created_by_user_info = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()
    is_admin = serializers.SerializerMethodField()
    feed_type = serializers.SerializerMethodField()
    ecard = ECardSerializer(read_only=True)
    images_with_ecard = serializers.SerializerMethodField()
    greeting_info = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        super(GreetingSerializerBase, self).__init__(*args, **kwargs)
        self.request = self.context.get("request")
        self.user = self.request.user

    @staticmethod
    def get_created_on(instance):
        return instance.created_on.strftime("%Y-%m-%d")

    def get_created_by_user_info(self, instance):
        return UserInfoSerializer(instance.created_by, context={'request': self.request}).data

    def get_is_owner(self, instance):
        return instance.created_by == self.user

    def get_is_admin(self, instance):
        return self.user.is_staff

    @staticmethod
    def get_feed_type(instance):
        return get_feed_type(instance)

    @staticmethod
    def get_greeting_info(post):
        return get_info_for_greeting_post(post)

    @staticmethod
    def get_images_with_ecard(instance):
        return get_images_with_ecard(instance)

    class Meta:
        model = Post
        fields = (
            "id", "created_by", "created_on", "organizations", "created_by_user_info", "title", "description",
            "post_type", "priority", "shared_with", "is_owner", "is_admin", "feed_type",
            "gif", "ecard", "images_with_ecard", "greeting_info"
        )


class OrganizationRecognitionSerializer(GreetingSerializerBase):
    modified_on = serializers.SerializerMethodField()
    appreciation_count = serializers.SerializerMethodField()
    poll_info = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    has_appreciated = serializers.SerializerMethodField()
    reaction_type = serializers.SerializerMethodField()
    user_strength = serializers.SerializerMethodField()
    user_reaction_type = serializers.SerializerMethodField()
    points = serializers.SerializerMethodField()
    nomination = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()

    @staticmethod
    def get_modified_on(instance):
        if instance.modified_on:
            return instance.modified_on.strftime("%Y-%m-%d")

    @staticmethod
    def get_appreciation_count(instance):
        return instance.postliked_set.count()

    def get_poll_info(self, instance):
        return get_poll_info(instance, self.context.get('request'))

    @staticmethod
    def get_comments_count(instance):
        return instance.comment_set.filter(mark_delete=False).count()

    def get_can_edit(self, instance):
        return user_can_edit(self.user, instance)

    def get_can_delete(self, instance):
        return user_can_delete(self.user, instance)

    def get_has_appreciated(self, instance):
        return instance.postliked_set.filter(created_by=self.user).exists()

    @staticmethod
    def get_reaction_type(instance):
        if instance.postliked_set.count() > 0:
            return instance.postliked_set.values('reaction_type').annotate(
                reaction_count=Count('reaction_type')).order_by('-reaction_count')[:2]
        return list()

    @staticmethod
    def get_user_strength(instance):
        return get_user_strength(instance)

    def get_user_reaction_type(self, instance):
        return get_user_reaction_type(self.user, instance)

    def get_points(self, instance):
        return str(instance.points(self.user))

    def get_nomination(self, instance):
        return NominationsSerializer(
            instance=instance.nomination, context={"user": self.user}, fields=self.context.get('nomination_fields')
        ).data

    def get_user(self, post):
        return get_user_detail_with_org(post, {"request": self.request})

    class Meta:
        model = Post
        fields = GreetingSerializerBase.Meta.fields + (
            "modified_by", "modified_on", "poll_info", "active_days", "priority", "prior_till", "can_edit",
            "can_delete", "has_appreciated", "appreciation_count", "comments_count", "reaction_type", "nomination",
            "user_strength", "user", "user_reaction_type", "points", "departments", "job_families"
        )


class GreetingSerializer(GreetingSerializerBase):
    tagged_users = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()

    @staticmethod
    def get_tagged_users(instance):
        result = instance.tagged_users.all()
        return UserInfoSerializer(result, many=True).data

    @staticmethod
    def get_tags(obj):
        return list(obj.tags.values_list("name", flat=True))

    class Meta:
        model = Post
        fields = GreetingSerializerBase.Meta.fields + ("tagged_users", "tags")
