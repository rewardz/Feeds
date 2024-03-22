from __future__ import division, print_function, unicode_literals

from django.conf import settings

from rest_framework.pagination import PageNumberPagination


class FeedsResultsSetPagination(PageNumberPagination):
    try:
        page_size = settings.FEEDS_PAGE_SIZE
    except AttributeError as ae:
        page_size = 10
    page_size = page_size
    page_size_query_param = 'page'
    max_page_size = 500

    def get_page_size(self, request):
        try:
            page_size = request.GET.get("page_size")
            if not page_size:
                page_size = settings.FEEDS_PAGE_SIZE
        except AttributeError as ae:
            page_size = 10
        return page_size


class FeedsCommentsSetPagination(PageNumberPagination):
    page_size = 1000
    page_size_query_param = 'pageSize'
    max_page_size = 1000
