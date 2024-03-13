from __future__ import division, print_function, unicode_literals

from django.conf import settings
from django.utils import six
from rest_framework.compat import OrderedDict
from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.utils.urls import remove_query_param, replace_query_param


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


class OrganizationRecognitionsPagination(FeedsResultsSetPagination):

    def get_next_link(self):
        url = self.request.build_absolute_uri()
        page_number = self.current_page_number + 1
        return replace_query_param(url, self.page_query_param, page_number)

    def get_previous_link(self):
        page_number = self.current_page_number - 1
        if page_number == 0:
            return None
        url = self.request.build_absolute_uri()
        if page_number == 1:
            return remove_query_param(url, self.page_query_param)
        return replace_query_param(url, self.page_query_param, page_number)

    def get_paginated_response(self, data):
        if len(data) == 0:
            if self.current_page_number == 1:
                return Response(OrderedDict([
                    ('count', 0),
                    ('next', None),
                    ('previous', None),
                    ('results', [])
                ]))
            else:
                msg = self.invalid_page_message.format(
                    page_number=self.current_page_number, message="Empty page"
                )
                raise NotFound(msg)

        return Response(OrderedDict([
            ('count', 1000),  # hard coded for now cause Android need it to be greater than 0 when not empty
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
            self.current_page_number = page_number
        except ValueError as exc:
            msg = self.invalid_page_message.format(
                page_number=page_number, message=six.text_type(exc)
            )
            raise NotFound(msg)

        result = queryset[page_size * (page_number - 1):page_size * page_number]

        self.request = request
        return list(result)


class FeedsCommentsSetPagination(PageNumberPagination):
    page_size = 1000
    page_size_query_param = 'pageSize'
    max_page_size = 1000
