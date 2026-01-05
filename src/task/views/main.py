from adrf.requests import AsyncRequest
from adrf.viewsets import ViewSet
from rest_framework import status
from rest_framework.response import Response

from common.models import Category
from domain.schemas.task.common import StatusRetriveDTO, SprintRetriveDTO, TagRetrieveDTO, CategoryRetriveDTO
from infrastructure.comon.authetication import AsyncAuthentication
from infrastructure.comon.login_decorator import login_required
from task.models import Status, Sprint, Tag


class TaskAsyncViewSet(ViewSet):
    authentication_classes = [AsyncAuthentication]

    @login_required
    async def creation_page_info(
        self,
        request: AsyncRequest,
    ):
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        statuses = Status.objects.all()
        sprints = Sprint.objects.all()
        tags = Tag.objects.all()
        categories = Category.objects.filter(user_id=user.id)

        statuses = [
            StatusRetriveDTO.model_validate(item).model_dump()
            async for item in statuses
        ]
        sprints = [
            SprintRetriveDTO.model_validate(item).model_dump()
            async for item in sprints
        ]
        tags = [
            TagRetrieveDTO.model_validate(item).model_dump()
            async for item in tags
        ]
        categories = [
            CategoryRetriveDTO.model_validate(item).model_dump()
            async for item in categories
        ]

        return Response(data={
            'statuses': statuses,
            'sprints': sprints,
            'tags': tags,
            'categories': categories,
        })