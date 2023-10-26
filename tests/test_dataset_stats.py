from datalake.searcher import Searcher
from datalake.credentials import load_credentials


credentials = load_credentials()
searcher = Searcher(**credentials)

ds = searcher.dataset_list()[0]
print(ds)
for tag in ds.get_tags():
    print(f"Tag: {tag}, count: {ds.count_images_has_tag(tag)}")
