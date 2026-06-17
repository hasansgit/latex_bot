import re


def format_latex(text: str) -> str:
    text = text.strip()

    # Если пользователь уже сам использует нативный блок Telegram, не трогаем
    if "```math" in text:
        return text

    # Если есть явные теги $$...$$ или \[ ... \] — заменяем их на блок math
    if "$$" in text or r"\[" in text:
        text = re.sub(r"\$\$(.*?)\$\$", r"```math\n\1\n```", text, flags=re.DOTALL)
        text = re.sub(r"\\\[(.*?)\\\]", r"```math\n\1\n```", text, flags=re.DOTALL)
        return text

    # Если никаких тегов нет, считаем, что весь текст — это одна большая формула
    return f"```math\n{text}\n```"
