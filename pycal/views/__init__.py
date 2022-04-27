from typing import Protocol, Union

from rich.console import ConsoleRenderable, RichCast
from .agenda import Agenda

from textual.widgets import ScrollView

from pycal.ui import EventWidget


__all__ = [
    "Agenda",
    "CalendarView",
]


class CalendarView(Protocol):
    selected: EventWidget

    async def select_previous(self, view: ScrollView) -> None:
        ...

    async def select_next(self, view: ScrollView) -> None:
        ...

    async def select_first(self, view: ScrollView) -> None:
        ...

    async def select_last(self, view: ScrollView) -> None:
        ...

    async def reload_events(self) -> None:
        ...

    def __rich__(self) -> Union[ConsoleRenderable, RichCast, str]:
        ...
