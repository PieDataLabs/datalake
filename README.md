# datalake
DataLake product cli  
  
## Installation  
`pip install piedatalake`  
  
## Getting started  
`datalaker auth`    

Visit the page:  
https://console.piedata.ai/proxy?project_id=64b61f572e9765980a0640d3&action=/login  
Click on your logo (the most right icon at navbar)  
Paste here email and api key:  
  
email: ########@piedata.ai  
API_KEY: ##########  

Credentials successfully saved!  

`datalaker search "Rabbits" --image ./demo/rabbit.jpg --annotation polygon[rabbit,#FF0000]`  

View results in a file: `Rabbits.json`  


## Python api  

```python
from datalake.searcher import Searcher
from datalake.annotations import Tag, Polygon

data_request = searcher.search("Rabbits",
                               annotations=[Tag("rabbit")],
                               search_limit=10)

print(data_request.wait())
```

