import sys
import requests
import random

NotFoundTestGuid = "8324cf72-84c6-4001-bec2-46505dbe4301"
RandomStringCharset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"


def GenerateRandomString(length):
    return ''.join(random.choice(RandomStringCharset) for _ in range(length))


class InsertRequest:
    def __init__(self, title, description):
        self.title = title
        self.description = description

    @classmethod
    def fromjson(cls, json_object):
        return cls(json_object['title'], json_object['description'])

    def tojson(self):
        return {'title': self.title, 'description': self.description}


class ToDoItem:
    def __init__(self, item_id, title, description, insertion_timestamp, done_timestamp):
        self.id = item_id
        self.title = title
        self.description = description
        self.insertion_timestamp = insertion_timestamp
        self.done_timestamp = done_timestamp

    @classmethod
    def fromjson(cls, json_object):
        return cls(json_object['ID'], json_object['title'], json_object['description'],
                   json_object['insertion_timestamp'], json_object['done_timestamp'])

    def tojson(self):
        return {'ID': self.id, 'title': self.title, 'description': self.description,
                'insertion_timestamp': self.insertion_timestamp, 'done_timestamp': self.done_timestamp}


class API:
    def __init__(self, endpoint):
        if endpoint[-1] == '/':
            self.endpoint = endpoint
        else:
            self.endpoint = endpoint + "/"

    # API functions

    def listItems(self):
        resp = requests.get(url=self.endpoint + "lst")
        ret = []
        if resp.status_code == 200:
            if resp.content is not None:
                data = resp.json()
                if type(data) == list:
                    for item in data:
                        ret.append(ToDoItem.fromjson(item))
                else:
                    ret.append(ToDoItem.fromjson(data))
        else:
            print("failed listItems() with error code " + str(resp.status_code), file=sys.stderr)
            return None
        return ret

    def instertItem(self, insert_request):
        resp = requests.post(url=self.endpoint + "put", json=insert_request.tojson())
        if resp.status_code == 200:
            data = resp.json()
            return ToDoItem.fromjson(data)
        else:
            print("failed insertItem() with error code " + str(resp.status_code), file=sys.stderr)
            return None

    def markAsDone(self, item_id):
        resp = requests.post(url=self.endpoint + "done?id=" + item_id)
        if resp.status_code != 200:
            print("failed markAsDone() with error code " + str(resp.status_code), file=sys.stderr)
            return None
        return item_id

    def deleteItem(self, item_id):
        resp = requests.post(url=self.endpoint + "del?id=" + item_id)
        if resp.status_code != 200:
            print("failed deleteItem() with error code " + str(resp.status_code), file=sys.stderr)
            return None
        return item_id

    def getItem(self, item_id):
        resp = requests.get(url=self.endpoint + "get?id=" + item_id)
        if resp.status_code == 200:
            data = resp.json()
            return ToDoItem.fromjson(data)
        else:
            print("failed insertItem() with error code " + str(resp.status_code), file=sys.stderr)
            return None

    # Tests

    def checkAvailablity(self):
        res = self.listItems() is not None
        if res:
            print("API available!")
        else:
            print("API unavailable!")
        return res

    def insertItems(self, count):
        print("Inserting %d ToDo Items..." % count)
        insert_requests = []
        items = []
        for i in range(count):
            ir = InsertRequest("Todo-Item-%d" % i, GenerateRandomString(300))
            insert_requests.append(ir)
            item = self.instertItem(ir)
            if item is None:
                return None
            items.append(item)
        for i in range(len(insert_requests)):
            if insert_requests[i].title != items[i].title:
                print("failed insertItems() with a unequal titles!", file=sys.stderr)
                return None
            elif insert_requests[i].description != items[i].description:
                print("failed insertItems() with a unequal descriptions!", file=sys.stderr)
                return None
        return items

    def checkListItems(self, items, mustExist, checkIsDone):
        print("Requesting List of Items...")
        itemsFromApp = self.listItems()
        if items is None:
            return None
        for i in range(len(items)):
            found = False
            for j in range(len(itemsFromApp)):
                if items[i].title == itemsFromApp[j].title and items[i].description == itemsFromApp[j].description:
                    found = True
                    if checkIsDone and itemsFromApp[j].done_timestamp == -1:
                        print("Fail!\nFound item that is expected to be Done but is not!", file=sys.stderr)
                        return None
                    break
            if not found and mustExist:
                print("Fail!\nCould not find an Item!", file=sys.stderr)
                return None
            if found and not mustExist:
                print("Fail!\nFound Item that should be deleted!!", file=sys.stderr)
                return None
        print("Done!")
        return "ok!"

    def markItemsAsDone(self, items):
        print("Marking %d items as Done..." % len(items))
        for i in range(len(items)):
            if self.markAsDone(items[i].id) is None:
                return None
        print("Done!")
        return "ok!"

    def checkItemsNotDone(self, items):
        print("Using 'Get' Function to check if the %d items are Done..." % len(items))
        for i in range(len(items)):
            item = self.getItem(items[i].id)
            if item is None:
                return None
            if item.id != items[i].id:
                print("Fail!\nGet Item returned a different ID then queried.", file=sys.stderr)
                return None
            if item.done_timestamp != -1:
                print("Fail!\nAn Item is marked as done while it should not!", file=sys.stderr)
                return None
        print("Done!")
        return "ok!"

    def checkDelete(self, items):
        print("Deleting all inserted Items...")
        for item in items:
            if self.deleteItem(item.id) is None:
                return None
        print("Done!")
        return "ok!"

    def checkFunctionsNotFoundBehaviour(self):
        print("Checking ID specific functions API Behaviour if ID does not exist")
        print("Get Function...")
        if self.getItem(NotFoundTestGuid) is not None:
            print("Fail!\nExpected Error. Got None.", file=sys.stderr)
            return None
        print("Ok! Got error while getting Item.\nDone Function...")
        if self.markAsDone(NotFoundTestGuid) is not None:
            print("Fail!\nExpected Error. Got None.", file=sys.stderr)
            return None
        print("Ok! Got error while marking as done.\nDelete Function...")
        if self.deleteItem(NotFoundTestGuid) is not None:
            print("Fail!\nExpected Error. Got None.", file=sys.stderr)
            return None
        print("Ok Got error while deleting item!\nDone!")
        return "ok!"


def test_api(endpoint, count):
    api = API(endpoint)
    if not api.checkAvailablity():
        return
    items = api.insertItems(count)
    if items is None:
        return
    if api.checkListItems(items, True, False) is None:
        return
    bound = int(count/2)
    print("Using Bound %d" % bound)
    doneItems = items[:bound]
    notDoneItems = items[bound:]
    if api.markItemsAsDone(doneItems) is None:
        return
    if api.checkListItems(doneItems, True, True) is None:
        return
    if api.checkItemsNotDone(notDoneItems) is None:
        return
    if api.checkDelete(items) is None:
        return
    if api.checkListItems(items, False, False) is None:
        return
    # if api.checkFunctionsNotFoundBehaviour() is None:
    #     return
    print("Success! All Checks have passed!")
    return "ok!"
