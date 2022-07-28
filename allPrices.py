#Add SQL VMs

import pandas as pd
import numpy as np
import requests
import re

import warnings
warnings.filterwarnings('ignore')

import asyncio
import aiohttp
######################################################################################################################################################
# importing data
######################################################################################################################################################
print("Importing Data\n ...................................")
VMs = pd.read_excel('Avaliable VMs in SA North.xlsx')
Disks = pd.read_excel('Avaliable Storage Disks in SA North.xlsx')

VMs = VMs[VMs['Name'].str.contains("-")==False]
VMs.reset_index(drop = True, inplace = True)
######################################################################################################################################################
# Async Get License
######################################################################################################################################################
print("Get Licensing\n ...................................")
async def main():
    async with aiohttp.ClientSession() as session:
        tasks1 = []
        tasks2 = []
        tasks3 = []
        tasks4 = []
        tasks5 = []
        for i in range(len(VMs)):
            armSkuName = VMs['Name'].iloc[i]
            task1 = asyncio.ensure_future(get_BASE_VM(session, armSkuName, i))
            tasks1.append(task1)

            # vCPU = re.findall('[0-9]+', VMs['Name'].iloc[i])[0]
            vCPU = VMs['NumberOfCores'].iloc[i]
            task2 = asyncio.ensure_future(get_Windows_License(session, vCPU, i))
            tasks2.append(task2)

            # vCPU = VMs['NumberOfCores'].iloc[i]
            task3 = asyncio.ensure_future(get_Windows_SQL_License(session, vCPU, i))
            tasks3.append(task3)

            task4 = asyncio.ensure_future(get_LinuxRedHat_License(session, vCPU, i))
            tasks4.append(task4)

        for j in range(len(Disks)):
            meterName = Disks['Disk Name'].iloc[j]
            disk = Disks['Disk Name'].str[0].iloc[j]
            task5 = asyncio.ensure_future(get_Disk_License(session, meterName, disk, j))
            tasks5.append(task5)

        view_counts1 = await asyncio.gather(*tasks1)
        view_counts2 = await asyncio.gather(*tasks2)
        view_counts3 = await asyncio.gather(*tasks3)
        view_counts4 = await asyncio.gather(*tasks4)
        view_counts5 = await asyncio.gather(*tasks5)
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
            VMs.loc[i,'PAYG/1Y/3Y ID'] = viewCount
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
            VMs.loc[i,'Windows License'] = viewCount
######################################################################################################################################################
# Windows SQL License
######################################################################################################################################################
async def get_Windows_SQL_License(session, vCPU, i):

    if vCPU < 5:
        url = f"https://prices.azure.com/api/retail/prices?$filter=productName eq 'SQL Server Enterprise' and priceType eq 'Consumption' and meterName eq '1-4 vCPU VM License' and unitOfMeasure eq '1 Hour'"
    else:
        url = f"https://prices.azure.com/api/retail/prices?$filter=productName eq 'SQL Server Enterprise' and priceType eq 'Consumption' and meterName eq '{vCPU} vCPU VM License' and unitOfMeasure eq '1 Hour'"

    async with session.get(url) as response:
        result_data = await response.json()
        results = result_data['Items']
        if len(results) > 0:
            viewCount = results[0]['meterId']
            VMs.loc[i,'Windows SQL License'] = viewCount
######################################################################################################################################################
# Linux Redhat License
######################################################################################################################################################
async def get_LinuxRedHat_License(session, vCPU, i):

    if vCPU < 5:
        url = f"https://prices.azure.com/api/retail/prices?$filter=productName eq 'Red Hat Enterprise Linux' and priceType eq 'Consumption' and meterName eq '1 vCPU VM License' and armSkuName eq 'RHEL_1-4_vCPU'"
    else:
        url = f"https://prices.azure.com/api/retail/prices?$filter=productName eq 'Red Hat Enterprise Linux' and priceType eq 'Consumption' and meterName eq '12 vCPU VM License' and armSkuName eq 'RHEL_5plus_vCPU'"

    async with session.get(url) as response:
        result_data = await response.json()
        results = result_data['Items']
        if len(results) > 0:
            viewCount = results[0]['meterId']
            VMs.loc[i,'Red Hat Enterprise Linux License'] = viewCount
######################################################################################################################################################
# Disks License
######################################################################################################################################################
async def get_Disk_License(session, meterName, disk, j):

    if disk == 'E':
        url = f"https://prices.azure.com/api/retail/prices?$filter=armRegionName eq 'southafricanorth' and serviceName eq 'Storage' and meterName eq '{meterName}' and priceType eq 'Consumption' and productName eq 'Standard SSD Managed Disks'"
    else:
        url = f"https://prices.azure.com/api/retail/prices?$filter=armRegionName eq 'southafricanorth' and serviceName eq 'Storage' and meterName eq '{meterName}' and priceType eq 'Consumption' and productName eq 'Premium SSD Managed Disks'"

    async with session.get(url) as response:
        result_data = await response.json()
        results = result_data['Items']
        if len(results) > 0:
            viewCount = results[0]['meterId']
            Disks.loc[j,'License'] = viewCount

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(main())
######################################################################################################################################################
# Async get Pricing
######################################################################################################################################################
# VMs['osAPI'] = np.nan
# VMs['osAPI'] = VMs['Red Hat Enterprise Linux License'].combine_first(VMs['Windows License'])

