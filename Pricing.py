import pandas as pd
import numpy as np

import asyncio
import aiohttp

import requests

import warnings
warnings.filterwarnings('ignore')
######################################################################################################################################################
# importing data
######################################################################################################################################################
print("Importing data\n ...................................'")
input = pd.read_excel('Bryte costing.xlsx', sheet_name = "Sheet5")
VM_IDs = pd.read_excel('IDs.xlsx', sheet_name = 'VMs')
Disk_IDs = pd.read_excel('IDs.xlsx', sheet_name = 'Disks')
######################################################################################################################################################
# Getting best Azure VM for each input VM
######################################################################################################################################################
print("Searching for best VMs\n ...................................'")
input['ratio'] = input['Size MB']/1024/input['CPUs']

VMdf = pd.DataFrame()

VMdf['vm'] = input['VM']
VMdf['OS according to the VMware Tools'] = input['OS according to the VMware Tools']

for i in range(len(input)):
  if pd.isna(input.loc[i,'ratio']):
      VMdf.loc[i,'Series'] = np.nan
  elif input.loc[i,'ratio'] <= 2:
      VMdf.loc[i,'Series'] = 'F'
  elif input.loc[i,'ratio'] < 8:
      VMdf.loc[i,'Series']  = 'D'
  else:
      VMdf.loc[i,'Series']  = 'E'

for i in range(len(input)):
  temp = VM_IDs[VM_IDs['Name'].str.split(pat='_',expand=True)[1].str[0] == VMdf['Series'].iloc[i]]
  VMdf.loc[i,'azureVM'] = temp[temp['MemoryInMb'] >= input['Size MB'].iloc[i]]['Name'].iloc[0]
  if input['CPUs'].iloc[i] > VM_IDs[VM_IDs['Name'] == VMdf['azureVM'].iloc[i]]['NumberOfCores'].iloc[0]:
    VMdf.loc[i,'azureVM'] = temp[temp['MemoryInMb'] >= input['Size MB'].iloc[i]]['Name'].iloc[1]
######################################################################################################################################################
# Identifying Licenses needed for each VM
######################################################################################################################################################
print("Determining Licenses\n ...................................'")

# VMdf = pd.merge(VMdf[['vm',	'OS according to the VMware Tools',	'Series',	'azureVM']], VM_IDs[['MaxDataDiskCount', 'MemoryInMb', 'Name', 'NumberOfCores','OsDiskSizeInMb', 'ResourceDiskSizeInMb', 'Windows License','Windows SQL License', 'PAYG/1Y/3Y ID','Red Hat Enterprise Linux License']], how = "left", left_on='azureVM', right_on='Name')

licenses = {
    
    'Windows': { 'codes': ['windows'],
      #SQL otherwise normal Windows OS
      'Type': {'SQL': ['sql']}},

    'Linux': { 'codes': ['linux'],
                      
      'Type': {'Ubuntu': ['ubuntu'], 
               'Red Hat': ['linux','red','hat'], 
               'SQL': ['sql','oracle'],
               'SUSE': ['suse']}} 
}


for i in range(len(VMdf)):
  if  pd.notna(VMdf.loc[i,'OS according to the VMware Tools']):

    #Base price API call ref
    VMdf.loc[i,'Base'] = VM_IDs[VM_IDs['Name'] == VMdf['azureVM'].iloc[i]]['PAYG/1Y/3Y ID'].iloc[0]

    VMdf['Windows License'] = np.nan
    VMdf['Windows SQL License'] = np.nan
    VMdf['Red Hat Enterprise Linux License'] = np.nan
    

    #Check if VM is Windows
    if any(code in VMdf.loc[i,'OS according to the VMware Tools'].lower() for code in licenses['Windows']['codes']):
      VMdf.loc[i,'Windows License'] = VM_IDs[VM_IDs['Name'] == VMdf['azureVM'].iloc[i]]['Windows License'].iloc[0]
      if any(code in VMdf.loc[i,'OS according to the VMware Tools'].lower() for code in licenses['Windows']['Type']['SQL']) or any(code in VMdf.loc[i,'vm'].lower() for code in licenses['Windows']['Type']['SQL']):
        VMdf.loc[i,'Windows SQL License'] = VM_IDs[VM_IDs['Name'] == VMdf['azureVM'].iloc[i]]['Windows SQL License'].iloc[0]
    #Check if VM is Linux
    elif any(code in VMdf.loc[i,'OS according to the VMware Tools'].lower() for code in licenses['Linux']['codes']):
        if any(code in VMdf.loc[i,'OS according to the VMware Tools'].lower() for code in licenses['Linux']['Type']['Red Hat']):
          VMdf.loc[i,'Red Hat Enterprise Linux License'] = VM_IDs[VM_IDs['Name'] == VMdf['azureVM'].iloc[i]]['Red Hat Enterprise Linux License'].iloc[0]
        # elif any(code in VMdf.loc[i,'OS according to the VMware Tools'].lower() for code in licenses['Linux']['Type']['SUSE']):
        #   VMdf.loc[i,'SUSE Linux Enterprise'] = ref[ref['Name'] == VMdf['azureVM'].iloc[i]]['SUSE Linux Enterprise'].iloc[0]
