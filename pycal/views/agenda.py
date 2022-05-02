from collections import defaultdict
from datetime import date
from typing import Dict, List, Optional, Tuple

from rich import box
from rich.console import RenderableType
from rich.padding import Padding
from rich.table import Table
from rich.text import Text
from textual.widget import Widget
from textual.widgets import ScrollView
from textual.reactive import Reactive

from pycal.api import Event, EventStorage
from pycal.ui import EventWidget


class Agenda(Widget):
    selected: Reactive[Optional[EventWidget]] = Reactive(None)

    def __init__(self, storage: EventStorage):
        super().__init__()
        self.storage = storage
        self.events: Dict[date, List[EventWidget]] = defaultdict(list)
        self.head: Optional[EventWidget]
        self.tail: Optional[EventWidget]
        self.load_events()

    @property
    def rows(self):
        return sum(len(v) for v in self.events.values())

    @property
    def cols(self):
        return 1

    def watch_selected(
        self, previous: Optional[EventWidget], current: Optional[EventWidget]
    ) -> None:
        if previous:
            previous.deselect()

        if current:
            current.select()

    def reload_events(self) -> None:
        self.load_events(ignore_cache=True)

    def load_events(self, ignore_cache: bool = False) -> None:
        self.events.clear()
        self.head = None
        self.tail = None
        self.selected = None

        for event in self.storage.get_events(ignore_cache):
            self.add_event(event)

        self.refresh()

    def select(
        self, event: EventWidget, scroll_view: ScrollView, x: float, y: float
    ) -> None:
        self.selected = event
        scroll_view.x = x
        scroll_view.y = y

    async def select_first(self, scroll_view: ScrollView) -> None:
        if self.head:
            self.select(self.head, scroll_view, 0, 0)

    async def select_last(self, scroll_view: ScrollView) -> None:
        if self.tail:
            self.select(self.tail, scroll_view, 0, scroll_view.max_scroll_y)

    async def select_next(self, scroll_view: ScrollView) -> None:
        if self.selected and self.selected.next:
            scroll_y = scroll_view.y + scroll_view.max_scroll_y // self.rows + 1
            self.select(self.selected.next, scroll_view, 0, scroll_y)

    async def select_previous(self, scroll_view: ScrollView) -> None:
        if self.selected and self.selected.previous:
            scroll_y = scroll_view.y - scroll_view.max_scroll_y // self.rows - 1
            self.select(self.selected.previous, scroll_view, 0, scroll_y)

    async def join_selected_event(self) -> None:
        if self.selected:
            self.storage.join_event(self.selected.event)

    def add_event(self, event: Event) -> None:
        event_widget = EventWidget(event)
        self.events[event.start_time.date()].append(event_widget)

        if not self.head:
            self.head = event_widget
            self.selected = event_widget

        elif self.tail:
            self.tail.next = event_widget
            event_widget.previous = self.tail

        self.tail = event_widget

    def _build_event(self, display_date: bool, event_widget: EventWidget) -> Tuple:
        start_time = event_widget.event.start_time

        date_repr: RenderableType = (
            Text.assemble(
                ((start_time.format("DD")), "bold"), "\n", start_time.format("ddd")
            )
            if display_date
            else ""
        )

        return Padding(date_repr, (1,)), event_widget

    def _build_table(self) -> Table:
        table = Table(
            box=box.SIMPLE,
            padding=(0, 0, 0, 0),
            show_header=False,
            expand=True,
            style="white on black",
        )

        table.add_column(
            "Date",
            style="cyan on black",
            min_width=5,
            width=5,
        )

        table.add_column(
            "EventWidget",
            style="white on black",
        )

        return table

    def render(self) -> RenderableType:
        table = self._build_table()

        for events in self.events.values():
            for index, event in enumerate(events):
                table.add_row(
                    *self._build_event(index == 0, event),
                )

        return table