async def main():
    async with aiohttp.ClientSession() as session:
        tasks1 = []
        tasks2 = []
        tasks3 = []
        tasks4 = []
        tasks5 = []
        tasks6 = []
        tasks7 = []
        for i in range(len(VMs)):

          meterID = VMs['PAYG/1Y/3Y ID'].iloc[i]
          term = '3 Years'
          armSkuName = VMs['Name'].iloc[i]
          task1 = asyncio.ensure_future(get_3Year(session, armSkuName, term, meterID, i))
          tasks1.append(task1)

          term = '1 Year'
          task7 = asyncio.ensure_future(get_1Year(session, armSkuName, term, meterID, i))
          tasks7.append(task7)

          type = 'Consumption'
          task2 = asyncio.ensure_future(get_PAYG(session, armSkuName, type, meterID, i))
          tasks2.append(task2)

          meterID = VMs['Windows License'].iloc[i]
          type = 'Consumption'
          task3 = asyncio.ensure_future(get_Windows_OS(session, type, meterID, i))
          tasks3.append(task3)

          meterID = VMs['Red Hat Enterprise Linux License'].iloc[i]
          type = 'Consumption'
          task6 = asyncio.ensure_future(get_Linux_OS(session, type, meterID, i))
          tasks6.append(task6)

          meterID = VMs['Windows SQL License'].iloc[i]
          type = 'Consumption'
          task4 = asyncio.ensure_future(get_Win_SQL(session, type, meterID, i))
          tasks4.append(task4)

        for j in range(len(Disks)):
          meterID = Disks['License'].iloc[j]
          type = 'Consumption'
          task5 = asyncio.ensure_future(get_Disks(session, type, meterID, j))
          tasks5.append(task5)

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
            VMs.loc[i,'3Year'] = viewCount/36
######################################################################################################################################################
# Get 1 Year Reserve Pricing
######################################################################################################################################################
print("Get 1 Year Reserved Pricing\n ...................................")
async def get_1Year(session, armSkuName, term, meterID, i):
    apiString = "https://prices.azure.com/api/retail/prices?$filter="
    url = f"{apiString} meterId eq '{meterID}' and reservationTerm eq '{term}' and armSkuName eq '{armSkuName}'"

    async with session.get(url) as response:
        result_data = await response.json()
        results = result_data['Items']
        if len(results) > 0:
            viewCount = results[0]['retailPrice']
            VMs.loc[i,'1Year'] = viewCount/12
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
            VMs.loc[i,'PAYG'] = viewCount*730
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
            VMs.loc[i,'Windows OS'] = viewCount*730
######################################################################################################################################################
# Get Linux OS License Pricing
######################################################################################################################################################
print("Get Linux OS License Pricing\n ...................................")
async def get_Linux_OS(session, type, meterID, i):
    apiString = "https://prices.azure.com/api/retail/prices?$filter="
    url = f"{apiString} meterId eq '{meterID}' and priceType eq '{type}'"

    async with session.get(url) as response:
        result_data = await response.json()
        results = result_data['Items']
        if len(results) > 0:
            viewCount = results[0]['retailPrice']
            VMs.loc[i,'LinuxOS'] = viewCount*730
######################################################################################################################################################
# Get Windows SQL Pricing
######################################################################################################################################################
print("Get Windows SQL Pricing\n ...................................")
async def get_Win_SQL(session, type, meterID, i):
    apiString = "https://prices.azure.com/api/retail/prices?$filter="
    url = f"{apiString} meterId eq '{meterID}' and priceType eq '{type}'"

    async with session.get(url) as response:
        result_data = await response.json()
        results = result_data['Items']
        if len(results) > 0:
            viewCount = results[0]['retailPrice']
            VMs.loc[i,'Windows SQL'] = viewCount*730
######################################################################################################################################################
# Get Disks Pricing
######################################################################################################################################################
print("Get Disks Pricing\n ...................................")
async def get_Disks(session, type, meterID, i):
    apiString = "https://prices.azure.com/api/retail/prices?$filter="
    url = f"{apiString} meterId eq '{meterID}' and priceType eq '{type}'"

    async with session.get(url) as response:
        result_data = await response.json()
        results = result_data['Items']
        if len(results) > 0:
            viewCount = results[0]['retailPrice']
            Disks.loc[i,'Pricing'] = viewCount

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(main())

print(VMs)
print(VMs.columns)

with pd.ExcelWriter('IDs.xlsx') as writer:
    VMs.to_excel(writer, sheet_name='VMs')
    Disks.to_excel(writer, sheet_name='Disks')