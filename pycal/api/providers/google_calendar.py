from __future__ import annotations
from datetime import datetime
import os
from enum import Enum
from typing import TYPE_CHECKING, Dict, List

import arrow
from google.oauth2.credentials import Credentials  # type: ignore
from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore
from google.auth.exceptions import RefreshError  # type: ignore
from google.auth.transport.requests import Request  # type: ignore
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build

if TYPE_CHECKING:
    from googleapiclient._apis.calendar.v3.schemas import Event as GoogleEvent

from pycal.api import BaseCalendar, Event, EventStatus, JsonCacheManager


class GoogleEventStatus(Enum):
    accepted = EventStatus.ACCEPTED
    declined = EventStatus.DECLINED
    needsAction = EventStatus.NOT_ANSWERED
    tentative = EventStatus.NOT_ANSWERED


class GoogleCredentials:
    SCOPES = [
        "https://www.googleapis.com/auth/calendar.events",
    ]

    def __init__(self, credentials_file: str):
        self.credentials_file = credentials_file
        self.token_file = credentials_file.replace(".json", ".token.json")
        self._authorization = None

    def _authorize_from_credentials(self) -> bool:
        self._authorization = InstalledAppFlow.from_client_secrets_file(
            self.credentials_file,
            self.SCOPES,
        ).run_local_server(port=0)

        self._save_authorization()
        return self._authorization is not None and self._authorization.valid

    def _authorize_from_token(self) -> bool:
        if not os.path.exists(self.token_file):
            return False

        self._authorization = Credentials.from_authorized_user_file(
            self.token_file,
            self.SCOPES,
        )

        if (
            self._authorization
            and self._authorization.expired
            and self._authorization.refresh_token
        ):
            self._refresh_authorization()
            self._save_authorization()

        return self._authorization is not None and self._authorization.valid

    def _refresh_authorization(self) -> None:
        if not self._authorization:
            return

        request = Request()

        try:
            self._authorization.refresh(request)
        finally:
            if request.session:
                request.session.close()

    def _save_authorization(self) -> None:
        if not self._authorization:
            raise

        with open(self.token_file, "w") as token:
            token.write(self._authorization.to_json())

    def get_authorization(self):
        if not self._authorization or not self._authorization.valid:
            authorized = False

            try:
                authorized = self._authorize_from_token()
            except RefreshError:
                pass

            if not authorized:
                self._authorize_from_credentials()

        return self._authorization


class GoogleCalendarAPI:
    def get_events(self, max_results: int = 10) -> List["GoogleEvent"]:
        try:
            events_result = self.service.list(
                calendarId="primary",
                timeMin=datetime.utcnow().isoformat() + "Z",
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            ).execute()

            return events_result.get("items", [])
        except HttpError:
            return []
        finally:
            self.service.close()

    def __init__(self, credentials_file: str):
        self._credentials = GoogleCredentials(credentials_file)
        self._service = None

    @property
    def service(self):
        if not self._service:
            self._service = build(
                "calendar",
                "v3",
                credentials=self._credentials.get_authorization(),
            ).events()

        return self._service


class GoogleCalendar(BaseCalendar["GoogleEvent"]):
    @classmethod
    def from_settings(cls, name: str, config: Dict) -> "GoogleCalendar":
        credentials_file = os.path.expanduser(config["credentials"])

        return cls(
            name,
            service=GoogleCalendarAPI(credentials_file),
            cache_manager=JsonCacheManager(
                os.path.expanduser(
                    f"~/agenda.{name.lower().replace(' ', '_')}.json",
                )
            ),
        )

    def _parse_user_response(self, event: GoogleEvent) -> EventStatus:
        for attendee in event.get("attendees", []):
            if attendee.get("self"):
                response = attendee.get("responseStatus", "needsAction")
                return GoogleEventStatus[response].value

        return GoogleEventStatus.needsAction.value

    def _parse_event(self, event: GoogleEvent) -> Event:
        try:
            start: arrow.Arrow = arrow.get(event["start"]["dateTime"])
            end: arrow.Arrow = arrow.get(event["end"]["dateTime"])
            event_type: str = (
                event.get("conferenceData", {})
                .get("conferenceSolution", {})
                .get("name", "-")
            )

            return Event(
                id=event["id"],
                title=event["summary"],
                start_time=start,
                end_time=end,
                location=event.get("location", "-"),
                going=self._parse_user_response(event),
                type=event_type,
                video_link=event.get("hangoutLink"),
                calendar=self.name,
            )
        except KeyError:
            raise
