from django.contrib import admin

from feeds.models import Post, Comment, PostLiked, Clap, PollsAnswer

# Register your models here.
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('created_by', 'title', 'description', 'created_date', 'published_date', 'priority',
                    'prior_till', 'shared_with', 'poll',)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('content', 'parent', 'commented_by', 'commented_on', 'post')


@admin.register(PostLiked)
class PostLikedAdmin(admin.ModelAdmin):
    list_display = ('liked_by', 'liked_on', 'post',)


@admin.register(Clap)
class ClapAdmin(admin.ModelAdmin):
    list_display = ('clapped_by', 'clapped_on', 'post',)


# @admin.register(PollsQuestion)
# class PollsQuestionAdmin(admin.ModelAdmin):
#     list_display = ('question_text', 'organization', 'created_by', 'created_on', 'shared_with')


@admin.register(PollsAnswer)
class PollsAnswerAdmin(admin.ModelAdmin):
    list_display = ('question', 'answer_text', 'votes', 'get_voters')
