import pandas as pd

data = pd.read_excel('Scenario1.xlsx')

print(data.head())

for i in range(len(data)):
    for j in range(data.loc[i,'Number of Disks']):
        data.loc[i, f'Disk {j+1}'] = data.loc[i,'Total Storage']/data.loc[i,'Number of Disks']

data.to_excel('Scenario1.xlsx')