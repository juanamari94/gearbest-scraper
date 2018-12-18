"""
Authors: Juan Amari, François Oren Chikli

Main file for the parser unit tests.
"""

from unittest.mock import MagicMock

import pytest
from bs4 import Tag

from gearbest_scraping.gearbest_parser import GearbestParser


def generate_get_text_mock(text):
    cls_ = Tag(name="something")
    cls_.get_text = MagicMock(return_value=text)
    return cls_


@pytest.mark.parametrize("test_input,locale,expected", [
    ("$267.83", "$", ('267.83', '$')),
    ("267.83", "$", ('267.83', '$')),
    ("267", "$", ("267", "$")),
    ("", "", (None, None)),
    (None, None, (None, None))
])
def test_gearbest_price_parsing(test_input, locale, expected):
    result = GearbestParser.parse_price(test_input, locale)
    assert result == expected


@pytest.mark.parametrize("test_input,expected", [
    (generate_get_text_mock("$267.83"), {"price": 267.83, "currency_type": "$"}),
    (generate_get_text_mock("268.83"), {"price": 268.83, "currency_type": "$"}),
    (None, {})
])
def test_gearbest_parse_price_element(test_input, expected):
    item_dict = {}
    GearbestParser._parse_price_element(test_input, item_dict)
    assert item_dict == expected