from django.contrib import admin

from feeds.models import FlagPost, Post, Comment, PostLiked, PollsAnswer


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'organization', 'shared_with', 'post_type',
        'created_by', 'created_on', 'modified_on', 'modified_by', 'mark_delete',
    )
    list_filter = ('organization', 'priority', 'mark_delete',)
    search_fields = ('organization__name',)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('content', 'parent', 'created_by', 'created_on', 'post')


@admin.register(PostLiked)
class PostLikedAdmin(admin.ModelAdmin):
    list_display = ('created_by', 'created_on', 'post',)


@admin.register(PollsAnswer)
class PollsAnswerAdmin(admin.ModelAdmin):
    list_display = ('question', 'answer_text', 'votes', 'get_voters')


@admin.register(FlagPost)
class FlagPostAdmin(admin.ModelAdmin):
    list_display = ('post', 'flagger', 'notes', 'accepted', 'notified')
