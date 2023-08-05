import os
import sys


class Searcher(object):
    def __init__(self, email, api_key):
        self.email = email
        self.api_key = api_key

    def limits(self):
        pass

    def search(self, query,
               images,
               annotations):
        return []
