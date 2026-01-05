from django.urls import path

from common.views.main import CategoryAsyncViewSet

urlpatterns = [
    path('category/list/', CategoryAsyncViewSet.as_view({
        'get': 'get',
    })),
]