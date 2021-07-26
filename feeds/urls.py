from django.conf.urls import include, url

from rest_framework import routers

from .views import CommentViewset, PostViewSet, ImagesDetailView, search_user

router = routers.DefaultRouter()
router.register(r'posts', PostViewSet, basename='posts')
router.register(r'comments', CommentViewset, basename='comments')

api_urls = router.urls

app_name = "feeds"
urlpatterns = [
    url(r'^api/', include(api_urls)),
    url(r'^api/images/(?P<pk>[0-9]+)/$', ImagesDetailView.as_view()),
    url(r'^api/search_users/', search_user),
]
