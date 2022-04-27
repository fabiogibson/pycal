import json
from datetime import datetime
from typing import Dict, Optional
import arrow
from mock import patch, mock_open, Mock

import pytest

from pycal.api import BaseCalendar, Event, EventStatus, EventStorage, JsonCacheManager


class TestJsonCacheManager:
    @patch("os.path.exists", Mock(return_value=False))
    def test_load_cache_from_missing_file_returns_no_events(self):
        # arrange
        cache_manager = JsonCacheManager(cache_file="cache.json")

        # act
        cache, is_valid = cache_manager.load_cache()

        # assert
        assert cache == []
        assert not is_valid

    @patch("os.path.exists", Mock(return_value=True))
    @pytest.mark.parametrize("expiration, expect_valid", [(100, False), (90, True)])
    def test_load_cache_expiration(self, expiration: int, expect_valid: bool):
        # arrange
        m_data = {
            "load_time": datetime.now().timestamp() - expiration,
            "events": [1, 2, 3],
        }

        with patch("pycal.api.open", mock_open(read_data=json.dumps(m_data))):
            cache_manager = JsonCacheManager(cache_file="cache.json")

            # act
            cache, is_valid = cache_manager.load_cache(expiration=100)

            # assert
            assert cache == [1, 2, 3]
            assert is_valid == expect_valid

    @patch("pycal.api.Arrow.now", Mock(return_value=arrow.get("1970-01-01")))
    @patch("pycal.api.json.dump")
    def test_build_cache(self, m_dump):
        # arrange
        cache_manager = JsonCacheManager(cache_file="cache.json")

        with patch("pycal.api.open", mock_open()) as m_open:
            # act
            cache_manager.build_cache([{"event": "data"}])

            # assert
            m_dump.assert_called_with(
                {"events": [{"event": "data"}], "load_time": 0.0}, m_open.return_value
            )


class TestEventStorage:
    @pytest.mark.parametrize("init_state, ignore_cache", [(None, False), ({}, True)])
    def test_get_events_from_calendars(
        self, init_state: Optional[Dict], ignore_cache: bool
    ):
        # arrange
        m_event = Event(
            id="1",
            title="some event",
            start_time=arrow.now(),
            end_time=arrow.now(),
            going=EventStatus.ACCEPTED,
            location="",
            type="",
            video_link="",
            calendar="Mock Calendar",
        )
        m_calendar = Mock(spec=BaseCalendar)
        m_calendar.get_events.return_value = [m_event]
        m_calendar.name = "Mock Calendar"

        storage = EventStorage([m_calendar])
        storage._events = init_state

        # act
        events = storage.get_events(ignore_cache)

        # assert
        assert m_event in events

    def test_get_events_from_cache(self):
        # arrange
        m_calendar = Mock(spec=BaseCalendar)
        m_calendar.name = "Mock Calendar"

        storage = EventStorage([m_calendar])
        storage._events = {}

        # act
        events = list(storage.get_events())

        # assert
        assert events == []
        m_calendar.get_events.assert_not_called()
