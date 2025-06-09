import sys
from pathlib import Path

import pytest
from utils.utils import decode_to_number

@pytest.mark.parametrize("input_str,expected_id", [
    ("11 bit studios", "1"),
    ("11 BIT STUDIOS", "1"),
])
def test_decode_to_number_with_fuzzy_name_returns_correct_id(input_str, expected_id):
    stock_id = {
        "1": "11 bit studios SA",
        "2": "Digital Network SA"
    }

    result = decode_to_number(
        input_str,
        ticker_to_number={},
        symbol_to_number={},
        stock_id=stock_id
    )

    assert result == expected_id

@pytest.mark.parametrize("input_str,expected_id", [
    ("11B", "1"),
    ("ATR", "62"),
])
def test_decode_to_number_with_ticker_returns_correct_id(input_str, expected_id):
    ticker_to_number = {
        "11B": "1",
        "ATR": "62"
    }

    result = decode_to_number(
        input_str,
        ticker_to_number=ticker_to_number,
        symbol_to_number={},
        stock_id={}
    )

    assert result == expected_id

@pytest.mark.parametrize("input_str,expected_id", [
    ("11BIT", "1"),
    ("APATOR", "34"),
])
def test_decode_to_number_with_symbol_returns_correct_id(input_str, expected_id):
    symbol_to_number = {
        "11BIT": "1",
        "APATOR": "34"
    }

    result = decode_to_number(
        input_str,
        ticker_to_number={},
        symbol_to_number=symbol_to_number,
        stock_id={}
    )

    assert result == expected_id


def test_decode_to_number_with_unknown_input_raises_error():
    with pytest.raises(ValueError, match="Unrecognized company identifier"):
        decode_to_number(
            "Nonexistent company",
            ticker_to_number={},
            symbol_to_number={},
            stock_id={}
        )