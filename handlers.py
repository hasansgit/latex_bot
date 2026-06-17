import hashlib
import aiohttp
from aiogram import Router, F, Bot
from aiogram.types import Message, InlineQuery
from aiogram.filters import CommandStart
from utils import format_latex

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
# ... existing code ...
        "Пиши мне формулы напрямую или используй инлайн: `@твой_бот \int x dx`.\n"
        "Если хочешь смешать текст и математику, оборачивай формулы в `$$...$$`."
    )

@router.message(F.text)
async def handle_private_message(message: Message, bot: Bot):
    formatted_text = format_latex(message.text)
    
    # Используем новый метод sendRichMessage (Bot API 10.1+) для нативного рендера математики
    url = f"https://api.telegram.org/bot{bot.token}/sendRichMessage"
    payload = {
        "chat_id": message.chat.id,
        "rich_message": {
            "markdown": formatted_text
        }
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            data = await resp.json()
            if not data.get("ok"):
                # Фолбэк, если синтаксис формулы неверен или клиент не поддерживает
                fallback_text = f"```math\n{message.text}\n```"
                await message.answer(fallback_text, parse_mode="MarkdownV2")

@router.inline_query()
async def handle_inline_query(inline_query: InlineQuery, bot: Bot):
    query_text = inline_query.query.strip()
    
    if not query_text:
        await inline_query.answer([])
        return

    formatted_text = format_latex(query_text)
    result_id = hashlib.md5(query_text.encode()).hexdigest()

    # Для инлайн запроса используем сырой HTTP-запрос, чтобы избежать проблем с типами aiogram 
    # и передать новый InputRichMessageContent (Bot API 10.1+)
    url = f"https://api.telegram.org/bot{bot.token}/answerInlineQuery"
    payload = {
        "inline_query_id": inline_query.id,
        "results": [
            {
                "type": "article",
                "id": result_id,
                "title": "Отправить LaTeX",
                "description": query_text[:50] + ("..." if len(query_text) > 50 else ""),
                "input_message_content": {
                    "rich_message": {
                        "markdown": formatted_text
                    }
                }
            }
        ],
        "cache_time": 1,
        "is_personal": True
    }
    
    async with aiohttp.ClientSession() as session:
        await session.post(url, json=payload)
