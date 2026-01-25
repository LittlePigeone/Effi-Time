from adrf.requests import AsyncRequest
from asgiref.sync import sync_to_async
from rest_framework.authentication import BaseAuthentication

from user.models import User


class AsyncAuthentication(BaseAuthentication):
    async def authenticate(self, request: AsyncRequest):
        user_id = await sync_to_async(lambda: request.session.get('_auth_user_id'))()

        try:
            user = await User.objects.aget(pk=user_id)

            return user, None

        except User.DoesNotExist:
            return None

        except Exception:
            return None