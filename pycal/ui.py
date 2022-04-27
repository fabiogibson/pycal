from typing import Optional
from rich import box
from rich.console import RenderableType
from rich.panel import Panel
from rich.text import Text
from textual.reactive import Reactive
from textual.widget import Widget

from pycal.api import Event


class EventWidget(Widget):
    selected = Reactive(False)

    def select(self):
        self.selected = True

    def deselect(self):
        self.selected = False

    def __init__(self, event: Event):
        super().__init__()
        self.next: Optional[EventWidget] = None
        self.previous: Optional[EventWidget] = None
        self.event = event

    def render(self) -> Panel:
        return Panel(
            Text.assemble(
                (f"{self.event.title}", "bold yellow"),
                (f" ({self.event.calendar})", "green"),
                (
                    (
                        f"\n{self.event.start_time.format('hh:mm')} - "
                        f"{self.event.end_time.format('hh:mm')}"
                        f"\n{self.event.location}\n{self.event.type}"
                    ),
                    "white",
                ),
                (f"\n{self.event.going}", "green"),
            ),
            style="red on black" if self.selected else "white on black",
            box=box.ROUNDED,
        )


class FooterWidget(Widget):
    def __init__(self) -> None:
        self.keys: list[tuple[str, str]] = []
        super().__init__()
        self.layout_size = 1
        self._key_text: Text | None = None

    def make_key_text(self) -> Text:
        text = Text(
            style="white on dark",
            no_wrap=True,
            overflow="ellipsis",
            justify="left",
            end="",
        )

        for binding in self.app.bindings.shown_keys:
            key_display = (
                binding.key if binding.key_display is None else binding.key_display
            )

            key_text = Text.assemble(
                (f"[{key_display}]", "magenta on default"),
                f" {binding.description} ",
            )

            text.append_text(key_text)

        return text

    def render(self) -> RenderableType:
        if self._key_text is None:
            self._key_text = self.make_key_text()

        return self._key_text
