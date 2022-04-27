import subprocess
from mock.mock import AsyncMock, Mock, patch
import pytest
from pycal.app import PyCalendar


@pytest.mark.asyncio
@patch("pycal.app.ScrollView", AsyncMock)
class TestApp:
    @patch("pycal.app.Header", Mock(return_value=1))
    async def test_mount_header(self):
        # arrange
        m_config = Mock()
        m_config.layout.show_header = True

        with patch("pycal.app.PyCalendar.view", AsyncMock()) as m_view:
            # act
            await PyCalendar(calendar_view=None, config=m_config).on_mount()

            # assert
            m_view.dock.assert_any_call(1, edge="top")

    @patch("pycal.app.FooterWidget", Mock(return_value=1))
    async def test_mount_footer(self):
        # arrange
        m_config = Mock()
        m_config.layout.show_footer = True

        with patch("pycal.app.PyCalendar.view", AsyncMock()) as m_view:
            # act
            await PyCalendar(calendar_view=None, config=m_config).on_mount()

            # assert
            m_view.dock.assert_any_call(1, edge="bottom")

    async def test_mount_scrollable_view(self):
        # arrange
        m_config = Mock()

        with patch("pycal.app.PyCalendar.view", AsyncMock()) as m_view:
            # act
            app = PyCalendar(calendar_view=None, config=m_config)
            await app.on_mount()

            # assert
            m_view.dock.assert_any_call(app.body, edge="top")

    async def test_bind_keys(self):
        # arrange
        m_config = Mock()
        m_config.load_keybindings.return_value = {"some_action": "k"}

        with patch("pycal.app.PyCalendar.bind") as m_bind:
            # act
            await PyCalendar(calendar_view=None, config=m_config).on_load()

            # assert
            m_bind.assert_called_once_with("k", "some_action", "Some action")

    @pytest.mark.parametrize(
        "action",
        [
            "select_previous",
            "select_next",
            "select_last",
            "select_first",
        ],
    )
    async def test_invoke_events_navigation(self, action):
        # arrange
        app = PyCalendar(calendar_view=AsyncMock(), config=Mock())
        app.body = Mock()

        # act
        app_action = getattr(app, f"action_{action}")
        await app_action()

        # assert
        getattr(app.calendar_view, action).assert_called_once_with(app.body)

    async def test_invoke_refresh_events(self):
        # arrange
        app = PyCalendar(calendar_view=AsyncMock(), config=Mock())
        app.body = Mock()

        # act
        await app.action_refresh()

        # assert
        app.calendar_view.reload_events.assert_called_once()
        app.calendar_view.select_first.assert_called_once_with(app.body)

    @patch("pycal.app.subprocess.run")
    async def test_invoke_join_meeting(self, m_run):
        # arrange
        m_view = Mock()
        m_view.selected.event.video_link = "some link"
        app = PyCalendar(calendar_view=m_view, config=Mock(browser="browser"))

        with patch.object(app, "action") as m_action:
            # act
            await app.action_join_meeting()

        # assert
        m_run.assert_called_once_with(
            ["browser", "some link"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        m_action.assert_called_once_with("quit")
