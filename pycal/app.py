import subprocess

from textual.widgets import ScrollView, Header
from textual.app import App
from pycal.config import Config

from pycal.ui import FooterWidget
from pycal.views import CalendarView


class PyCalendar(App):
    def __init__(self, calendar_view: CalendarView, config: Config, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.body: ScrollView
        self.calendar_view = calendar_view
        self.config = config

    async def _bind_keys(self):
        for action, key in self.config.load_keybindings(self.calendar_view).items():
            await self.bind(
                key,
                action,
                action.capitalize().replace("_", " "),
            )

    async def on_mount(self) -> None:
        self.body = ScrollView()

        if self.config.layout.show_header:
            await self.view.dock(Header(style="white on black"), edge="top")

        if self.config.layout.show_footer:
            await self.view.dock(FooterWidget(), edge="bottom")

        await self.view.dock(self.body, edge="top")
        await self.body.update(self.calendar_view)

    async def on_load(self) -> None:
        await self._bind_keys()

    async def action_select_previous(self) -> None:
        """"""
        await self.calendar_view.select_previous(self.body)

    async def action_select_next(self) -> None:
        """"""
        await self.calendar_view.select_next(self.body)

    async def action_select_last(self) -> None:
        """"""
        await self.calendar_view.select_last(self.body)

    async def action_select_first(self) -> None:
        """"""
        await self.calendar_view.select_first(self.body)

    async def action_refresh(self) -> None:
        """"""
        self.calendar_view.reload_events()
        await self.calendar_view.select_first(self.body)

    async def action_join_meeting(self) -> None:
        """"""
        if (
            self.calendar_view.selected
            and self.calendar_view.selected.event
            and self.calendar_view.selected.event.video_link
        ):
            subprocess.run(
                [self.config.browser, self.calendar_view.selected.event.video_link],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            await self.action("quit")

    async def action_accept_event(self) -> None:
        """"""
        raise NotImplementedError
