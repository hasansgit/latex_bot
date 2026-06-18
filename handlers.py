import aiohttp
import hashlib
from aiogram import Router, F
from aiogram.types import Message, InlineQuery
from aiogram.filters import CommandStart
from config import BOT_TOKEN

router = Router()


def format_math(text: str) -> str:
    text = text.strip()
    # Если юзер не обернул формулу в доллары сам, делаем это за него (по умолчанию блочная)
    if "$$" not in text and "\\[" not in text and "$" not in text and "\\(" not in text:
        return f"$${text}$$"
    return text


@router.message(CommandStart())
async def cmd_start(message: Message):
    # Прямой вызов новейшего API Telegram 10.1 (Rich Messages)
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendRichMessage"
    payload = {
        "chat_id": message.chat.id,
        "rich_message": {
            "markdown": "Привет! Я рендерю **нативный LaTeX** в Telegram.\n\nПросто отправь мне формулу (например, `\\int x dx`).\nЯ поддерживаю Markdown и математику: `$$...$$`.\nЕщё я работаю в инлайн-режиме: `@твой_бот \\mathbb{R}`"
        },
    }
    async with aiohttp.ClientSession() as session:
        await session.post(url, json=payload)


@router.message(F.text)
async def handle_private_message(message: Message):
    formatted = format_math(message.text)

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendRichMessage"
    payload = {
        "chat_id": message.chat.id,
        "rich_message": {
            # В режиме rich_message Telegram сам парсит $$ и превращает их в красивые формулы
            "markdown": formatted
        },
    }

    async with aiohttp.ClientSession() as session:
        resp = await session.post(url, json=payload)
        data = await resp.json()

        # Если случилась ошибка API (например, кривой Markdown), отправляем как есть
        if not data.get("ok"):
            await message.answer(f"Ошибка рендера. Сырой текст:\n{formatted}")


@router.inline_query()
async def handle_inline_query(inline_query: InlineQuery):
    query_text = inline_query.query.strip()
    if not query_text:
        return

    formatted = format_math(query_text)
    result_id = hashlib.md5(query_text.encode()).hexdigest()

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/answerInlineQuery"

    # Используем InputRichMessageContent для инлайна
    payload = {
        "inline_query_id": inline_query.id,
        "results": [
            {
                "type": "article",
                "id": result_id,
                "title": "Отправить красивый LaTeX",
                "description": query_text[:50],
                "input_message_content": {"rich_message": {"markdown": formatted}},
            }
        ],
        "cache_time": 1,
        "is_personal": True,
    }

    async with aiohttp.ClientSession() as session:
        resp = await session.post(url, json=payload)
        data = await resp.json()

        # Fallback: если инлайн еще не поддерживает Rich Messages на серверах ТГ
        if not data.get("ok"):
            fallback_payload = {
                "inline_query_id": inline_query.id,
                "results": [
                    {
                        "type": "article",
                        "id": result_id,
                        "title": "Отправить LaTeX (классический режим)",
                        "description": query_text[:50],
                        "input_message_content": {"message_text": formatted},
                    }
                ],
                "cache_time": 1,
                "is_personal": True,
            }
            await session.post(url, json=fallback_payload)

