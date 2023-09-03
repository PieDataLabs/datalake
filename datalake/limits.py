import os


class Limits(object):
    def __init__(self, data):
        super(Limits, self).__init__()
        self.data = data

    def __repr__(self):
        n_public_datasets = self.data.get("n_public_datasets", 0)
        n_public_images = self.data.get("n_public_images", 0)

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
N Public Datasets: {n_public_datasets}
N Public Images: {n_public_images}
Download Quota: {dq}
Searches Quota: {sq}
"""
