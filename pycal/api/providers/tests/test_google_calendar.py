from typing import TYPE_CHECKING
import arrow
from mock.mock import Mock, PropertyMock, mock_open, patch

from pycal.api import EventStatus
from pycal.api.providers.google_calendar import (
    GoogleCalendar,
    GoogleCalendarAPI,
    GoogleCredentials,
)


if TYPE_CHECKING:
    from googleapiclient._apis.calendar.v3.schemas import Event as GoogleEvent


m_event: "GoogleEvent" = {
    "kind": "calendar#event",
    "etag": '"3298511920778000"',
    "id": "abc123",
    "status": "confirmed",
    "htmlLink": "https://www.google.com/calendar/event?eid=NmU0c3ExcnNydWkyZHFicGdvczMyZ2N1OGUgZmFiaW9naWJzb24ucmpAbQ",
    "created": "2022-04-06T14:39:20.000Z",
    "updated": "2022-04-06T14:39:20.389Z",
    "summary": "Test Event",
    "creator": {"email": "fabiogibson.rj@gmail.com", "self": True},
    "organizer": {"email": "fabiogibson.rj@gmail.com", "self": True},
    "start": {"dateTime": "2022-04-06T17:00:00", "timeZone": "Europe/Madrid"},
    "end": {"dateTime": "2022-04-06T18:00:00", "timeZone": "Europe/Madrid"},
    "iCalUID": "6e4sq1rsrui2dqbpgos32gcu8e@google.com",
    "sequence": 0,
    "reminders": {"useDefault": True},
    "eventType": "default",
    "location": "Some office room",
    "hangoutLink": "http://meet.google.com/meeting",
    "attendees": [{"self": True, "responseStatus": "accepted"}],
}


# m_event = cast(GoogleEvent, m_event)


class TestGoogleCalendar:
    def test_parse_google_event(self):
        # arrange
        calendar = GoogleCalendar(
            name="Test Calendar", service=Mock(), cache_manager=Mock()
        )

        # act
        event = calendar._parse_event(m_event)

        # assert
        assert event.id == "abc123"
        assert event.title == "Test Event"
        assert event.start_time == arrow.get("2022-04-06 17:00:00")
        assert event.end_time == arrow.get("2022-04-06 18:00:00")
        assert event.location == "Some office room"
        assert event.going == EventStatus.ACCEPTED
        assert event.type == "-"
        assert event.video_link == "http://meet.google.com/meeting"
        assert event.calendar == "Test Calendar"


class TestGoogleCredentials:
    @patch("os.path.exists", Mock(return_value=True))
    @patch("pycal.api.providers.google_calendar.Credentials")
    def test_authorize_from_token(self, m_credentials):
        # arrange
        m_authorization = Mock(expired=False)
        m_credentials.from_authorized_user_file.return_value = m_authorization

        # act
        credentials = GoogleCredentials("foobar.json")
        authorization = credentials.get_authorization()

        # assert
        assert authorization is m_authorization

    @patch("os.path.exists", Mock(return_value=True))
    @patch("pycal.api.providers.google_calendar.Credentials")
    @patch("pycal.api.providers.google_calendar.open", new_callable=mock_open)
    def test_authorize_from_expired_token(self, m_open, m_credentials):
        # arrange
        m_authorization = Mock(expired=True)
        m_credentials.from_authorized_user_file.return_value = m_authorization
        credentials = GoogleCredentials("foobar.json")

        with patch.object(credentials, "_authorization", Mock(valid=False)):
            # act
            authorization = credentials.get_authorization()

        # assert
        assert authorization is m_authorization
        m_authorization.refresh.assert_called_once()
        m_open.return_value.write.assert_called_once_with(m_authorization.to_json())

    @patch("os.path.exists", Mock(return_value=False))
    @patch("pycal.api.providers.google_calendar.InstalledAppFlow")
    @patch("pycal.api.providers.google_calendar.open", new_callable=mock_open)
    def test_authorize_from_credentials(self, m_open, m_appflow):
        # arrange
        m_flow_auth = Mock()
        m_authorization = Mock(valid=True)

        m_appflow.from_client_secrets_file.return_value = m_flow_auth
        m_flow_auth.run_local_server.return_value = m_authorization
        credentials = GoogleCredentials("foobar.json")

        # act
        authorization = credentials.get_authorization()

        assert authorization is m_authorization
        m_open.return_value.write.assert_called_once_with(m_authorization.to_json())


class TestGoogleCalendarAPI:
    @patch.object(GoogleCalendarAPI, "service", new_callable=PropertyMock)
    def test_get_google_events(self, m_service):
        # arrange
        m_service.return_value.list.return_value.execute.return_value = {
            "items": [1, 2, 3]
        }

        # act
        google_api = GoogleCalendarAPI("foobar.json")
        events = google_api.get_events()

        # assert
        assert events == [1, 2, 3]
