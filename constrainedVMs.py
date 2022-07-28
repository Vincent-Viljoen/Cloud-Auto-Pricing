import pandas as pd
import numpy as np
import re
import requests

import warnings
warnings.filterwarnings('ignore')

import asyncio
import aiohttp

const_VMs = pd.read_excel('ConstrainedVMs.xlsx', header=0)
all_VMs = pd.read_excel('Avaliable VMs in SA North.xlsx', header=0)

not_in_SA_North = pd.DataFrame()
count = 0
for i in range(len(const_VMs)):
    x = (all_VMs[const_VMs['Name'].iloc[i] == all_VMs['Name']])
    if len(x) > 0:
        const_VMs.loc[i,'OS_vCPU'] = x['NumberOfCores'].iloc[0]
        const_VMs.loc[i,'MemoryInGb'] = x['MemoryInMb'].iloc[0]/1024
    else:
        not_in_SA_North.loc[count,'Name'] = const_VMs['Name'].iloc[i]
        count = count+1

const_VMs.dropna(inplace=True)
const_VMs['OS_vCPU'] = const_VMs['OS_vCPU'].astype(int)
const_VMs.reset_index(inplace=True, drop=True)

async def main():
    async with aiohttp.ClientSession() as session:
        tasks1 = []
        tasks2 = []
        tasks3 = []
        tasks4 = []
        tasks5 = []
        for i in range(len(const_VMs)):
            armSkuName = const_VMs['Name'].iloc[i]
            task1 = asyncio.ensure_future(get_BASE_VM(session, armSkuName, i))
            tasks1.append(task1)

            # vCPU = re.findall('[0-9]+', const_VMs['Name'].iloc[i])[0]
            # const_VMs.loc[i,'OS ID'] = vCPU
            vCPU = const_VMs['OS_vCPU'].iloc[i]
            task2 = asyncio.ensure_future(get_Windows_License(session, vCPU, i))
            tasks2.append(task2)

            vCPU = const_VMs['vCPU'].iloc[i]
            task3 = asyncio.ensure_future(get_Windows_SQL_Enterprise_License(session, vCPU, i))
            tasks3.append(task3)

            task4 = asyncio.ensure_future(get_Windows_SQL_Standard_License(session, vCPU, i))
            tasks4.append(task4)

        view_counts1 = await asyncio.gather(*tasks1)
        view_counts2 = await asyncio.gather(*tasks2)
        view_counts3 = await asyncio.gather(*tasks3)
        view_counts4 = await asyncio.gather(*tasks4)
######################################################################################################################################################
# Base VM License
######################################################################################################################################################
async def get_BASE_VM(session, armSkuName, i):

    url = f"https://prices.azure.com/api/retail/prices?$filter= armRegionName eq 'southafricanorth' and armSkuName eq '{armSkuName}' and priceType eq 'Reservation' and reservationTerm eq '3 Years'"

    async with session.get(url) as response:
        result_data = await response.json()
        results = result_data['Items']
        if len(results) > 0:
            viewCount = results[0]['meterId']
            const_VMs.loc[i,'PAYG/1Y/3Y ID'] = viewCount
######################################################################################################################################################
# Windows License
######################################################################################################################################################
async def get_Windows_License(session, vCPU, i):

    url = f"https://prices.azure.com/api/retail/prices?$filter=productName eq 'Windows Server' and priceType eq 'Consumption' and meterName eq '{vCPU} vCPU VM License' and unitOfMeasure eq '1 Hour'"

    async with session.get(url) as response:
        result_data = await response.json()
        results = result_data['Items']
        if len(results) > 0:
            viewCount = results[0]['meterId']
            const_VMs.loc[i,'Windows License'] = viewCount
######################################################################################################################################################
# SQL Server Enterprise
######################################################################################################################################################
async def get_Windows_SQL_Enterprise_License(session, vCPU, i):

    if vCPU < 5:
        url = f"https://prices.azure.com/api/retail/prices?$filter=productName eq 'SQL Server Enterprise' and priceType eq 'Consumption' and meterName eq '1-4 vCPU VM License' and unitOfMeasure eq '1 Hour'"
    else:
        url = f"https://prices.azure.com/api/retail/prices?$filter=productName eq 'SQL Server Enterprise' and priceType eq 'Consumption' and meterName eq '{vCPU} vCPU VM License' and unitOfMeasure eq '1 Hour'"

    async with session.get(url) as response:
        result_data = await response.json()
        results = result_data['Items']
        if len(results) > 0:
            viewCount = results[0]['meterId']
            const_VMs.loc[i,'SQL Enterprise License'] = viewCount

