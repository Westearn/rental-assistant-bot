from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Awaitable, Dict, Any


class AuthMiddleware(BaseMiddleware):
    def __init__(self, allowed_users: list[int]):
        self.allowed_users = allowed_users

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ):
        if event.from_user.id not in self.allowed_users:
            await event.answer("⛔ У вас нет доступа к этому боту")
            return

        return await handler(event, data)