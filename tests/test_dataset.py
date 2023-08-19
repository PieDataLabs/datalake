from datalake.searcher import Searcher
from datalake.credentials import load_credentials
from datalake.annotations import Tag, Polygon


credentials = load_credentials()
searcher = Searcher(**credentials)

print(searcher.dataset_list())
