from datalake.searcher import Searcher
from datalake.credentials import load_credentials


credentials = load_credentials()
searcher = Searcher(**credentials)

ds = searcher.dataset_list()[-1]
print(ds)

data_request = searcher.search("Cats")
data_request.wait()
ds.add(data_request, ids=[0, 1])
