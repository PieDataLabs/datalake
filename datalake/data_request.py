import os
from time import sleep
from typing import Optional, Union, TYPE_CHECKING
if TYPE_CHECKING:
    from .dataset import Dataset
from .settings import FREEMIUM_SEARCH_LIMIT


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
                dataset: Optional['Dataset'] = None,
                search_limit=FREEMIUM_SEARCH_LIMIT) -> 'DataRequest':
        return self.searcher.search_similar(self.request_id,
                                            data_ids,
                                            dataset_id=None if dataset is None else dataset.dataset_id,
                                            search_limit=search_limit)
