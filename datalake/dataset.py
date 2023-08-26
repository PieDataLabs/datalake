import os
from typing import List
from PIL import Image
import numpy as np

from .data_request import DataRequest
from .annotations import Annotation
from .settings import FEATURE_DIMENSION
from .utils import to_base64


class Dataset(object):
    def __init__(self, searcher,
                 dataset_id: str):
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
        return f"Dataset#{info['keyname']}(images={info['images_count']}, annotations={info['annotations_count']}, public={info['public']})"

    def add_image(self,
                  image_url,
                  annotations: List = None):
        if annotations is None:
            annotations = []

        response = self.searcher.pierequest("/add_image_to_dataset",
                                            dataset_id=self.dataset_id,
                                            image_url=image_url,
                                            annotations=annotations)
        if response.get("status") != "ok":
            raise RuntimeError(response.get("message"))

    def remove_image(self, image_url):
        response = self.searcher.pierequest("/remove_image_from_dataset",
                                            dataset_id=self.dataset_id,
                                            image_url=image_url)
        if response.get("status") != "ok":
            raise RuntimeError(response.get("message"))

    def retrieve(self, page=0):
        response = self.searcher.pierequest("/retrieve_from_dataset",
                                            dataset_id=self.dataset_id,
                                            page=page)
        if response.get("status") != "ok":
            raise RuntimeError(response.get("message"))
        return response.get("data", [])

    def export(self, format=None):
        raise NotImplementedError()

    def search(self, query,
               images: List[Image.Image] = None,
               annotations: List[Annotation] = None,
               search_limit=9) -> DataRequest:
        if images is None:
            images = []
        if annotations is None:
            annotations = []

        if search_limit >= 10:
            raise NotImplementedError("Now free search limit is 10 photos")

        response = self.searcher.pierequest("/search",
                                            query=query,
                                            images=[to_base64(im)
                                                    for im in images],
                                            annotations=[ann.to_dict()
                                                         for ann in annotations],
                                            search_limit=search_limit,
                                            dataset_id=self.dataset_id)
        if response.get("status") != "ok":
            raise RuntimeError(response.get("message"))

        return DataRequest(self, response.get("request_id"))

    def deepsearch(self, embedding: np.ndarray,
                   annotations: List[Annotation] = None,
                   search_limit=9):

        if annotations is None:
            annotations = []

        if embedding.shape != (FEATURE_DIMENSION, ):
            raise RuntimeError("Bad embedding shape")

        if search_limit >= 10:
            raise NotImplementedError("Now free search limit is 10 photos")

        response = self.searcher.pierequest("/deepsearch",
                                            embedding=embedding.tolist(),
                                            annotations=[ann.to_dict()
                                                         for ann in annotations],
                                            search_limit=search_limit,
                                            dataset_id=self.dataset_id)
        if response.get("status") != "ok":
            raise RuntimeError(response.get("message"))

        return DataRequest(self, response.get("request_id"))
