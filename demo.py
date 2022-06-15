# -*- coding: utf-8 -*-
"""
Created on Thu Jun  2 15:59:55 2022

@author: jelisaveta.m
"""
import pandas as pd
import os
import glob
import numpy as np

"""
notes: 
    1. separator is ;
    2. check with various inputs
"""
os.chdir("C:/Users/jelisaveta.m/Desktop/Demo")

extension = 'csv'
allFilenames = [i for i in glob.glob('*.{}'.format(extension))]

shoppingRawData = pd.concat([pd.read_csv(f, sep=',', keep_default_na=False) for f in allFilenames])
surveyFinalData = pd.read_excel('C:\\Users\\jelisaveta.m\\Desktop\\Demo\\220437.xlsx')
shoppingRawData = shoppingRawData[shoppingRawData['USER ID'] != '']

shoppingRawData['CONSIDERATIONS'] = np.where(shoppingRawData['CONSIDERATIONS'] == 'NULL', 0, shoppingRawData['CONSIDERATIONS'])
shoppingRawData['QUANTITY'] = np.where(shoppingRawData['QUANTITY'] == 'NULL', 0, shoppingRawData['QUANTITY'])

shoppingRawData = shoppingRawData.astype({'CONSIDERATIONS':'int', 'QUANTITY':'int'})



shoppingRawData['CONSIDERATIONS_BINARY'] = shoppingRawData['CONSIDERATIONS'].apply (lambda x: 1 if x > 0 else 0)
shoppingRawData['PENETRATION_BINARY'] = shoppingRawData['QUANTITY'].apply (lambda x: 1 if x > 0 else 0)

shoppingRawData.replace(to_replace = '', value = 'NOT DEFINED', inplace = True)
shoppingRawData.replace(to_replace = 'NULL', value = 'NO SHOPPING', inplace = True)

#trenutno, dok se ne vidi sta je bug sa money spent na VS platformi
shoppingRawData = shoppingRawData[ (shoppingRawData['PENETRATION_BINARY'] == 1) & (shoppingRawData['MONEY SPENT'] != 'NO SHOPPING') ]
shoppingRawData = shoppingRawData.astype({'MONEY SPENT':'float', 'PRICE':'float'})


shoppingMergedData = pd.merge(shoppingRawData, surveyFinalData, how='right', left_on='USER ID', right_on='uuid')
"""
Calculate CONSIDERATION
"""
#DEFINISI SVE BAZE


#definisi sve splitove
mandatoryFields = ['uuid']

splits = ['CELL', 'AGE_CATEGORY', 'GENDER']

mandatoryFields.extend(splits)
surveyFinalDataSplits = surveyFinalData[mandatoryFields]

shoppingMergedData = pd.merge(shoppingRawData, surveyFinalData, how='right', left_on='USER ID', right_on='uuid')







fullBase = shoppingMergedData['USER ID'].nunique()

splitScheme = {'1': ['CELL'], '2': ['AGE_CATEGORY'], '3': ['GENDER'],'1.2': ['CELL','AGE_CATEGORY'], '1.3': ['CELL','GENDER'], '2.1': ['AGE_CATEGORY', 'CELL'], '3.1': ['GENDER', 'CELL'],\
               '1.2.3': ['CELL','AGE_CATEGORY','GENDER'], '1.3.2': ['CELL','GENDER','AGE_CATEGORY']}
 





levels = ['BRAND']
sublevels = ['CARIBOU','CINNABON','ILLY','KROGER']
lis = {}
dfAll = pd.DataFrame()

for level in levels:
    for sublevel in sublevels:
        dfAll = pd.DataFrame()
        for split in splits:
            #print ([level,sublevel,split])
            df = shoppingMergedData[shoppingMergedData.CONSIDERATIONS_BINARY == 1].pivot_table('USER ID', index=level, columns=split, aggfunc='nunique', margins=True, margins_name='Total').reset_index()
            df = df[df[level] == sublevel] 
            lis[split] = df
            if dfAll.empty:
                dfAll = df
            else:
                #pd.merge(dfAll, df, how='left', on=level)
                dfAll = pd.concat([lis['CELL'],lis['GENDER'],lis['AGE_CATEGORY']])
                df = pd.DataFrame()
            

fullBase = shoppingMergedData['USER ID'].nunique()
considerers = shoppingMergedData[shoppingMergedData.CONSIDERATIONS_BINARY == 1]['USER ID'].nunique()
shoppers = shoppingMergedData[shoppingMergedData.PENETRATION_BINARY == 1]['USER ID'].nunique()

