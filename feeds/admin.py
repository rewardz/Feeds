from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.db import models

from ajax_select import make_ajax_form

from feeds.models import (
    Comment, ECard, ECardCategory, FlagPost, Images, PollsAnswer, Post, PostLiked, PostReportAbuse)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    form = make_ajax_form(Post, {
        'user': 'CustomUser',
    })
    list_display = (
        'title', 'shared_with', 'post_type',
        'created_by', 'created_on', 'modified_on', 'modified_by', 'mark_delete',
    )
    readonly_fields = ('transaction', 'nomination', 'cc_users', 'created_by', 'modified_by',)
    list_filter = ('priority', 'mark_delete',)
    # search_fields = ('organization__name',)

    formfield_overrides = {
        # Make many to many field user FilteredSelectMultiple widget instead of the default
        models.ManyToManyField: {
            "widget": FilteredSelectMultiple("", is_stacked=False)
        }
    }


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('content', 'parent', 'created_by', 'created_on', 'post')
    readonly_fields = ('created_by', 'modified_by', )


@admin.register(PostLiked)
class PostLikedAdmin(admin.ModelAdmin):
    list_display = ('created_by', 'created_on', 'post',)
    readonly_fields = ('created_by',)


@admin.register(PollsAnswer)
class PollsAnswerAdmin(admin.ModelAdmin):
    list_display = ('question', 'answer_text', 'votes', 'get_voters')


@admin.register(FlagPost)
class FlagPostAdmin(admin.ModelAdmin):
    list_display = ('post', 'flagger', 'notes', 'accepted', 'notified')
    readonly_fields = ('flagger',)


@admin.register(ECardCategory)
class ECardCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization')


@admin.register(ECard)
class ECardAdmin(admin.ModelAdmin):
    list_display = ('category', 'image')


@admin.register(PostReportAbuse)
class PostReportAbuseAdmin(admin.ModelAdmin):
    list_display = ('post', 'user', 'is_active')


@admin.register(Images)
class ImagesAdmin(admin.ModelAdmin):
    list_display = ('post', 'image')
