"""Convert json inventory data to json monthly TBO data"""

import pandas as pd
import numpy as np
from datetime import datetime
import math

file_load_location = "inventory_tsdb.json"
file_sav_location = "PLTBO.json"

PLANTS = ['DLCW', 'RWCW', 'MKCW', 'APCW', 'AC', 'RDCW', 'GCW', 'SDCW', 'VC',
       'NJFD', 'BGCW', 'BKCW', 'HCW', 'KCW', 'MHCW', 'SCW', 'DHCW',
       'NDCW', 'ACW', 'BJCW', 'RC', 'BLCW']
TAR_INV_DAYS = 45
months_for_calc = ["Dec22", "Jan23", "Feb23", "Mar23", "Apr23", "May23", "Jun23", "Jul23", "Aug23", "Sep23", "Oct23", "Nov23"]
months_for_tbo = months_for_calc[:-3]

def ts_to_date(ts):
    """Convert UNIX timestamp to date"""
    dt = datetime.fromtimestamp(ts/1000).strftime('%d-%b-%y').split('-')
    return dt[1] + dt[2]

def dict_to_unix(ds):
    """Convert dict to unix"""
    ts = int(ds.get('$numberLong'))
    return ts

def format_data(df_inv):
    """Format the dataframe based on requirements"""
    df_inv.I_Date = df_inv.I_Date.apply(dict_to_unix)
    df_inv.I_Date = df_inv.I_Date.apply(ts_to_date)
    df_inv['I_OpeningInventoryDate'] = (df_inv.I_OpeningInventoryDate*1000).apply(ts_to_date)
    df_inv = df_inv[['C_PlantID', 'I_ClosingStockPlant',
           'I_ConsumptionQuantity', 'I_Date', 'I_Fuel_Type', 'I_Number',
           'I_OpeningInventoryDate', 'I_OpeningStockPlant', 'I_PlantDays',
             'I_ReceiptQuantity']]
    df_inv = df_inv[df_inv.I_Number == "Integrated"]
    df_inv = df_inv[df_inv.I_Fuel_Type == "Total"]
    df_inv = df_inv[df_inv.I_Date.isin(months_for_calc)]
    df_inv = df_inv[df_inv.C_PlantID.isin(PLANTS)]
    
    df_inv = df_inv.reset_index(drop=True)
    return df_inv

def all_tbo(df_inv):
    """Return tbo for all the months"""
    df0 = pd.DataFrame()
    df0["C_PlantID"] = PLANTS

    for i in range(len(months_for_tbo)):
        mnum = i
        MONTH = months_for_calc[mnum]
        prev_mon = months_for_calc[mnum-1] if mnum != 0 else None
        next_mon = months_for_calc[mnum+1] if mnum < 8 else None
        months_to_calc = []
        next_months_to_calc = []
        for n, i in enumerate(months_for_calc):
            if i == MONTH:
                for j in range(1, 4):
                    months_to_calc.append(months_for_calc[n + j])
                    if next_mon is None:
                        next_months_to_calc = None
                    else:
                        next_months_to_calc.append(months_for_calc[n + j + 1])    

        hm = df_inv[df_inv.I_Date == MONTH].reset_index(drop=True)

        plant_list = hm.C_PlantID.unique()
        toa = []
        for i in plant_list:
            pl = i
            gh = df_inv[df_inv.C_PlantID == pl]
            gh = gh[gh.I_Date.isin(months_to_calc)]
            avg = gh.I_ConsumptionQuantity.mean()/30
            toa.append([pl, avg])
        toa = pd.DataFrame(toa, columns=["C_PlantID", "AvgConsumptionJanFebMar23"])
        hm = pd.merge(hm, toa)

        pld = hm.I_PlantDays.values.tolist()
        plda = []
        for i in pld:
            if i < 0:
                i = 0
            plda.append(TAR_INV_DAYS - i)
        hm["DiffDays"] = plda

        dec_list = hm.values.tolist()
        tbol = []
        for i in dec_list:
            days = i[-1]
            avg = i[-2]
            if days < 0:
                days = 0
            tbo = days*avg
            tbo = math.ceil(tbo)
            tbol.append((tbo))
        hm[f"{MONTH}_TBO"] = tbol

        df0 = pd.merge(df0, hm[["C_PlantID", f"{MONTH}_TBO"]])
    return df0

def sub_tbo(df):
    """Get TBO by subtracting value from previous months"""
    ls = list(df.columns)
    del ls[0]
    for i in range(len(ls)-1):
        for j in range(i+1):
            df[f"{ls[i+1]}"] = df[f"{ls[i+1]}"] - df[f"{ls[i-j]}"]
            df[f"{ls[i+1]}"] = df[f"{ls[i+1]}"].mask(df[f"{ls[i+1]}"].lt(0),0)
    return df

def sav_json(df, file_sav_location):
    """sav dataframe as json"""
    df.to_json(fr'{file_sav_location}')
    return df

def main():
    """Main function"""
    dfi = pd.read_json(file_load_location)
    
    gg = sav_json(sub_tbo(all_tbo(format_data(dfi))), file_sav_location)

# main()
