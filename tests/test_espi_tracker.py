import sys
from pathlib import Path

import pytest
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from unittest.mock import AsyncMock, MagicMock, patch
from cogs.espi_tracker import ESPITracker


@pytest.mark.asyncio
async def test_add_company_success(monkeypatch):
    tracker = ESPITracker(bot=MagicMock())
    ctx = AsyncMock()
    ctx.channel.name = "⌊🌍⌉-czat-polska"
    ctx.send = AsyncMock()

    monkeypatch.setattr("cogs.espi_tracker.get_company_name", lambda url: "Test Corp")
    monkeypatch.setattr("cogs.espi_tracker.get_espi_announcements", lambda url: [])
    tracker.get_company_emoji = MagicMock(return_value="🚀")
    tracker.save_json = MagicMock()

    msg = AsyncMock()
    msg.content = "Test Corp 🚀"
    msg.id = 123
    msg.pin = AsyncMock()
    ctx.send.side_effect = [None, msg]

    await tracker._add_company_to_dict(ctx, "42")

    assert "42" in tracker.pinned_stocks
    assert tracker.pinned_stocks["42"]["name"] == "Test Corp"
    assert tracker.pinned_stocks["42"]["emoji"] == "🚀"
    msg.pin.assert_called_once()
    tracker.check_espi.cancel()

@pytest.mark.asyncio
async def test_remove_company_success(monkeypatch):
    tracker = ESPITracker(bot=MagicMock())
    ctx = AsyncMock()
    ctx.channel.name = "⌊🌍⌉-czat-polska"
    ctx.guild = MagicMock()
    channel = MagicMock()
    ctx.guild.channels = [channel]
    channel.name = "⌊🌍⌉-czat-polska"
    ctx.send = AsyncMock()

    tracker.pinned_stocks["42"] = {
        "name": "Test Corp",
        "emoji": "🚀",
        "url": "https://example.com",
        "messages": [{"id": 123, "content": "msg", "pinned": True}]
    }
    tracker.espi_history["42"] = [{"title": "Example"}]
    tracker.save_json = MagicMock()

    # Mock message fetch/unpin
    msg = AsyncMock()
    msg.unpin = AsyncMock()
    channel.fetch_message = AsyncMock(return_value=msg)

    await tracker._remove_stock(ctx, "42")

    assert "42" not in tracker.pinned_stocks
    assert "42" not in tracker.espi_history
    msg.unpin.assert_called_once()
    ctx.send.assert_called_with("Stopped tracking ESPI announcements for **Test Corp**.")
    tracker.check_espi.cancel()