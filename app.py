import numpy as np
import pandas as pd
import streamlit as st
from compile  import format_data, all_tbo, sub_tbo, sav_json, ts_to_date, dict_to_unix
import os
from datetime import datetime
import math


st.subheader("Upload JSON inventory file to get monthly TBO")

json_file = st.file_uploader("Upload audio file", type=['json'])

def save_import(file):
    if file.size > 4000000000000:
        return 1
    # if not os.path.exists("audio"):
    #     os.makedirs("audio")
    folder = "import"
    datetoday = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    # clear the folder to avoid storage overload
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

    try:
        with open("log0.txt", "a") as f:
            f.write(f"{file.name} - {file.size} - {datetoday};\n")
    except:
        pass

    with open(os.path.join(folder, file.name), "wb") as f:
        f.write(file.getbuffer())
    return 0

if json_file is not None:


    file_load_location = "import/inventory_tsdb.json"
    file_sav_location = "import/PLTBO.json"

    PLANTS = ['DLCW', 'RWCW', 'MKCW', 'APCW', 'AC', 'RDCW', 'GCW', 'SDCW', 'VC',
        'NJFD', 'BGCW', 'BKCW', 'HCW', 'KCW', 'MHCW', 'SCW', 'DHCW',
        'NDCW', 'ACW', 'BJCW', 'RC', 'BLCW']
    TAR_INV_DAYS = 45
    months_for_calc = ["Dec22", "Jan23", "Feb23", "Mar23", "Apr23", "May23", "Jun23", "Jul23", "Aug23", "Sep23", "Oct23", "Nov23"]
    months_for_tbo = months_for_calc[:-3]


    path = os.path.join("import", json_file.name)
    if_save_json = save_import(json_file)

    dfi = pd.read_json(file_load_location)
    
    gg = sav_json(sub_tbo(all_tbo(format_data(dfi))), file_sav_location)

    gg = gg.to_json(orient="records")

    st.download_button(label='Download TBO JSON', file_name="plttbo.json",data=gg, mime='text/json')

