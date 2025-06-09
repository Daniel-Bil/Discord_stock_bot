import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
import pytest
from unittest.mock import AsyncMock, MagicMock
from cogs.espi_tracker import ESPITracker
from cogs.espi_tracker import decode_to_number  # Optional, for debug

@pytest.mark.asyncio
async def test_add_command_fuzzy_match_real_data():
    # Real decoders will be loaded
    tracker = ESPITracker(bot=MagicMock())

    ctx = AsyncMock()
    ctx.channel.name = "⌊🌍⌉-czat-polska"
    tracker._add_company_to_dict = AsyncMock()

    input_str = "11 bit studios"

    decoded = decode_to_number(
        input_str,
        tracker.ticker_to_id,
        tracker.symbol_to_id,
        tracker.stock_id
    )

    assert decoded == "1", f"Expected '1', got '{decoded}'"

    await tracker.add(tracker, ctx, input_str)

    tracker._add_company_to_dict.assert_awaited_once_with(ctx, "1")
