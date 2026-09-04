from .core.command import Command
_GET = Command("termux-clipboard-get")
_SET = Command("termux-clipboard-set")

def get(*, timeout: float | None=15.0) -> str:
    return _GET.text(timeout=timeout)

async def get_async(*, timeout: float | None=15.0) -> str:
    return await _GET.text_async(timeout=timeout)

def set(text: str, *, timeout: float | None=15.0) -> str:
    return _SET.text(input=text.encode("utf-8"), timeout=timeout)

async def set_async(text: str, *, timeout: float | None=15.0) -> str:
    return await _SET.text_async(input=text.encode("utf-8"), timeout=timeout)
