from typing import TYPE_CHECKING, Callable, Dict, Generator, List
import os
import yaml


if TYPE_CHECKING:
    from pycal.api import BaseCalendar

    CalendarFactory = Callable[[str, Dict], BaseCalendar]


class Layout:
    def __init__(self, config: Dict):
        self.config = config

    @property
    def show_header(self) -> bool:
        return self.config.get("show_header", True)

    @property
    def show_footer(self) -> bool:
        return self.config.get("show_footer", True)


class Config:
    FACTORIES: Dict[str, "CalendarFactory"] = {}

    @staticmethod
    def _read_file(file_path: str):
        with open(file_path, "r") as f:
            return yaml.load(f, Loader=yaml.FullLoader)

    def __init__(self):
        self._config = self._read_file(os.path.expanduser("~/.pycal.yml"))
        self._layout = Layout(self._config.get("layout", {}))
        self._calendars: List[BaseCalendar] = []

    @property
    def calendars(self) -> List["BaseCalendar"]:
        if not self._calendars:
            for calendar in self._config["calendars"]:
                for name, config in calendar.items():
                    factory = self.FACTORIES[config["type"]]
                    self._calendars.append(factory(name, config))

        return self._calendars

    @property
    def layout(self) -> Layout:
        return self._layout

    @property
    def browser(self) -> str:
        return self._config["system"]["browser"]

    def load_keybindings(self, view) -> Dict[str, str]:
        view_name = view.__class__.__name__
        return self._config[view_name.lower()]["bindings"]
