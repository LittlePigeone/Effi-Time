import logging

from adrf.requests import AsyncRequest
from adrf.viewsets import ViewSet
from rest_framework import status
from rest_framework.response import Response

from common.models import Category
from domain.schemas.task.common import StatusRetriveDTO, SprintRetriveDTO, TagRetrieveDTO, CategoryRetriveDTO
from domain.schemas.task.main import TaskCreateDTO, TaskRetrieveDTO
from infrastructure.comon.authetication import AsyncAuthentication
from infrastructure.comon.login_decorator import login_required
from task.models import Status, Sprint, Tag, Task


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

    @login_required
    async def create(self,  request: AsyncRequest):
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        data = request.data
        try:
            task_create_dto = TaskCreateDTO(**data)

            task = await Task.objects.acreate(
                **task_create_dto.model_dump()
            )

            return Response(
                data={'id':  task.id},
                status=status.HTTP_201_CREATED
            )

        except Exception as exc:
            logging.error(exc)
            return Response(status=status.HTTP_400_BAD_REQUEST)

    @login_required
    async def retrive(
        self,
        request: AsyncRequest,
        task_id: int,
    ):
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        try:
            task = await Task.objects.aget(id=task_id)
        except Task.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        task_retrive_dto = TaskRetrieveDTO.model_validate(task)

        return Response(data=task_retrive_dto.model_dump())