from __future__ import division, print_function, unicode_literals

from django.utils.translation import ugettext as _

from rest_framework import exceptions, serializers

from .models import (
    Comment, Post, PostLiked, PollsAnswer, Images, Videos,
)
from .utils import validate_priority


class ImagesSerializer(serializers.ModelSerializer):

    class Meta:
        model = Images
        fields = (
            'id', 'image', 'thumbnail_img_url', 'display_img_url',
            'large_img_url'
        )


class VideosSerializer(serializers.ModelSerializer):

    class Meta:
        model = Videos
        fields = (
            'post', 'video',
        )


class PostSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()
    videos = serializers.SerializerMethodField()
    answers = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = (
            "id", "created_by", "organization", "title", "description",
            "created_on", "published_date", "priority", "prior_till",
            "shared_with", "images", "videos", "answers", "post_type"
        )

    def get_images(self, instance):
        post_id = instance.id
        images = Images.objects.filter(post=post_id)
        return ImagesSerializer(images, many=True, read_only=True).data

    def get_videos(self, instance):
        post_id = instance.id
        videos = Videos.objects.filter(post=post_id)
        return VideosSerializer(videos, many=True, read_only=True).data
    
    def get_answers(self, instance):
        result = instance.related_answers()
        return PollsAnswerSerializer(result, many=True, read_only=True).data

    def create(self, validated_data):
        validate_priority(validated_data)
        return super(PostSerializer, self).create(validated_data)


class PostDetailSerializer(PostSerializer):

    comments = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = (
            "id", "created_by", "organization", "title", "description",
            "created_on", "published_date", "priority", "prior_till",
            "shared_with", "images", "videos", "answers", "post_type", "comments",
        )
    
    def get_comments(self, instance):
        post_id = instance.id
        comments = Comment.objects.filter(post=post_id)
        return CommentSerializer(comments, many=True, read_only=True).data

    def update(self, instance, validated_data):
        validate_priority(validated_data)
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get('description', instance.description)
        instance.shared_with = validated_data.get('shared_with', instance.shared_with)
        instance.priority = validated_data.get('priority', instance.priority)
        instance.save()
        return instance


class CommentSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        comment_response = kwargs.pop("comment_response", False)
        super(CommentSerializer, self).__init__(*args, **kwargs)
        if not comment_response:
            self.fields["comment_response"] = CommentSerializer(many=True, comment_response=True)

    class Meta:
        model = Comment
        fields = ("id", "content", "created_by", "created_on",
                  "post", "comment_response", "parent",)


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

    class Meta:
        model = PostLiked
        fields = (
            "id", "created_by", "created_on", "post",
        )
    
    def validate(self, data):
        """
        Check if user has already liked the post. 
        Do not allow the user to like the post again.
        """
        user = data['created_by']
        post = data['post']
        
        if PostLiked.objects.filter(post=post, created_by=user).exists():
            raise serializers.ValidationError(_("You cannot like the post again!"))
    
    def create(self, validated_data):
        return super(PostLikedSerializer, self).create(validated_data)


class PollsAnswerSerializer(serializers.ModelSerializer):

    class Meta:
        model = PollsAnswer
        fields = (
            "id", "question", "answer_text", "votes", "get_voters", "percentage",
        )
