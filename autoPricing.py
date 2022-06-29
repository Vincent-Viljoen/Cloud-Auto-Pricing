import pandas as pd
import numpy as np
import requests

#Making api request and parsing it to json format
r = requests.get(url = "https://prices.azure.com/api/retail/prices?$filter=meterId  eq 'ff595cb7-60f8-4815-8022-adee24f52953'")
data = r.json()
print(data)
