from django.conf.urls import include, url

from rest_framework import routers

from .views import PostViewSet, ImagesDetailView

router = routers.DefaultRouter()
router.register(r'posts', PostViewSet, base_name='posts')

api_urls = router.urls

urlpatterns = [
    url(r'^api/', include(api_urls)),
    url(r'^api/images/(?P<pk>[0-9]+)/$', ImagesDetailView.as_view()),
]
