from datetime import datetime, timedelta
from dateutil.parser import parse
import logging


def encode_event(timestamp, name, type):
    """Returns a string-encoded event representation.
    Example: '2021-03-27 12:21:50.624783+01:00,prepare,start'"""
    return f"{timestamp},{name},{type}"


def decode_event(event_string):
    event = event_string.split(',')
    event_time = parse(event[0])
    event_name = event[1]
    event_type = event[2]
    return (event_time, event_name, event_type)


class EventLog:
    """Abstracts string-encoded sb events (e.g., invoke) stored in the spec config."""

    SB_EVENT_LOG = 'sb_event_log'

    def __init__(self, spec):
        self.spec = spec

    @property
    def events(self):
        # Make sb config backwards-compatible if event log is missing
        if not isinstance(self.spec[EventLog.SB_EVENT_LOG], list):
            self.spec[EventLog.SB_EVENT_LOG] = []
        return self.spec[EventLog.SB_EVENT_LOG]

    def start(self, name):
        return self.add_event(name, 'start')

    def end(self, name):
        return self.add_event(name, 'end')

    def add_event(self, name, type):
        """Adds a named timestamp to the sb log and returns the timestamp.
        MUST not contain a comma (,)"""
        timestamp = datetime.now().astimezone()
        event = encode_event(timestamp, name, type)
        self.events.append(event)
        return timestamp

    def last_event(self):
        if len(self.events) > 0:
            return self.events[-1]
        else:
            return None

    def has_started(self, name='invoke'):
        """Returns true iff there is a start event of the given name available."""
        return self.last_event_time(name, 'start') is not None

    def last_event_time(self, name, type):
        for event_string in reversed(self.events):
            event_time, event_name, event_type = decode_event(event_string)
            if event_name == name and event_type == type:
                return event_time
        return None

    def total_duration(self) -> timedelta:
        """Returns the total benchmark duration since the first logged timestamp"""
        if len(self.events) > 0:
            start_time, _, _ = decode_event(self.events[0])
            end_time, end_name, end_type = decode_event(self.events[-1])
            if end_name == 'cleanup' and end_type == 'end':
                return end_time - start_time
            else:  # in progress
                return datetime.now().astimezone() - start_time
        else:
            return timedelta()

    def event_duration(self, name):
        """Returns the duration of the last event with the given name
        or None if no matching start and end timestamps exist.
        Example: event_duration('invoke')."""
        # scan events backwards for matching end and start times
        end_time = None
        start_time = None
        for event_string in reversed(self.events):
            event_time, event_name, event_type = decode_event(event_string)
            if event_name == name:
                if event_type == 'end':
                    end_time = event_time
                elif event_type == 'start':
                    start_time = event_time
                    # found matching end-start pair
                    if end_time:
                        return end_time - start_time
                    # start_time without matching end_time:
                    # either in progress or aborted
                    # else:
                    #     return None
        return None

    def get_invoke_timespan(self, end_offset=timedelta(minutes=5)):
        """Returns the timespan of the invocation as a tuple of start and end time
        end_offset: Some applications run longer in the background than their
                    user-facing response time. Including extra time after the
                    invocation ended allows traces in progress to complete.
                    Caveat: A too long offset could lead to traces being mixed up
                    with the next benchmark execution.
        """
        start = None
        end = None
        # Some applications run longer in the background than their
        # user-facing response time. A too long offset could lead to
        # traces being mixed up with the next benchmark execution.
        start_invoke = self.last_event_time('invoke', 'start')
        end_invoke = self.last_event_time('invoke', 'end')
        if (start_invoke is not None) and (end_invoke is not None):
            start = start_invoke
            end = end_invoke + end_offset
        elif (start_invoke is not None) and (end_invoke is None):
            logging.warning("Invocation end time missing but start time present: \
    Using current time as end time.")
            start = start_invoke
            end = datetime.now().astimezone()
        else:
            logging.warning("Invocation start and end time missing: \
    Using max time span (current time -6h).")
            end = datetime.now().astimezone()
            start = end + timedelta(hours=-6)
        return (start, end)
