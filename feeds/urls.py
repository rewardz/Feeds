from django.conf.urls import include, url

from rest_framework import routers

from .views import CommentViewset, PostViewSet, ImagesDetailView

router = routers.DefaultRouter()
router.register(r'posts', PostViewSet, base_name='posts')
router.register(r'comments', CommentViewset, base_name='comments')

api_urls = router.urls

urlpatterns = [
    url(r'^api/', include(api_urls)),
    url(r'^api/images/(?P<pk>[0-9]+)/$', ImagesDetailView.as_view()),
]
