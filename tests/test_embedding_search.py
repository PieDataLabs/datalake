import numpy as np
from time import time
from datalake.searcher import Searcher
from datalake.credentials import load_credentials


credentials = load_credentials()
searcher = Searcher(**credentials)
t1 = time()
print(searcher.deepsearch(np.zeros(512, dtype=np.float32),
                          search_limit=1).wait())
t2 = time()
print(f"Timing: {t2 - t1}")
