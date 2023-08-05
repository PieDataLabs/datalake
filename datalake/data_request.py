import os


class DataRequest(object):
    def __init__(self, request_id: str):
        super(DataRequest, self).__init__()
        self.request_id = request_id

    def __repr__(self):
        return f"DataRequest({self.request_id})"
