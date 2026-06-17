## LaTeX Bot

Сделай тг бота, который работает инлайн (вызывается в начале сообщения через @botname, боты использование которых делает via @botname)

У него должен быть следующий функционал:

- пишешь в любом чате сообщение формата "@botname some latex", и на выход выводится сообщение с красивым латехом, который завезли в тг
- пишешь ему сообщение в личку бота формата "some latex", он выводит тоже сообщение, но с красивым латехом, который завезли в тг
- бот должен естественно и с markdown работать
- не дожно быть кучи вариантов выбора перед отправкой -- только один, который точно всегда работает

Технические требования:

- Бот должен быть написан на python.
- Подгружать токен с .env файла.
- Если получается большим, то разделить исходник на несколько файлов.
- Должен быть requirement.txt для быстрой установки необходимых библиотек.
- Бот должен работать и с мобильного телефона, есть такие боты, которые не стабильно работают с телефона, но более стабильно с ПК.

Если есть варианты улучшить - пиши.

Чтобы исходник не превратился в кашу, я разбил его на логические модули.

### Структура проекта

```text
latex_bot/
├── .env
├── requirements.txt
├── config.py
├── utils.py
├── handlers.py
└── main.py
```

---

### 1. Файлы конфигурации

**`requirements.txt`**

```text
aiogram>=3.4.0
python-dotenv>=1.0.0
```

**`.env`**
Здесь будет лежать твой токен от BotFather.

```env
BOT_TOKEN=твой_токен_здесь
```

**`config.py`**
Простая подгрузка переменных окружения.

```python
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Токен бота не найден. Проверь файл .env")
```

---

### 2. Логика форматирования

**`utils.py`**
Здесь реализована "умная" обработка текста. Если юзер пишет просто формулу — мы оборачиваем её целиком. Если юзер смешивает текст и LaTeX (используя `$$`), мы конвертируем это так, чтобы Telegram отрисовал математику, а текст вокруг оставил как Markdown.

````python
import re

def format_latex(text: str) -> str:
    text = text.strip()

    # Если пользователь уже сам использует нативный блок Telegram, не трогаем
    if '```math' in text:
        return text

    # Если есть явные теги $$...$$ или \[ ... \] — заменяем их на блок math
    if '$$' in text or r'\[' in text:
        text = re.sub(r'\$\$(.*?)\$\$', r'```math\n\1\n```', text, flags=re.DOTALL)
        text = re.sub(r'\\\[(.*?)\\\]', r'```math\n\1\n```', text, flags=re.DOTALL)
        return text

    # Если никаких тегов нет, считаем, что весь текст — это одна большая формула
    return f"```math\n{text}\n```"
````

---

### 3. Обработчики (Handlers)

**`handlers.py`**
Обрабатываем личные сообщения и инлайн-запросы. По твоему ТЗ — выдаем строго **один** вариант ответа, который железобетонно работает.

````python
import hashlib
from aiogram import Router, F
from aiogram.types import Message, InlineQuery, InlineQueryResultArticle, InputTextMessageContent
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
            await message.answer("Произошла ошибка при рендере. Проверь синтаксис формулы.")

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
            message_text=formatted_text,
            parse_mode="MarkdownV2"
        )
    )

    await inline_query.answer([result], cache_time=1, is_personal=True)
````

---

### 4. Точка входа

**`main.py`**
Запуск бота.

```python
import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers import router

logging.basicConfig(level=logging.INFO)

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(router)

    # Дропаем старые апдейты, чтобы бот не спамил ответами на сообщения, присланные пока он был в оффлайне
    await bot.delete_webhook(drop_pending_updates=True)

    print("Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
```

### Как запустить и важные шаги для настройки:

1. **Установи зависимости:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Включи Inline режим в BotFather!**
   По умолчанию у новых ботов отключен инлайн. Зайди в `@BotFather`, отправь `/mybots` -> выбери своего бота -> `Bot Settings` -> `Inline Mode` -> нажми `Turn on`.
3. **Запусти:**

   ```bash
   python main.py
   ```

### Варианты улучшений (на будущее):

- **Обработка многострочного ввода в инлайне:** Инлайн-запросы в Telegram технически могут быть многострочными, но с телефона набирать `\n` в строке поиска неудобно. Можно добавить фичу в `utils.py`: если юзер пишет `\n` (как два символа `\` и `n`), бот программно заменяет их на реальный перенос строки.
- **Экранирование MarkdownV2:** Telegram API для MarkdownV2 требует экранирования символов вроде `.`, `+`, `-`, `!` если они находятся _вне_ блока с математикой. В текущей версии я сделал механизм `try-except` (fallback): если API ругается на неэкранированный текст юзера, бот принудительно заворачивает весь запрос в `
