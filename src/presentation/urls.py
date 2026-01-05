from django.urls import path, include
from .page.urls import urlpaterns as templates_urls
from .user.auth import urlpatterns as auth_urls
from .common.urls import urlpatterns as common_urls
from .task.urls import urlpaterns as task_urls


urlpatterns = [
    path('', include(auth_urls)),
    path("", include(templates_urls)),
    path("", include(common_urls)),
    path('task/', include(task_urls))
]