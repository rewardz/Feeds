from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.db import models

from news_feed.tests.profiles.models import CustomUser, Department, Organization


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'img', 'first_name', 'last_name', 'is_active', 'is_staff',
                    'organization', 'get_departments')


class DepartmentInline(admin.TabularInline):
    model = Department
    fields = ("name",)
    readonly_fields = ("slug",)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    inlines = (DepartmentInline,)
    formfield_overrides = {
        # Make many to many field user FilteredSelectMultiple widget instead of the default
        models.ManyToManyField: {
            "widget": FilteredSelectMultiple("", is_stacked=False)
        }
    }


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization')
    list_filter = ('organization',)
    search_fields = ('name',)
    # readonly_fields = ('slug',)
    prepopulated_fields = {"slug": ("name",)}

    formfield_overrides = {
        # Make many to many field user FilteredSelectMultiple widget instead of the default
        models.ManyToManyField: {
            "widget": FilteredSelectMultiple("", is_stacked=False)
        }
    }
