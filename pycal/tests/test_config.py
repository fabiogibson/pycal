from typing import Dict
from mock import mock_open
from mock.mock import Mock, patch
from pycal.api import BaseCalendar, Event
from pycal.config import Config


m_config = """
system:
  browser: brave

layout:
    show_header: false
    show_footer: false

calendars:
  - Test Calendar:
      type: FakeCalendar
      credentials: /home/user/credentials.json


agenda:
  bindings:
    select_next: j
    select_previous: k
    select_first: g
    select_last: G
    accept_event: a
    join_meeting: o
    refresh: r
    quit: q
"""


class FakeCalendar(BaseCalendar[Dict]):
    def _parse_event(self, event: Dict) -> Event:
        raise NotImplementedError

    @classmethod
    def fake_factory(cls, name: str, config: Dict) -> "FakeCalendar":
        return cls(name, service=Mock(), cache_manager=Mock())


class TestConfig:
    @classmethod
    def setup_class(cls):
        with patch("pycal.config.open", mock_open(read_data=m_config)):
            cls.config = Config()

    def test_config_browser(self):
        # assert
        assert self.config.browser == "brave"

    def test_load_calendars(self):
        # arrange
        self.config.FACTORIES["FakeCalendar"] = FakeCalendar.fake_factory

        # act
        calendar = list(self.config.calendars)[0]

        # assert
        assert isinstance(calendar, FakeCalendar)
        assert calendar.name == "Test Calendar"

    def test_load_keybindings(self):
        # arrange
        view = Mock()
        view.__class__.__name__ = "Agenda"

        # act
        bindings = self.config.load_keybindings(view)

        # assert
        assert bindings == self.config._config["agenda"]["bindings"]

    def test_layout(self):
        # act/assert
        assert self.config.layout.show_header is False
        assert self.config.layout.show_footer is False