sampleSizeses = 0
def calculateKPI (measure, level, split):
	definition = {
	'Consideration on total sample': 
		{'filters' : "CONSIDERATIONS_BINARY",
		'data' : "USER ID",
		'aggfunction' : "nunique",
		'base' : "fullBase"}
	,
	'Penetration on total sample': 
		{'filters' : "PENETRATION_BINARY",
		'data' : "USER ID",
		'aggfunction' : "nunique",
		'base' : "fullBase"}
	,
	'Consideration on considerers': 
		{'filters' : "CONSIDERATIONS_BINARY",
		'data' : "USER ID",
		'aggfunction' : "nunique",
		'base' : "shoppers"}
	,
	'Penetration on shoppers': 
		{'filters' : "PENETRATION_BINARY",
		'data' : "USER ID",
		'aggfunction' : "nunique",
		'base' : "fullBase"}
	,
	'Unit Buy Rate (Units per Buyer)': 
		{'filters' : "PENETRATION_BINARY",
		'data' : "QUANTITY",
		'aggfunction' : "mean",
		'base' : 1}
	,
	'Value Buy Rate (Units per Buyer)': 
		{'filters' : "PENETRATION_BINARY",
		'data' : "MONEY SPENT",
		'aggfunction' : "mean",
		'base' : 1}
	,
	'Total Units': 
		{'filters' : "PENETRATION_BINARY",
		'data' : "QUANTITY",
		'aggfunction' : "sum",
		'base' : 1}
	,
	'Total Value': 
		{'filters' : "PENETRATION_BINARY",
		'data' : "MONEY SPENT",
		'aggfunction' : "sum",
		'base' : 1}
	,
	'Share of Total Units': 
		{'filters' : "PENETRATION_BINARY",
		'data' : "QUANTITY",
		'aggfunction' : "sum",
		'base' : 1}
	,
	'Share of Total Value': 
		{'filters' : "PENETRATION_BINARY",
		'data' : "MONEY SPENT",
		'aggfunction' : "sum",
		'base' : 1}
	}
    
	
	if measure == "Total Units" or measure == "Total Value" or measure == "Unit Buy Rate (Units per Buyer)" or measure == "Value Buy Rate (Units per Buyer)":
		kpi = shoppingMergedData[shoppingMergedData[definition[measure]['filters']] == 1].pivot_table(definition[measure]['data'], index=level, columns=split, aggfunc=definition[measure]['aggfunction'],  margins=True, margins_name='Total')
	elif measure == "Share of Total Units" or measure == "Share of Total Value":
		kpiTemp = shoppingMergedData[shoppingMergedData[definition[measure]['filters']] == 1].pivot_table(definition[measure]['data'], index=level, columns=split, aggfunc=definition[measure]['aggfunction'],  margins=False, margins_name='Total')
		kpi = ((kpiTemp/kpiTemp.sum())*100).fillna(0).round(0).astype(int).astype(str) + '%'
	else:
		kpi = shoppingMergedData.pivot_table(definition[measure]['data'], index=level, columns=split, aggfunc=definition[measure]['aggfunction'],  margins=True, margins_name='Total')
		sampleSizes = surveyFinalData[split].value_counts()
		sampleSizes['Total'] = sampleSizes.sum()
		if measure != "Unit Buy Rate (Units per Buyer)" and measure != "Value Buy Rate (UnitsValue per Buyer)":
			kpi = ((kpi.div(sampleSizes))*100).fillna(0).round(0).astype(int).astype(str) + '%'
		N = pd.DataFrame(data = [sampleSizes], index = ['Sample size'], columns=kpi.columns)
		kpi = pd.concat([N, kpi])
	
	return kpi
	


test = calculateKPI('Consideration on total sample','BRAND',['GENDER', 'AGE_CATEGORY'])


import requests, json
from urllib.request import urlopen
def get_datamap(datamap_json_file):
    datamap = {}
    questions_label_text = []
    #datamap_json = json.load(datamap_json_file)
    url = requests.get("https://jsonplaceholder.typicode.com/users")
    text = url.text
    datamap_json = json.loads(text)
    #response = urlopen("https://github.com/jelisavetaM/VS_module/blob/main/datamap.json")
    #datamap_json = json.loads(response.read())
    for var in datamap_json["variables"]:
        q_title = var["label"]
        answers = {}
        if "value" in var:
            answers[0] = "NO TO: " + var["rowTitle"]
            answers[var["value"]] = var["rowTitle"]
        elif "values" in var:
            for val in var["values"]:
                answers[val["value"]] = val["title"]

        q_json = {
            "text" : var["title"],
            "type" : var["type"],
            "vgroup" : var["vgroup"],
            "answers" : answers
        
        }
        datamap[q_title] = q_json
        questions_label_text.append(q_title + "->" + var["title"])

    return [datamap,questions_label_text]   

get_datamap(5)
