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
        "Пиши мне формулы напрямую или используй инлайн: `@твой_бот \int x dx`.\n"
        "Если хочешь смешать текст (Markdown) и математику, оборачивай формулы в `$$...$$`."
    )


@router.message(F.text)
async def handle_private_message(message: Message):
    formatted_text = format_latex(message.text)
    try:
        # Пытаемся отправить с MarkdownV2 (чтобы работал жирный шрифт, курсив и т.д.)
        await message.answer(formatted_text, parse_mode="MarkdownV2")
    except Exception:
        # MarkdownV2 очень строг к экранированию спецсимволов вне блоков кода (например, знаков +, -, .).
        # Если юзер ошибся в Markdown, мы фолбечимся: оборачиваем вообще всё в math, чтобы не было ошибки.
        fallback_text = f"```math\n{message.text}\n```"
        try:
            await message.answer(fallback_text, parse_mode="MarkdownV2")
        except Exception:
            await message.answer(
                "Произошла ошибка при рендере. Проверь синтаксис формулы."
            )


@router.inline_query()
async def handle_inline_query(inline_query: InlineQuery):
    query_text = inline_query.query.strip()

    if not query_text:
        await inline_query.answer([])
        return

    formatted_text = format_latex(query_text)

    # Генерируем уникальный ID для результата на основе запроса
    result_id = hashlib.md5(query_text.encode()).hexdigest()

    # Строго один вариант выбора
    result = InlineQueryResultArticle(
        id=result_id,
        title="Отправить LaTeX",
        description=query_text[:50] + ("..." if len(query_text) > 50 else ""),
        input_message_content=InputTextMessageContent(
            message_text=formatted_text, parse_mode="MarkdownV2"
        ),
    )

    await inline_query.answer([result], cache_time=1, is_personal=True)
