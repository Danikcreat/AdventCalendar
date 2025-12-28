from typing import Optional

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

DEFAULT_MAINTENANCE_TEXT = "Извини, к сожалению, не могу сейчас ответить."


class MaintenanceMiddleware(BaseMiddleware):
    def __init__(self, enabled: bool, text: str = DEFAULT_MAINTENANCE_TEXT, photo_id: Optional[str] = None):
        self.enabled = enabled
        self.text = text
        self.photo_id = photo_id

    async def __call__(self, handler, event, data):
        if not self.enabled:
            return await handler(event, data)

        if isinstance(event, Message):
            if self.photo_id:
                await event.answer_photo(self.photo_id, caption=self.text)
            else:
                await event.answer(self.text)
            return

        if isinstance(event, CallbackQuery):
            if event.message:
                if self.photo_id:
                    await event.message.answer_photo(self.photo_id, caption=self.text)
                else:
                    await event.message.answer(self.text)
            await event.answer()
            return

        return
