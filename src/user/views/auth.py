from adrf.requests import AsyncRequest
from adrf.viewsets import ViewSet
from asgiref.sync import sync_to_async
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from rest_framework import status
from rest_framework.response import Response

from user.models import User


class AuthAsyncViewSet(ViewSet):

    async def page(
            self,
            request: AsyncRequest,
    ):
        return render(
            request=request,
            template_name='user/login.html',
            context={
                'title': 'Авторизация',
            },
        )

    async def login(
        self,
        request: AsyncRequest,
    ):
        data = request.data

        try:
            user = await User.objects.aget(username=data['username'])
        except Exception:
            return Response(data={
                'detail': 'Нет такого пользователя!'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = await sync_to_async(authenticate)(
                request=request,
                username=user.username,
                password=data['password'],
            )
            if user is None:
                raise Exception
        except Exception:
            return Response(data={
                'detail': 'Неверный пароль!'
            }, status=status.HTTP_400_BAD_REQUEST)

        await sync_to_async(login)(request, user)

        return Response(data={}, status=status.HTTP_204_NO_CONTENT)

    async def logout(
        self,
        request: AsyncRequest,
    ):
        await sync_to_async(logout)(request)

        return redirect(reverse_lazy('login'))