######################################################################################################################################################
# Getting best Azure Disk for each input Disk
######################################################################################################################################################
print("Searching for best Disks\n ...................................'")
disks = []
priority = []
colNames = [x for x in input.columns if 'Disk' in x]

# VM	OS according to the VMware Tools

for col in colNames:
  for i in range(len(input)):
    if pd.notna(input.loc[i,col]):
      disks.append(input.loc[i,col])
      if 'sql' in input.loc[i,'VM'].lower():
        priority.append(1)
      else:
        priority.append(0)

disksDF = pd.DataFrame({'MemoryInGb':disks, 'Premium': priority})

for i in range(len(disksDF)):

  #Check for premium
  if disksDF.loc[i,'Premium'] == 0:
    temp = Disk_IDs[Disk_IDs['Name'].str.contains(pat = 'E')]
    disksDF.loc[i,'azureDisk'] = temp[temp['MemoryInGb'] >= disksDF['MemoryInGb'].iloc[i]]['Name'].iloc[0]
  else:
    temp = Disk_IDs[Disk_IDs['Name'].str.contains(pat = 'P')]
    disksDF.loc[i,'azureDisk'] = temp[temp['MemoryInGb'] >= disksDF['MemoryInGb'].iloc[i]]['Name'].iloc[0]

for i in range(len(disksDF)):
  disksDF.loc[i,'ID'] = Disk_IDs[Disk_IDs['Name'] == disksDF['azureDisk'].iloc[i]]['License'].iloc[0]
######################################################################################################################################################
# Async API calls
######################################################################################################################################################

VMdf['osAPI'] = np.nan
VMdf['osAPI'] = VMdf['Red Hat Enterprise Linux License'].combine_first(VMdf['Windows License'])

async def main():
    async with aiohttp.ClientSession() as session:
        tasks1 = []
        tasks2 = []
        tasks3 = []
        tasks4 = []
        tasks5 = []
        for i in range(len(input)):

          meterID = VMdf['Base'].iloc[i]
          term = '3 Years'
          armSkuName = VMdf['azureVM'].iloc[i]
          task1 = asyncio.ensure_future(get_3Year(session, armSkuName, term, meterID, i))
          tasks1.append(task1)

          type = 'Consumption'
          task2 = asyncio.ensure_future(get_PAYG(session, armSkuName, type, meterID, i))
          tasks2.append(task2)

          meterID = VMdf['osAPI'].iloc[i]
          type = 'Consumption'
          task3 = asyncio.ensure_future(get_OS(session, type, meterID, i))
          tasks3.append(task3)

          meterID = VMdf['Windows SQL License'].iloc[i]
          type = 'Consumption'
          task4 = asyncio.ensure_future(get_Win_SQL(session, type, meterID, i))
          tasks4.append(task4)

        for j in range(len(disksDF)):
          meterID = disksDF['ID'].iloc[j]
          type = 'Consumption'
          task5 = asyncio.ensure_future(get_Disks(session, type, meterID, j))
          tasks5.append(task5)

        view_counts1 = await asyncio.gather(*tasks1)
        view_counts2 = await asyncio.gather(*tasks2)
        view_counts3 = await asyncio.gather(*tasks3)
        view_counts4 = await asyncio.gather(*tasks4)
        view_counts5 = await asyncio.gather(*tasks5)

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
            VMdf.loc[i,'3Year'] = viewCount/36
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
            VMdf.loc[i,'PAYG'] = viewCount*730
######################################################################################################################################################
# Get VM OS License Pricing
######################################################################################################################################################
print("Get OS License Pricing\n ...................................")
async def get_OS(session, type, meterID, i):
    apiString = "https://prices.azure.com/api/retail/prices?$filter="
    url = f"{apiString} meterId eq '{meterID}' and priceType eq '{type}'"

    async with session.get(url) as response:
        result_data = await response.json()
        results = result_data['Items']
        if len(results) > 0:
            viewCount = results[0]['retailPrice']
            VMdf.loc[i,'OS'] = viewCount*730
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
            VMdf.loc[i,'Windows SQL'] = viewCount*730
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
            disksDF.loc[i,'Pricing'] = viewCount

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(main())

