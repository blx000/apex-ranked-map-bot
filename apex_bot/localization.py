from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

_MAP_TRANSLATIONS = {
    "kings canyon": "Каньон Кингс",
    "e-district": "Квартал Электро",
    "e district": "Квартал Электро",
    "district": "Квартал Электро",
    "world's edge": "Край света",
    "storm point": "Место бури",
    "olympus": "Олимп",
    "broken moon": "Расколотая луна",
}


def normalize_map_name(name: str) -> str:
    normalized = name.strip().replace("’", "'").replace("`", "'").casefold()
    return re.sub(r"\s+", " ", normalized)


def localized_map_name(name: str) -> str:
    translation = _MAP_TRANSLATIONS.get(normalize_map_name(name))
    if translation is None:
        logger.warning("Missing Russian translation for Apex map", extra={"map_name": name})
        translation = "перевод не добавлен"
    return f"{name} ({translation})"

