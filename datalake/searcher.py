import os
import sys
import requests
import json
import io
import base64
from PIL import Image
from typing import List
from .annotations import Annotation
from .data_request import DataRequest


def to_base64(im: Image.Image):
    file_object = io.BytesIO()
    im.save(file_object, 'JPEG')
    file_object.seek(0)
    b64 = base64.b64encode(file_object.read()).decode('utf-8')
    src = f"data:image/jpeg;charset=utf-8;base64, {b64}"
    return src


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

        return response.get("limits", {})

    def recent_searches(self):
        response = self.pierequest("/recent_")
        if response.get("status") != "ok":
            raise RuntimeError(response.get("message"))

        return response.get("limits", {})

    def search(self, query,
               images: List[Image.Image],
               annotations: List[Annotation]):
        response = self.pierequest("/search",
                                   query=query,
                                   images=[to_base64(im)
                                           for im in images],
                                   annotations=[ann.to_dict()
                                                for ann in annotations])
        if response.get("status") != "ok":
            raise RuntimeError(response.get("message"))

        return DataRequest(response.get("request_id"))
