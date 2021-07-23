

from django.conf import settings

from rest_framework.pagination import PageNumberPagination


class FeedsResultsSetPagination(PageNumberPagination):
    try:
        page_size = settings.FEEDS_PAGE_SIZE
    except AttributeError as ae:
        page_size = 20
    page_size = page_size
    page_size_query_param = 'page'
    max_page_size = 500

    def get_page_size(self, request):
        try:
            page_size = settings.FEEDS_PAGE_SIZE
        except AttributeError as ae:
            page_size = 20
        return page_size
