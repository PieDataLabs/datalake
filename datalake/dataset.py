import os
from typing import List
from .data_request import DataRequest


class Dataset(object):
    def __init__(self, searcher,
                 dataset_id):
        super(Dataset, self).__init__()
        self.searcher = searcher
        self.dataset_id = dataset_id

    def add(self,
            data_request: DataRequest,
            ids: List[int]):
        self.searcher.dataset_add(self.dataset_id,
                                  data_request.request_id,
                                  data_ids=ids)
        return self

    def count(self):
        return self.searcher.dataset_info(self.dataset_id).get("images_count", 0)

    def count_annotations(self):
        return self.searcher.dataset_info(self.dataset_id).get("annotations_count", 0)

    def list(self) -> List['Dataset']:
        return self.searcher.dataset_list()

    def __repr__(self):
        info = self.searcher.dataset_info(self.dataset_id)
        return f"Dataset#{info['keyname']}(images={info['images_count']}, annotations={info['annotations_count']})"
