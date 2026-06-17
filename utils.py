import re


def format_latex(text: str) -> str:
    text = text.strip()

    # В новом Bot API 10.1 (Rich Messages) Telegram нативно поддерживает
    # LaTeX формулы внутри тегов $$...$$ или \[...\].

    # Если пользователь уже сам использует эти теги, не трогаем
    if "$$" in text or r"\[" in text:
        return text

    # Если никаких тегов нет, считаем, что весь текст — это одна большая формула
    return f"$${text}$$"

