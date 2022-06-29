import pandas as pd
import numpy as np
import requests

#Choose correct vm


#Select general disk for vm


#Get correct disks

#Making api request and parsing it to json format
r = requests.get(url = "https://prices.azure.com/api/retail/prices?$filter=meterId  eq 'ff595cb7-60f8-4815-8022-adee24f52953'")
data = r.json()
print(data)
print('test 2')

print(x)

#reghard
#vincent
#origin