import pandas as pd
import numpy as np
import requests

#import data
df = pd.read_excel('Bryte costing.xlsx', sheet_name = 'Sheet4')
#Remove first row, it is blank
vmSpecs = pd.read_excel('Avaliable VMs in SA North.xlsx').iloc[1:,]

#Add series to skuNAME
for i in range(len(df)):
    ratio = df['Size MB'].iloc[i]/1024/df['CPUs'].iloc[i]
    if pd.isna(ratio):
        skuNAME = np.nan
    elif ratio <= 2:
        skuNAME = 'F'
    elif ratio < 8:
        skuNAME = 'D'
    else:
        skuNAME = 'E'

print(vmSpecs)

#Link vm IDs with vm Name, CPUs and RAM

#Choose correct vm

#Make api request and parsing it to json format

#vmId needs to be dynamic bases on the requirements
# skuNAME = "'F2'"
# vmID = "'dc7ab2e8-27b1-4b96-b55b-f0b09f5f68a2'"
# vmURL = f"https://prices.azure.com/api/retail/prices?$filter=meterId  eq {vmID} and SkuName eq {skuNAME}"
# r = requests.get(url = vmURL)
# data = r.json()

#Select general disk for vm



#Get correct disks

