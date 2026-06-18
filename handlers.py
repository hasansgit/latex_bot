import hashlib
from aiogram import Router, F
from aiogram.types import (
    Message,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)
from aiogram.filters import CommandStart
from utils import format_latex

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Я рендерю нативный LaTeX в Telegram.\n\n"
        "Просто отправь мне формулу (например, <code>\\int x dx</code>).\n"
        "Я поддерживаю смешивание текста и математики (оборачивай формулы в <code>$$...$$</code>), "
        "а также Markdown: **жирный** или __курсив__.\n\n"
        "Ещё я работаю в инлайн-режиме в любом чате: <code>@твой_бот \\mathbb{R}</code>",
        parse_mode="HTML",
    )


@router.message(F.text)
async def handle_private_message(message: Message):
    formatted_text = format_latex(message.text)
    try:
        # Отправляем в HTML режиме (он не ломает LaTeX слэши!)
        await message.answer(formatted_text, parse_mode="HTML")
    except Exception as e:
        # Безотказный фоллбэк: если что-то пошло не так, кидаем сырой текст.
        # Математика всё равно отрендерится клиентом!
        print(f"Ошибка парсинга HTML: {e}")
        await message.answer(message.text)


@router.inline_query()
async def handle_inline_query(inline_query: InlineQuery):
    query_text = inline_query.query.strip()

    if not query_text:
        await inline_query.answer([])
        return

    formatted_text = format_latex(query_text)

    # Генерируем уникальный ID для результата на основе запроса
    result_id = hashlib.md5(query_text.encode()).hexdigest()

    # По ТЗ: строго один вариант выбора, который точно всегда работает
    result = InlineQueryResultArticle(
        id=result_id,
        title="Отправить LaTeX",
        description=query_text[:50] + ("..." if len(query_text) > 50 else ""),
        input_message_content=InputTextMessageContent(
            message_text=formatted_text, parse_mode="HTML"
        ),
    )

    await inline_query.answer([result], cache_time=1, is_personal=True)

