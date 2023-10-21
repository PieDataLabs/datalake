from datalake.searcher import Searcher
from datalake.credentials import load_credentials
from datalake.annotations import TagSearch


credentials = load_credentials()
searcher = Searcher(**credentials)

data_request = searcher.search("Rabbits",
                               annotations=[TagSearch("rabbit")],
                               search_limit=9)

print(data_request)
data_request.wait(2)
similar_request = data_request.similar([0, 1])
print(similar_request)
print(similar_request.wait())
