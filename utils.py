import re


def format_latex(text: str) -> str:
    text = text.strip()

    # Если в тексте ВООБЩЕ нет математических тегов ($$, \[, $),
    # значит юзер прислал просто голую формулу (например: \mathbb{R}).
    # Оборачиваем её целиком, чтобы Telegram понял, что это математика.
    if not re.search(r"(\$\$|\\\[|\$|\\\()", text):
        text = f"$${text}$$"

    # Разбиваем текст на куски: обычный текст - математика - обычный текст
    math_pattern = r"(\$\$.*?\$\$|\\\[.*?\\\]|\$.*?\$|\\\(.*?\\\))"
    parts = re.split(math_pattern, text, flags=re.DOTALL)

    result = []
    for part in parts:
        if not part:
            continue

        # Обязательно экранируем HTML-символы, чтобы Telegram API не ругался на знаки < и >
        part_escaped = (
            part.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        )

        if re.match(math_pattern, part, flags=re.DOTALL):
            # Если это кусок с математикой - оставляем его как есть!
            # Telegram получит $$...$$ и сам всё красиво отрендерит на экране телефона/ПК.
            result.append(part_escaped)
        else:
            # Если это обычный текст, конвертируем привычный Markdown в HTML
            # Жирный: **текст**
            part_escaped = re.sub(
                r"\*\*(.*?)\*\*", r"<b>\1</b>", part_escaped, flags=re.DOTALL
            )
            # Курсив: __текст__
            part_escaped = re.sub(
                r"__(.*?)__", r"<i>\1</i>", part_escaped, flags=re.DOTALL
            )
            # Зачеркнутый: ~~текст~~
            part_escaped = re.sub(
                r"~~(.*?)~~", r"<s>\1</s>", part_escaped, flags=re.DOTALL
            )
            # Моноширинный: `текст` (одинарные кавычки)
            part_escaped = re.sub(
                r"`(.*?)`", r"<code>\1</code>", part_escaped, flags=re.DOTALL
            )

            result.append(part_escaped)

    return "".join(result)
