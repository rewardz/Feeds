from django.conf.urls import include, url

from ajax_select import urls as ajax_select_urls
from rest_framework import routers

from .views import CommentViewset, ECardCategoryViewSet, ECardViewSet, PostViewSet, ImagesDetailView, search_user,\
    UserFeedViewSet

router = routers.DefaultRouter()
router.register(r'posts', PostViewSet, base_name='posts')
router.register(r'comments', CommentViewset, base_name='comments')
router.register(r'ecard_category', ECardCategoryViewSet)
router.register(r'ecard', ECardViewSet)
router.register(r'user_feed', UserFeedViewSet, base_name="user_feed")

api_urls = router.urls

urlpatterns = [
    url(r'^api/', include(api_urls)),
    url(r'^api/images/(?P<pk>[0-9]+)/$', ImagesDetailView.as_view()),
    url(r'^api/search_users/', search_user),
    url(r'^ajax_select/', include(ajax_select_urls)),
]