VMdf['Total'] = VMdf['OS'] + VMdf['PAYG'] + VMdf['3Year']

######################################################################################################################################################
# Get 3 Year Reserve Pricing
######################################################################################################################################################
# print("Get 3 Year Reserved Pricing\n ...................................'")
# apiString = "https://prices.azure.com/api/retail/prices?$filter="
# for i in range(len(input)):
#   if pd.notna(VMdf['Base'].iloc[i]):
#     meterID = VMdf['Base'].iloc[i]
#     term = '3 Years'
#     armSkuName = VMdf['azureVM'].iloc[i]
#     vmAPI = f"{apiString} meterId eq '{meterID}' and reservationTerm eq '{term}' and armSkuName eq '{armSkuName}'"
#     response = requests.get(f"{vmAPI}")
#     dto = response.json()
#     retailPrice = dto['Items'][0]['retailPrice']
#     VMdf.loc[i,'3Year'] = retailPrice/36
######################################################################################################################################################
# Get VM Pay As You Go Pricing
######################################################################################################################################################
# print("Get PAYG Pricing\n ...................................'")
# apiString = "https://prices.azure.com/api/retail/prices?$filter="

# for i in range(len(input)):
#   if pd.notna(VMdf['Base'].iloc[i]):
#     meterID = VMdf['Base'].iloc[i]
#     type = 'Consumption'
#     armSkuName = VMdf['azureVM'].iloc[i]
#     vmAPI = f"{apiString} meterId eq '{meterID}' and priceType eq '{type}' and armSkuName eq '{armSkuName}'"
#     response = requests.get(f"{vmAPI}")
#     dto = response.json()
#     retailPrice = dto['Items'][0]['retailPrice']
#     VMdf.loc[i,'PAYG'] = retailPrice*730

######################################################################################################################################################
# Get VM OS License Pricing
######################################################################################################################################################
# print("Get OS License Pricing\n ...................................'")
# VMdf['osAPI'] = np.nan
# VMdf['osAPI'] = VMdf['Red Hat Enterprise Linux License'].combine_first(VMdf['Windows License'])

# apiString = "https://prices.azure.com/api/retail/prices?$filter="
# VMdf['osPricing'] = np.nan
# for i in range(len(input)):
#     if pd.notna(VMdf['osAPI'].iloc[i]): 
#         meterID = VMdf['osAPI'].iloc[i]
#         type = 'Consumption'
#         osAPI = f"{apiString} meterId eq '{meterID}' and priceType eq '{type}'"
#         response = requests.get(f"{osAPI}")
#         dto = response.json()
#         retailPrice = dto['Items'][0]['retailPrice']
#         VMdf['osPricing'].iloc[i] = retailPrice*730
######################################################################################################################################################
# Get Windows SQL Pricing
######################################################################################################################################################
# print("Get Windows SQL Pricing\n ...................................'")
# apiString = "https://prices.azure.com/api/retail/prices?$filter="
# VMdf['sqlPricing'] = np.nan
# for i in range(len(input)):
#     if pd.notna(VMdf['Windows SQL License'].iloc[i]): 
#         meterID = VMdf['Windows SQL License'].iloc[i]
#         type = 'Consumption'
#         sqlAPI = f"{apiString} meterId eq '{meterID}' and priceType eq '{type}'"
#         response = requests.get(f"{sqlAPI}")
#         dto = response.json()
#         retailPrice = dto['Items'][0]['retailPrice']
#         VMdf['sqlPricing'].iloc[i] = retailPrice*730
######################################################################################################################################################
# Get Disks Pricing
######################################################################################################################################################
# print("Get Disks Pricing\n ...................................'")
# apiString = "https://prices.azure.com/api/retail/prices?$filter="
# disksDF['Pricing'] = np.nan
# for i in range(len(disksDF)):
#   meterID = disksDF['ID'].iloc[i]
#   type = 'Consumption'
#   diskAPI = f"{apiString} meterId eq '{meterID}' and priceType eq '{type}'"
#   response = requests.get(f"{diskAPI}")
#   dto = response.json()
#   retailPrice = dto['Items'][0]['retailPrice']
#   disksDF['Pricing'].iloc[i] = retailPrice

######################################################################################################################################################
# Exporting IDs to excel
######################################################################################################################################################
print('Exporting data\n ...................................')
with pd.ExcelWriter('AzureProducts.xlsx') as writer:
  VMdf.to_excel(writer, sheet_name='VMs')
  disksDF.to_excel(writer, sheet_name='Disks')