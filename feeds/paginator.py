from __future__ import division, print_function, unicode_literals

from django.conf import settings
from django.utils import six

from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.compat import OrderedDict
from rest_framework.exceptions import NotFound
from rest_framework.utils.urls import (
    replace_query_param, remove_query_param
)


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
            page_size = request.GET.get("page_size")
            if not page_size:
                page_size = settings.FEEDS_PAGE_SIZE
        except AttributeError as ae:
            page_size = 20
        return page_size

    def get_next_link(self):
        url = self.request.build_absolute_uri()
        current_page_number = int(self.request.query_params.get(self.page_query_param, 1))
        page_number = current_page_number + 1
        return replace_query_param(url, self.page_query_param, page_number)

    def get_previous_link(self):
        current_page_number = int(self.request.query_params.get(self.page_query_param, 1))
        page_number = current_page_number - 1
        if page_number == 0:
            return None
        url = self.request.build_absolute_uri()
        if page_number == 1:
            return remove_query_param(url, self.page_query_param)
        return replace_query_param(url, self.page_query_param, page_number)

    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ]))

    def paginate_queryset(self, queryset, request, view=None):
        """
        Modified from DRF. Skip count() call.
        """
        self._handle_backwards_compat(view)

        page_size = self.get_page_size(request)
        if not page_size:
            return None

        try:
            page_number = int(request.query_params.get(self.page_query_param, 1))
        except ValueError as exc:
            msg = self.invalid_page_message.format(
                page_number=page_number, message=six.text_type(exc)
            )
            raise NotFound(msg)

        result = queryset[page_size * (page_number - 1):page_size * page_number]

        if len(result) == 0:
            msg = self.invalid_page_message.format(
                page_number=page_number, message="Empty page"
            )
            raise NotFound(msg)

        self.request = request
        return list(result)


class FeedsCommentsSetPagination(PageNumberPagination):
    page_size = 1000
    page_size_query_param = 'pageSize'
    max_page_size = 1000
