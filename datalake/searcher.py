import os
import sys
import requests
import json


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
            print(response.get("message"))
            exit()
        return response.get("limits", {})

    def search(self, query,
               images,
               annotations):
        print(self.pierequest("/limits"))

