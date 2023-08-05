import os
import sys
import requests
import json
import io
import base64
from urllib.request import urlopen
from PIL import Image
from typing import List
from .limits import Limits
from .annotations import Annotation
from .data_request import DataRequest


def to_base64(im: Image.Image):
    file_object = io.BytesIO()
    im.save(file_object, 'JPEG')
    file_object.seek(0)
    b64 = base64.b64encode(file_object.read()).decode('utf-8')
    src = f"data:image/jpeg;charset=utf-8;base64, {b64}"
    return src


def from_url(image_url: str):
    with urlopen(image_url) as url:
        return Image.open(url).convert("RGB")


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
            "annotations": [Annotation.from_dict(ann)
                            for ann in response.get('annotations', [])]
        }

    def retrieve_data(self, request_id):
        response = self.pierequest("/retrieve",
                                   request_id=request_id)
        if response.get("status") != "ok":
            raise RuntimeError(response.get("message"))
        return response.get("data", [])

    def search(self, query,
               images: List[Image.Image],
               annotations: List[Annotation],
               search_limit=10):
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
