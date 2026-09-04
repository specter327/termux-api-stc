from .core.command import Command
_ENGINES=Command("termux-tts-engines")
_SPEAK=Command("termux-tts-speak")
def engines(*, timeout: float | None=15.0):
    return _ENGINES.json(timeout=timeout)
async def engines_async(*, timeout: float | None=15.0):
    return await _ENGINES.json_async(timeout=timeout)
def speak(text: str, *, timeout: float | None=120.0) -> str:
    return _SPEAK.text(input=text.encode("utf-8"), timeout=timeout)
async def speak_async(text: str, *, timeout: float | None=120.0) -> str:
    return await _SPEAK.text_async(input=text.encode("utf-8"), timeout=timeout)
