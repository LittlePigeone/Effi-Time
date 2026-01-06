from django.urls import path

from task.views.main import TaskAsyncViewSet

urlpaterns = [
    path('creating/', TaskAsyncViewSet.as_view({
        'get': 'creation_page_info',
        'post': 'create',
    })),
]