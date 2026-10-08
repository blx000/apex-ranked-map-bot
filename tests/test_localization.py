from __future__ import annotations

import logging

import pytest

from apex_bot.localization import localized_map_name


@pytest.mark.parametrize(
    ("english", "russian"),
    [
        ("Kings Canyon", "Каньон Кингс"),
        ("E-District", "Квартал Электро"),
        ("World's Edge", "Край света"),
        ("World’s Edge", "Край света"),
        ("Storm Point", "Место бури"),
        ("Olympus", "Олимп"),
        ("Broken Moon", "Расколотая луна"),
    ],
)
def test_official_map_translations(english: str, russian: str) -> None:
    assert localized_map_name(english) == f"{english} ({russian})"


def test_unknown_map_is_safe_and_logged(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING):
        result = localized_map_name("Brand New Map")

    assert result == "Brand New Map (перевод не добавлен)"
    assert "Missing Russian translation" in caplog.text

