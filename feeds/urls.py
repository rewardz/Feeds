from django.conf.urls import include, url

from rest_framework import routers

from .views import PostViewSet, ImagesView

router = routers.DefaultRouter()
router.register(r'posts', PostViewSet, base_name='posts')

api_urls = router.urls

urlpatterns = [
    url(r'^api/', include(api_urls)),
    url(r'^api/images/', ImagesView.as_view()),
]
