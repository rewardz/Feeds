from django.contrib import admin

from feeds.models import Post, Comment, PostLiked, PollsAnswer


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'organization', 'priority', 'prior_till', 'shared_with', 
        'post_type', 'created_by', 'created_on',
    )
    list_filter = ('organization', 'priority')
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
