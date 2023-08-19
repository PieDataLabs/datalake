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

    def similar(self, data_ids,
                search_limit=9) -> 'DataRequest':
        return self.searcher.search_similar(self.request_id,
                                            data_ids,
                                            search_limit=search_limit)
