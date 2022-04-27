from freezegun import freeze_time
from mock import Mock
from arrow.arrow import Arrow
import pytest
from pycal.api import Event, EventStatus
from pycal.ui import EventWidget
from pycal.views.agenda import Agenda


@pytest.fixture
def event_factory():
    def _event_factory(id: str):
        return Event(
            id=id,
            title="Mock Event",
            start_time=Arrow.now(),
            end_time=Arrow.now(),
            location="Location",
            going=EventStatus.NOT_ANSWERED,
            type="Video",
            video_link="Link",
            calendar="Fake Calendar",
        )

    return _event_factory


class TestAgenda:
    def test_add_events(self, event_factory):
        m_events = [event_factory(f"fake event {i}") for i in range(3)]
        m_storage = Mock()
        m_storage.get_events.return_value = m_events

        # act
        agenda = Agenda(m_storage)

        # assert
        assert agenda.head.event is m_events[0]
        assert agenda.tail.event is m_events[-1]
        assert agenda.rows == 3

    @pytest.mark.parametrize(
        "selector, expected_selection, expected_x, expected_y",
        [
            (lambda a, s: a.select_first(s), 0, 0, 0),
            (lambda a, s: a.select_next(s), 1, 0, 34),
            (lambda a, s: a.select_last(s), -1, 0, 100),
        ],
    )
    @pytest.mark.asyncio
    async def test_select_events(
        self, selector, expected_selection, expected_x, expected_y, event_factory
    ):
        m_events = [event_factory(f"fake event {i}") for i in range(3)]
        m_storage = Mock()
        m_storage.get_events.return_value = m_events
        m_scrollview = Mock(max_scroll_y=100, y=0)

        # act
        agenda = Agenda(m_storage)
        await selector(agenda, m_scrollview)

        # assert
        assert agenda.selected.event is m_events[expected_selection]
        assert m_scrollview.x == expected_x
        assert m_scrollview.y == expected_y

    @freeze_time("2022-04-25")
    def test_render_agenda(self, event_factory):
        # arrange
        m_events = [event_factory("fake event")]
        m_storage = Mock()
        m_storage.get_events.return_value = m_events

        # act
        agenda = Agenda(m_storage)
        table = agenda.render()

        # assert
        assert len(table.columns) == 2
        assert len(table.rows) == 1

        cell_date = next(table.columns[0].cells)
        assert cell_date.renderable.plain == "25\nMon"
        assert isinstance(next(table.columns[1].cells), EventWidget)