######################################################################################################################################################
# SQL Server Standard
######################################################################################################################################################
async def get_Windows_SQL_Standard_License(session, vCPU, i):

    if vCPU < 5:
        url = f"https://prices.azure.com/api/retail/prices?$filter=productName eq 'SQL Server Standard' and priceType eq 'Consumption' and meterName eq '1-4 vCPU VM License' and unitOfMeasure eq '1 Hour'"
    else:
        url = f"https://prices.azure.com/api/retail/prices?$filter=productName eq 'SQL Server Standard' and priceType eq 'Consumption' and meterName eq '{vCPU} vCPU VM License' and unitOfMeasure eq '1 Hour'"

    async with session.get(url) as response:
        result_data = await response.json()
        results = result_data['Items']
        if len(results) > 0:
            viewCount = results[0]['meterId']
            const_VMs.loc[i,'SQL Standard License'] = viewCount

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(main())

async def main():
    async with aiohttp.ClientSession() as session:
        tasks1 = []
        tasks2 = []
        tasks3 = []
        tasks4 = []
        tasks5 = []
        tasks6 = []
        for i in range(len(const_VMs)):

          meterID = const_VMs['PAYG/1Y/3Y ID'].iloc[i]
          term = '3 Years'
          armSkuName = const_VMs['Name'].iloc[i]
          task1 = asyncio.ensure_future(get_3Year(session, armSkuName, term, meterID, i))
          tasks1.append(task1)
           
          meterID = const_VMs['PAYG/1Y/3Y ID'].iloc[i]
          term = '1 Year'
          armSkuName = const_VMs['Name'].iloc[i]
          task2 = asyncio.ensure_future(get_1Year(session, armSkuName, term, meterID, i))
          tasks2.append(task2) 

          type = 'Consumption'
          task3 = asyncio.ensure_future(get_PAYG(session, armSkuName, type, meterID, i))
          tasks3.append(task3)

          meterID = const_VMs['Windows License'].iloc[i]
          type = 'Consumption'
          task4 = asyncio.ensure_future(get_Windows_OS(session, type, meterID, i))
          tasks4.append(task4)

          meterID = const_VMs['SQL Enterprise License'].iloc[i]
          type = 'Consumption'
          task5 = asyncio.ensure_future(get_Enterprise_SQL(session, type, meterID, i))
          tasks5.append(task5)

          meterID = const_VMs['SQL Standard License'].iloc[i]
          type = 'Consumption'
          task6 = asyncio.ensure_future(get_Standard_SQL(session, type, meterID, i))
          tasks6.append(task6)


        view_counts1 = await asyncio.gather(*tasks1)
        view_counts2 = await asyncio.gather(*tasks2)
        view_counts3 = await asyncio.gather(*tasks3)
        view_counts4 = await asyncio.gather(*tasks4)
        view_counts5 = await asyncio.gather(*tasks5)
        view_counts6 = await asyncio.gather(*tasks6)
######################################################################################################################################################
# Get 3 Year Reserve Pricing
######################################################################################################################################################
print("Get 3 Year Reserved Pricing\n ...................................")
async def get_3Year(session, armSkuName, term, meterID, i):
    apiString = "https://prices.azure.com/api/retail/prices?$filter="
    url = f"{apiString} meterId eq '{meterID}' and reservationTerm eq '{term}' and armSkuName eq '{armSkuName}'"

    async with session.get(url) as response:
        result_data = await response.json()
        results = result_data['Items']
        if len(results) > 0:
            viewCount = results[0]['retailPrice']
            const_VMs.loc[i,'3Year'] = viewCount/36
            
######################################################################################################################################################
# Get 1 Year Reserve Pricing
######################################################################################################################################################
print("Get 3 Year Reserved Pricing\n ...................................")
async def get_1Year(session, armSkuName, term, meterID, i):
    apiString = "https://prices.azure.com/api/retail/prices?$filter="
    url = f"{apiString} meterId eq '{meterID}' and reservationTerm eq '{term}' and armSkuName eq '{armSkuName}'"

    async with session.get(url) as response:
        result_data = await response.json()
        results = result_data['Items']
        if len(results) > 0:
            viewCount = results[0]['retailPrice']
            const_VMs.loc[i,'1Year'] = viewCount/12

