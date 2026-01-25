from django.urls import path

from task.views.main import TaskAsyncViewSet

urlpaterns = [
    path('creating/', TaskAsyncViewSet.as_view({
        'get': 'creation_page_info',
        'post': 'create',
    })),
    path('<int:task_id>/updating/', TaskAsyncViewSet.as_view({
        'patch': 'update',
    })),
    path('<int:task_id>/subtasks/<int:subtask_id>/completed/', TaskAsyncViewSet.as_view({
        'patch': 'update_subtask_completed',
    })),
    path('canban/', TaskAsyncViewSet.as_view({
        'get': 'get_canaban_table',
    })),
    path('<int:task_id>/status/', TaskAsyncViewSet.as_view({
        'patch': 'update_status',
    })),
path('<int:task_id>/view/', TaskAsyncViewSet.as_view({
        'get': 'retrive',
    })),
    path('<int:task_id>/comments/', TaskAsyncViewSet.as_view({
        'get': 'list_comments',
        'post': 'create_comment',
    })),
    path('<int:task_id>/history/', TaskAsyncViewSet.as_view({
        'get': 'list_history',
    })),
]
