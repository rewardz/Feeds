from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.db import models

from ajax_select import make_ajax_form
from django.conf import settings
from django.utils.module_loading import import_string

from feeds.models import (
    Comment, ECard, ECardCategory, FlagPost, Images, PollsAnswer, Post, PostLiked, PostReportAbuse)

Organization = import_string(settings.ORGANIZATION_MODEL)
CustomUser = settings.AUTH_USER_MODEL


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
    list_filter = ('priority', 'mark_delete', 'organizations')

    formfield_overrides = {
        # Make many to many field user FilteredSelectMultiple widget instead of the default
        models.ManyToManyField: {
            "widget": FilteredSelectMultiple("", is_stacked=False)
        }
    }


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('content', 'parent', 'created_by', 'created_on', 'post', 'mark_delete')
    readonly_fields = ('created_by', 'modified_by', )

    def get_form(self, request, obj=None, **kwargs):
        form = super(CommentAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['post'].queryset = Post.objects.order_by("title")
        return form


@admin.register(PostLiked)
class PostLikedAdmin(admin.ModelAdmin):
    list_display = ('created_by', 'created_on', 'post',)
    readonly_fields = ('created_by',)


@admin.register(PollsAnswer)
class PollsAnswerAdmin(admin.ModelAdmin):
    list_display = ('question', 'answer_text', 'votes', 'get_voters')

    def get_form(self, request, obj=None, **kwargs):
        form = super(PollsAnswerAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['question'].queryset = Post.objects.order_by("title")
        return form


@admin.register(FlagPost)
class FlagPostAdmin(admin.ModelAdmin):
    list_display = ('post', 'flagger', 'notes', 'accepted', 'notified')
    readonly_fields = ('flagger',)

    def get_form(self, request, obj=None, **kwargs):
        form = super(FlagPostAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['post'].queryset = Post.objects.order_by("title")
        return form


@admin.register(ECardCategory)
class ECardCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization')

    def get_form(self, request, obj=None, **kwargs):
        form = super(ECardCategoryAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['organization'].queryset = Organization.objects.order_by("name")
        return form


@admin.register(ECard)
class ECardAdmin(admin.ModelAdmin):
    list_display = ('category', 'image')

    def get_form(self, request, obj=None, **kwargs):
        form = super(ECardAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['category'].queryset = ECardCategory.objects.order_by("organization__name", "name")
        return form


@admin.register(PostReportAbuse)
class PostReportAbuseAdmin(admin.ModelAdmin):
    list_display = ('post', 'user', 'is_active')

    form = make_ajax_form(Post, {
        'user': 'CustomUser',
    })

    def get_form(self, request, obj=None, **kwargs):
        form = super(PostReportAbuseAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['post'].queryset = Post.objects.order_by("title")
        form.base_fields['user'].queryset = CustomUser.objects.order_by("email")
        return form


@admin.register(Images)
class ImagesAdmin(admin.ModelAdmin):
    list_display = ('post', 'image')

    def get_form(self, request, obj=None, **kwargs):
        form = super(ImagesAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['post'].queryset = Post.objects.order_by("title")
        return form
