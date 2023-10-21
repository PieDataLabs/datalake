from datalake.searcher import Searcher
from datalake.credentials import load_credentials


credentials = load_credentials()
searcher = Searcher(**credentials)

print(searcher.dataset_list())
