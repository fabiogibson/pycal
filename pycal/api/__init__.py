from datetime import timedelta
import heapq
import os
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import subprocess
from typing import (
    Any,
    Generic,
    Iterable,
    Optional,
    List,
    Dict,
    Protocol,
    Tuple,
    TypeVar,
)

from arrow import Arrow

from pycal.config import Config


class EventStatus(str, Enum):
    ACCEPTED = "accepted"
    DECLINED = "declined"
    NOT_ANSWERED = "not answered"


@dataclass
class Event:
    id: str
    title: str
    start_time: Arrow
    end_time: Arrow
    location: str
    going: EventStatus
    type: str
    video_link: Optional[str]
    calendar: str


T = TypeVar("T")


class CalendarAPI(Protocol[T]):
    def get_events(self) -> List[T]:
        ...


class CacheManager(Protocol[T]):
    def load_cache(self, expiration: int = 600) -> Tuple[List[T], bool]:
        ...

    def build_cache(self, events: List[T]) -> None:
        ...


class JsonCacheManager:
    def __init__(self, cache_file: str):
        self.cache_file = cache_file

    def load_cache(self, expiration: int = 600) -> Tuple[List[Dict[Any, Any]], bool]:
        if not os.path.exists(self.cache_file):
            return [], False

        with open(self.cache_file, "r") as f:
            cache = json.load(f)
            delta: timedelta = Arrow.now() - Arrow.fromtimestamp(cache["load_time"])
            valid = delta.total_seconds() <= expiration
            return cache["events"], valid

    def build_cache(self, events: List[Dict[Any, Any]]) -> None:
        with open(self.cache_file, "w") as f:
            cache = {
                "events": events,
                "load_time": Arrow.now().timestamp(),
            }

            json.dump(cache, f)


class BaseCalendar(ABC, Generic[T]):
    def __init__(self, name: str, cache_manager: CacheManager, service: CalendarAPI):
        self.name = name
        self.cache_manager = cache_manager
        self.service = service

    def get_events(self, ignore_cache: bool = False) -> Iterable[Event]:
        events: List[T] = []
        valid: bool = False

        if not ignore_cache:
            events, valid = self.cache_manager.load_cache()

        if not valid:
            events = self.service.get_events()
            self.cache_manager.build_cache(events)

        yield from (self._parse_event(event) for event in events)

    @abstractmethod
    def _parse_event(self, event: T):
        """ """
        raise NotImplementedError


class EventStorage:
    def __init__(self, config: Config):
        self.config = config
        self.calendars = config.calendars
        self._events: Optional[Dict[str, Iterable[Event]]] = None

    def _merge_events(self, event_lists: Iterable[Iterable[Event]]):
        heap = []
        iterators = [iter(lst) for lst in event_lists]

        for index, iterator in enumerate(iterators):
            if event := next(iterator, None):
                heap.append((event.start_time, index, event))

        heapq.heapify(heap)

        while heap:
            _, index, event = heapq.heappop(heap)

            if next_event := next(iterators[index], None):
                heapq.heappush(heap, (next_event.start_time, index, next_event))

            yield event

    def get_events(self, ignore_cache: bool = False) -> Iterable[Event]:
        if self._events is None or ignore_cache:
            self._events = {c.name: c.get_events(ignore_cache) for c in self.calendars}

        return self._merge_events(self._events.values())

    def get_closest_event(self) -> Event:
        now = Arrow.now()

        return min(
            self.get_events(),
            key=lambda e: abs((now - e.start_time).total_seconds()),
        )

    def join_event(self, event: Event) -> None:
        if event.video_link:
            subprocess.run(
                [self.config.browser, event.video_link],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
