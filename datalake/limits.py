import os


class Limits(object):
    def __init__(self, data):
        super(Limits, self).__init__()
        self.data = data

    def __repr__(self):
        dq = self.data.get("download_quote", -1)
        if dq == -1:
            dq = "Unlimited"
        else:
            dq = f"{dq} per hour"
        sq = self.data.get("searches_quote", -1)
        if sq == -1:
            sq = "Unlimited"
        else:
            sq = f"{sq} per hour"
        return f"""
Download Quota: {dq}
Searches Quota: {sq}
"""