######################################################################################################################################################
# Get VM Pay As You Go Pricing
######################################################################################################################################################
print("Get PAYG Pricing\n ...................................")
async def get_PAYG(session, armSkuName, type, meterID, i):
    apiString = "https://prices.azure.com/api/retail/prices?$filter="
    url = f"{apiString} meterId eq '{meterID}' and priceType eq '{type}' and armSkuName eq '{armSkuName}'"

    async with session.get(url) as response:
        result_data = await response.json()
        results = result_data['Items']
        if len(results) > 0:
            viewCount = results[0]['retailPrice']
            const_VMs.loc[i,'PAYG'] = viewCount*730
######################################################################################################################################################
# Get Windows OS License Pricing
######################################################################################################################################################
print("Get Windows OS License Pricing\n ...................................")
async def get_Windows_OS(session, type, meterID, i):
    apiString = "https://prices.azure.com/api/retail/prices?$filter="
    url = f"{apiString} meterId eq '{meterID}' and priceType eq '{type}'"

    async with session.get(url) as response:
        result_data = await response.json()
        results = result_data['Items']
        if len(results) > 0:
            viewCount = results[0]['retailPrice']
            const_VMs.loc[i,'Windows OS'] = viewCount*730
######################################################################################################################################################
# Get Enterprise Windows SQL Pricing
######################################################################################################################################################
print("Get Windows SQL Pricing\n ...................................")
async def get_Enterprise_SQL(session, type, meterID, i):
    apiString = "https://prices.azure.com/api/retail/prices?$filter="
    url = f"{apiString} meterId eq '{meterID}' and priceType eq '{type}'"

    async with session.get(url) as response:
        result_data = await response.json()
        results = result_data['Items']
        if len(results) > 0:
            viewCount = results[0]['retailPrice']
            const_VMs.loc[i,'Windows Enterprise SQL'] = viewCount*730
######################################################################################################################################################
# Get Standard SQL Pricing
######################################################################################################################################################
print("Get Windows SQL Pricing\n ...................................")
async def get_Standard_SQL(session, type, meterID, i):
    apiString = "https://prices.azure.com/api/retail/prices?$filter="
    url = f"{apiString} meterId eq '{meterID}' and priceType eq '{type}'"

    async with session.get(url) as response:
        result_data = await response.json()
        results = result_data['Items']
        if len(results) > 0:
            viewCount = results[0]['retailPrice']
            const_VMs.loc[i,'Windows Standard SQL'] = viewCount*730
######################################################################################################################################################
# Get P10 Pricing
######################################################################################################################################################
print("Get P10 Pricing\n ...................................")
apiString = "https://prices.azure.com/api/retail/prices?$filter="
url = f"{apiString} meterId eq '4b305e71-6111-4612-918a-d4c40867b2fb' and priceType eq 'Consumption'"

response = requests.get(url)
result_data = response.json()
results = result_data['Items']
if len(results) > 0:
    p10Price = results[0]['retailPrice']

print(p10Price)
        

print(const_VMs.head())

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(main())

const_VMs['SQL Standard'] = const_VMs['PAYG'] + const_VMs['Windows Standard SQL']  + const_VMs['Windows OS'] + p10Price
const_VMs['SQL Enterprise'] = const_VMs['PAYG'] + const_VMs['Windows Enterprise SQL']  + const_VMs['Windows OS'] + p10Price
const_VMs['SQL Standard 1 Year RI'] = const_VMs['1Year'] + const_VMs['Windows Standard SQL']  + const_VMs['Windows OS'] + p10Price
const_VMs['SQL Enterprise 1 Year RI'] = const_VMs['1Year'] + const_VMs['Windows Enterprise SQL']  + const_VMs['Windows OS'] + p10Price
const_VMs['SQL Standard 3 Year RI'] = const_VMs['3Year'] + const_VMs['Windows Standard SQL']  + const_VMs['Windows OS'] + p10Price
const_VMs['SQL Enterprise 3 Year RI'] = const_VMs['3Year'] + const_VMs['Windows Enterprise SQL']  + const_VMs['Windows OS'] + p10Price
const_VMs['SQL Hybrid BYOL'] = const_VMs['PAYG'] + p10Price

const_VMs.drop(['PAYG/1Y/3Y ID','Windows License','SQL Enterprise License','SQL Standard License','1Year','PAYG','3Year','Windows Standard SQL', 'Windows Enterprise SQL' , 'Windows OS' ], inplace=True, axis=1)

with pd.ExcelWriter('output.xlsx') as writer:
    const_VMs.to_excel(writer, sheet_name='VMs in SA North')
    not_in_SA_North.to_excel(writer, sheet_name='VMs not in SA North')
