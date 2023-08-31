import requests
import json
from PIL import Image
from typing import List
import numpy as np
from .limits import Limits
from .annotations import AnnotationSearch
from .data_request import DataRequest
from .dataset import Dataset
from .settings import FEATURE_DIMENSION
from .utils import to_base64, from_url


class Searcher(object):
    def __init__(self, email, api_key):
        self.email = email
        self.api_key = api_key

    def pierequest(self, endpoint, **data):
        return requests.post("https://console.piedata.ai/api/process/proxy",
                             files={
                                 "piedemo__proxy": (None, json.dumps({
                                     "project_id": "64b61f572e9765980a0640d3",
                                     "direct": endpoint,
                                     "method": "post",
                                 })),
                                 "__pie_json_data": (None, json.dumps({
                                     "email": self.email,
                                     "api_key": self.api_key,
                                     **data
                                 })),
                             }).json()

    def limits(self):
        response = self.pierequest("/limits")
        if response.get("status") != "ok":
            raise RuntimeError(response.get("message"))

        return Limits(response.get("limits", {}))

    def recent_searches(self):
        response = self.pierequest("/recent_searches")
        if response.get("status") != "ok":
            raise RuntimeError(response.get("message"))

        return response.get("recent_searches", [])

    def view_search(self, request_id):
        response = self.pierequest("/view_search",
                                   request_id=request_id)
        if response.get("status") != "ok":
            raise RuntimeError(response.get("message"))

        response.pop('status')
        return {
            "query": response.get('query'),
            "images": [from_url(image_url)
                       for image_url in response.get("images")],
            "annotations": [AnnotationSearch.from_dict(ann)
                            for ann in response.get('annotations', [])]
        }

    def retrieve_data(self, request_id):
        response = self.pierequest("/retrieve",
                                   request_id=request_id)
        if response.get("status") != "ok":
            raise RuntimeError(response.get("message"))
        return response.get("data", [])

    def search(self, query,
               images: List[Image.Image] = None,
               annotations: List[AnnotationSearch] = None,
               search_limit=9) -> DataRequest:
        if images is None:
            images = []
        if annotations is None:
            annotations = []

        if search_limit >= 10:
            raise NotImplementedError("Now free search limit is 10 photos")

        response = self.pierequest("/search",
                                   query=query,
                                   images=[to_base64(im)
                                           for im in images],
                                   annotations=[ann.to_dict()
                                                for ann in annotations],
                                   search_limit=search_limit)
        if response.get("status") != "ok":
            raise RuntimeError(response.get("message"))

        return DataRequest(self, response.get("request_id"))

    def search_similar(self,
                       request_id,
                       data_ids: List[int] = None,
                       search_limit=9) -> DataRequest:

        if data_ids is None:
            data_ids = []

        response = self.pierequest("/search_similar",
                                   request_id=request_id,
                                   data_ids=data_ids,
                                   search_limit=search_limit)
        if response.get("status") != "ok":
            raise RuntimeError(response.get("message"))

        return DataRequest(self, response.get("request_id"))

    def deepsearch(self, embedding: np.ndarray,
                   annotations: List[AnnotationSearch] = None,
                   search_limit=9) -> DataRequest:

        if annotations is None:
            annotations = []

        if embedding.shape != (FEATURE_DIMENSION, ):
            raise RuntimeError("Bad embedding shape")

        if search_limit >= 10:
            raise NotImplementedError("Now free search limit is 10 photos")

        response = self.pierequest("/deepsearch",
                                   embedding=embedding.tolist(),
                                   annotations=[ann.to_dict()
                                                for ann in annotations],
                                   search_limit=search_limit)
        if response.get("status") != "ok":
            raise RuntimeError(response.get("message"))

        return DataRequest(self, response.get("request_id"))

    def dataset_list(self):
        response = self.pierequest("/dataset_list")
        if response.get("status") != "ok":
            raise RuntimeError(response.get("message"))

        return [Dataset(self, dataset_id)
                for dataset_id in response.get("datasets", [])]

    def dataset_shared_list(self):
        response = self.pierequest("/dataset_shared_list")
        if response.get("status") != "ok":
            raise RuntimeError(response.get("message"))

        return [Dataset(self, dataset_id)
                for dataset_id in response.get("datasets", [])]

    def dataset_info(self, dataset_id):
        response = self.pierequest("/dataset_info",
                                   dataset_id=dataset_id)
        if response.get("status") != "ok":
            raise RuntimeError(response.get("message"))

        return response

    def dataset_add(self, dataset_id: str,
                    request_id: str,
                    data_ids: List[int]):
        response = self.pierequest("/add_to_dataset",
                                   dataset_id=dataset_id,
                                   request_id=request_id,
                                   data_ids=data_ids)

        if response.get("status") != "ok":
            raise RuntimeError(response.get("message"))

        return response

    def get_embedding(self, image_url):
        raise NotImplementedError()
