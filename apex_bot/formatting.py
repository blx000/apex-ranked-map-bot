from __future__ import annotations

from html import escape

from apex_bot.localization import localized_map_name
from apex_bot.models import RankedRotation

ATTRIBUTION_URL = "https://apexlegendsstatus.com"


def format_duration(total_seconds: int) -> str:
    seconds = max(0, total_seconds)
    if seconds < 60:
        return "меньше минуты"
    total_minutes = seconds // 60
    hours, minutes = divmod(total_minutes, 60)
    if hours and minutes:
        return f"{hours} ч {minutes} мин"
    if hours:
        return f"{hours} ч"
    return f"{minutes} мин"


def format_rotation(rotation: RankedRotation, *, changed: bool = False) -> str:
    title = "🗺 <b>Карта в Ranked сменилась</b>" if changed else "🗺 <b>Текущая карта Ranked</b>"
    # Apostrophes are safe in Telegram text nodes. Keeping them unescaped also
    # avoids entities that Telegram's intentionally small HTML subset rejects.
    current = escape(localized_map_name(rotation.current.name), quote=False)
    next_map = escape(localized_map_name(rotation.next.name), quote=False)
    remaining = format_duration(rotation.remaining_seconds())
    return (
        f"{title}\n"
        f"Сейчас: <b>{current}</b>\n"
        f"Осталось: <b>{remaining}</b>\n"
        f"Следующая: <b>{next_map}</b>\n\n"
        f'<a href="{ATTRIBUTION_URL}">Data provided by Apex Legends Status</a>'
    )
