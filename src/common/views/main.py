from adrf.requests import AsyncRequest
from adrf.viewsets import ViewSet
from rest_framework import status
from rest_framework.response import Response

from common.models import Category
from domain.schemas.task.common import CategoryRetriveDTO, CategoryCreateDTO


class CategoryAsyncViewSet(ViewSet):
    async def get(
        self,
        request: AsyncRequest,
    ):
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)


        categories = Category.objects.filter(user_id=user.id)
        category_list = [
            CategoryRetriveDTO.model_validate(category).model_dump()
            async for category in categories
        ]

        return Response(data=category_list)

    async def create(
        self,
        request: AsyncRequest,
    ):
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        try:
            category_dto = CategoryCreateDTO(**request.data)
            category = await Category.objects.acreate(
                name=category_dto.name,
                user=user
            )
            return Response(
                data=CategoryRetriveDTO.model_validate(category).model_dump(),
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)

