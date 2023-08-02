import os
import sys


class Searcher(object):
    def __init__(self, api_key):
        self.api_key = api_key

    def limits(self):
        pass

    def search(self, query,
               images,
               annotations):
        return []
