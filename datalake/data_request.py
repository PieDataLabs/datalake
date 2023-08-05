import os
from time import sleep


class DataRequest(object):
    def __init__(self, searcher,
                 request_id: str):
        super(DataRequest, self).__init__()
        self.searcher = searcher
        self.request_id = request_id

    def __repr__(self):
        return f"DataRequest({self.request_id})"

    def retrieve(self):
        return self.searcher.retrieve_data(self.request_id)

    def wait(self, n=1,
             timeout=None):
        wait_time = 1
        while True:
            data = self.retrieve()
            if len(data) >= n:
                return data
            wait_time *= 1.01
            sleep(wait_time)
