import logging

from adrf.requests import AsyncRequest
from adrf.viewsets import ViewSet
from rest_framework import status
from rest_framework.response import Response

from common.models import Category
from domain.schemas.task.common import StatusRetriveDTO, SprintRetriveDTO, TagRetrieveDTO, CategoryRetriveDTO, \
    SubtaskBulkCreateDTO
from domain.schemas.task.error import TaskCreateErrorDTO
from domain.schemas.task.main import TaskCreateDTO, TaskRetrieveDTO
from infrastructure.comon.authetication import AsyncAuthentication
from infrastructure.comon.login_decorator import login_required
from task.models import Status, Sprint, Tag, Task, Subtask


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

    async def check_timing(
        self,
        task_create_dto,
        user_id: int,
    ) -> TaskCreateErrorDTO:
        error_text = 'Нельзя создать задачу на этол время'
        task_create_error_dto = TaskCreateErrorDTO()

        if task_create_dto.started_at > task_create_dto.finished_at:
            task_create_error_dto.can_create = False
            task_create_error_dto = 'Время начала не может быть больше времени окончания!'
            return task_create_error_dto

        prev_task = (
            await Task.objects
            .filter(finished_at__lt=task_create_dto.finished_at, user_id=user_id)
            .order_by('finished_at').alast()
        )

        if prev_task and prev_task.started_at < task_create_dto.finished_at:
            task_create_error_dto.can_create = False
            task_create_error_dto = error_text
            task_create_error_dto.available_start = prev_task.finished_at
            return task_create_error_dto

        next_task = (
            await Task.objects
            .filter(started_at__gt=task_create_dto.started_at, user_id=user_id)
            .order_by('started_at').afirst()
        )
        if next_task and task_create_dto.started_at > next_task.finished_at:
            task_create_error_dto.can_create = False
            task_create_error_dto = error_text
            task_create_error_dto.available_end =  next_task.started_at
            return task_create_error_dto

        return task_create_error_dto

    @login_required
    async def create(self,  request: AsyncRequest):
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        data = request.data
        try:
            task_create_dto = TaskCreateDTO(**data)
            subtask_bulk_crreate_dto = SubtaskBulkCreateDTO(**data)
            tags = data.get("tags", [])

            task_create_error_dto = await self.check_timing(
                task_create_dto=task_create_dto,
                user_id=user.id
            )
            if not task_create_error_dto.can_create:
                if task_create_dto.availbe_start:
                    task_create_error_dto.detail += (
                        f'\n Дата и время начала доступна с '
                        f'{task_create_error_dto.available_start}'
                    )
                if task_create_dto.availbe_end:
                    task_create_error_dto.detail += (
                        f'\n Дата и время окончания доступна до '
                        f'{task_create_error_dto.available_end}'
                    )
                return Response(
                    data={
                        'detail': task_create_error_dto.detail,
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            task = await Task.objects.acreate(
                **task_create_dto.model_dump(),
                user_id=user.id,
            )
            task.tags.aset(tags)

            subtask_objects = []
            for subtask in subtask_bulk_crreate_dto.subtasks:
                subtask_objects = [
                    Subtask(**subtask.model_dump(), task_id=task.id)
                ]
            await Subtask.objects.abulk_create_dto(subtask_objects)

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
            task = await Task.objects.aget(id=task_id, user_id=user.id)
        except Task.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        task_retrive_dto = TaskRetrieveDTO.model_validate(task)

        return Response(data=task_retrive_dto.model_dump())