
from sb.event_log import EventLog
from datetime import timedelta, datetime
from dateutil.tz import tzoffset


def test_event_duration():
    expected_duration = timedelta(seconds=1, microseconds=2661)
    event_log = EventLog({EventLog.SB_EVENT_LOG: [
        '2021-08-31 19:54:06.172199+02:00,prepare,start',
        '2021-08-31 19:54:07.174860+02:00,prepare,end'
    ]})
    assert event_log.event_duration('prepare') == expected_duration


def test_get_invoke_timespan():
    event_log = EventLog({EventLog.SB_EVENT_LOG: [
        '2021-08-31 20:00:00.100001+02:00,invoke,start',
        '2021-08-31 20:01:00.200002+02:00,invoke,end'
    ]})
    end_offset = timedelta(minutes=1)
    start, end = event_log.get_invoke_timespan(end_offset)
    assert start == datetime(2021, 8, 31, 20, 0, 0, 100001, tzinfo=tzoffset(None, 7200))
    assert end   == datetime(2021, 8, 31, 20, 2, 0, 200002, tzinfo=tzoffset(None, 7200))  # noqa: E221, E501
