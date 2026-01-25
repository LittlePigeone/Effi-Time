from adrf.requests import AsyncRequest
from adrf.viewsets import ViewSet
from django.shortcuts import render

from infrastructure.comon.authetication import AsyncAuthentication
from infrastructure.comon.login_decorator import login_required


class TemplatesAsyncViewsSet(ViewSet):
    authentication_classes = [AsyncAuthentication]

    @login_required
    async def get_category_page(
        self,
        request: AsyncRequest,
    ):
        context = {
            'title': 'Сферы жизни',
            'active_chapter': 'areas_of_life',
        }

        return render(
            request,
            template_name='category.html',
            context=context,
        )

    @login_required
    async def get_calendar_page(
        self,
        request: AsyncRequest,
    ):
        context = {
            'title': 'Календарь',
            'active_chapter': 'calendar',
        }

        return render(
            request,
            template_name='calendar.html',
            context=context,
        )

    @login_required
    async def get_canban_page(
        self,
        request: AsyncRequest,
    ):
        context = {
            'title': 'Канбан',
            'active_chapter': 'canban',
        }

        return render(
            request,
            template_name='canban.html',
            context=context,
        )