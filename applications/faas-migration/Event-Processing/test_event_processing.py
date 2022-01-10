import sys
import requests
import time

class SentEvent:
    def __init__(self, _type, _source):
        self.type = _type
        self.source = _source

class ProcessedEvent:
    def __init__(self, id, source, timestamp, message):
        self.id = id
        self.source = source
        self.timestamp = timestamp
        self.message = message

    @classmethod
    def fromjson(cls, json_object):
        return cls(json_object['ID'], json_object['source'], json_object['timestamp'], json_object['message'])

    def tojson(self):
        return {'ID': self.id, 'source': self.source, 'timestamp': self.timestamp, 'message': self.message}


class API:
    def __init__(self, endpoint):
        if endpoint[-1] == '/':
            self.endpoint = endpoint
        else:
            self.endpoint = endpoint + "/"

    # API functions

    def listEvents(self):
        resp = requests.get(url=self.endpoint + "list")
        ret = []
        if resp.status_code == 200:
            if resp.content is not None:
                data = resp.json()
                if type(data) == list:
                    for item in data:
                        ret.append(ProcessedEvent.fromjson(item))
                else:
                    ret.append(ProcessedEvent.fromjson(data))
        else:
            print("failed listEvents() with error code " + str(resp.status_code), file=sys.stderr)
            return None
        return ret

    def getLatest(self):
        resp = requests.get(url=self.endpoint + "latest")
        ret = []
        if resp.status_code == 200:
            if resp.content is not None:
                data = resp.json()
                if type(data) == list:
                    for item in data:
                        ret.append(ProcessedEvent.fromjson(item))
                else:
                    ret.append(ProcessedEvent.fromjson(data))
        else:
            print("failed getLatest() with error code " + str(resp.status_code), file=sys.stderr)
            return None
        if len(ret) == 1:
            return ret[0]
        else:
            print("No item in Latest.")
            return None

    # Tests

    def checkEndpoint(self):
        res = self.listEvents() is not None
        if res:
            print("API available!")
        else:
            print("API unavailable!")
        return res

    def insertEvents(self, spec, count):
        transfer_log_name = "transfer_log.csv"
        transfer_log_path = spec.logs_directory() / transfer_log_name

        envs = {
            'URL': self.endpoint
        }
        options = f"--logformat raw --console-output={transfer_log_path}"
        spec.run_k6(envs, options)
        # HACK to fix file permissions of transfer_log on Linux
        if spec.host_system() == 'Linux':
            spec.run('sb fix_permissions --local', image='serverless-benchmarker')

        # Read output
        events = []
        with open(transfer_log_path, "r") as transfer_log:
            for line in transfer_log:
                if line.startswith("transfer"):
                    splits = [x.strip() for x in line.split(",")]
                    events.append(SentEvent(splits[1], splits[2]))

        return events

    def validateEventsInserted(self, events):
        print("Retrieving all events from the database...")
        evts = self.listEvents()
        if evts is None:
            return None
        print("Ok!\nValidating that all events have been processed...")
        fail = False
        notFoundCount = 0
        for sent_event in events:
            found = False
            for processed_event in evts:
                if processed_event.source == sent_event.source:
                    found = True
                    if sent_event.type == "state_change" and not "status" in processed_event.message:
                        print("Fail!\nMessage Processing of State Change Message Failed", file=sys.stderr)
                        return None
                    if sent_event.type == "forecast" and not "Forecasted" in processed_event.message:
                        print("Fail!\nMessage Processing of Forecast Message Failed", file=sys.stderr)
                        return None
                    if sent_event.type == "temperature" and not "Temperature" in processed_event.message:
                        print("Fail!\nMessage Processing of Temperature Message Failed", file=sys.stderr)
                        return None
                    break
            if not found:
                fail = True
                notFoundCount = notFoundCount + 1
        if fail:
            print("Warning!\n%d of %d insertions were not found!" % (notFoundCount, len(events)))
            return None
        print("Ok!")
        return "ok!"

    def testLatest(self):
        print("Fetching latest element...")
        l = self.getLatest()
        if l is None:
            return None
        print("Ok! Got ID %d" % l.id)


def test(spec, endpoint, delay, count):
    api = API(endpoint)
    if not api.checkEndpoint():
        return None
    evts = api.insertEvents(spec, count)
    print("Waiting %d Seconds to let the events process..." % delay)
    time.sleep(delay)
    if api.validateEventsInserted(evts) is None:
        return None
    if api.testLatest() is None:
        return None
    print("Test Execution Done Successfully!")
    return "ok!"

